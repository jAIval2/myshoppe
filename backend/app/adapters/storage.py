"""Supabase Storage adapter using its HTTP/TUS APIs and the existing HTTPX dependency."""

import base64
from functools import lru_cache
from pathlib import PurePosixPath
from urllib.parse import quote, urljoin, urlsplit, unquote

import httpx

from app.settings import settings


class ObjectStorage:
    chunk_size = 6 * 1024 * 1024

    def __init__(self):
        project = settings.supabase_url.rstrip("/")
        parsed = urlsplit(project)
        if not parsed.scheme or not parsed.hostname:
            raise RuntimeError("SUPABASE_URL must be an absolute URL for object storage")
        self.project_url = project
        if parsed.hostname.endswith(".supabase.co"):
            host = parsed.hostname.removesuffix(".supabase.co") + ".storage.supabase.co"
            self.upload_url = f"{parsed.scheme}://{host}"
        else:
            self.upload_url = project
        self.bucket = settings.media_bucket
        self.client = httpx.Client(timeout=httpx.Timeout(120, connect=10))

    def _headers(self):
        key = settings.supabase_storage_key
        if not key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for media storage")
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def _object_path(self, key):
        path = PurePosixPath(key)
        if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
            raise ValueError("Invalid media object key")
        return "/".join(quote(part, safe="-_.~") for part in path.parts)

    def public_url(self, key):
        return f"{self.project_url}/storage/v1/object/public/{quote(self.bucket, safe='-_.~')}/{self._object_path(key)}"

    def key_from_public_url(self, value):
        actual, configured = urlsplit(value), urlsplit(self.project_url)
        prefix = f"/storage/v1/object/public/{self.bucket}/"
        if (
            actual.scheme != configured.scheme
            or actual.netloc != configured.netloc
            or not actual.path.startswith(prefix)
            or actual.query
            or actual.fragment
        ):
            return None
        key = unquote(actual.path[len(prefix) :])
        try:
            self._object_path(key)
        except ValueError:
            return None
        return key

    def put(self, key, source, size, content_type):
        """Create an immutable object with bounded TUS chunks, including videos over 6 MB."""
        metadata = {
            "bucketName": self.bucket,
            "objectName": key,
            "contentType": content_type,
            "cacheControl": "31536000",
        }
        encoded = ",".join(
            f"{name} {base64.b64encode(value.encode()).decode()}" for name, value in metadata.items()
        )
        headers = {
            **self._headers(),
            "Tus-Resumable": "1.0.0",
            "Upload-Length": str(size),
            "Upload-Metadata": encoded,
            # Job outputs use a fresh random key per operation, so replacing
            # that same key after a reclaimed worker is a safe retry.
            "x-upsert": "true",
        }
        response = self.client.post(
            f"{self.upload_url}/storage/v1/upload/resumable", headers=headers
        )
        response.raise_for_status()
        location = urljoin(self.upload_url + "/", response.headers["Location"])
        if (
            urlsplit(location).scheme != urlsplit(self.upload_url).scheme
            or urlsplit(location).netloc != urlsplit(self.upload_url).netloc
        ):
            raise RuntimeError("Storage returned an unexpected resumable upload host")

        offset = 0
        while offset < size:
            chunk = source.read(min(self.chunk_size, size - offset))
            if not chunk:
                raise ValueError("Media source ended before its declared size")
            response = self.client.patch(
                location,
                headers={
                    **self._headers(),
                    "Tus-Resumable": "1.0.0",
                    "Upload-Offset": str(offset),
                    "Content-Type": "application/offset+octet-stream",
                },
                content=chunk,
            )
            response.raise_for_status()
            offset = int(response.headers.get("Upload-Offset", offset + len(chunk)))
        if offset != size:
            raise RuntimeError("Storage upload completed at an unexpected size")
        return self.public_url(key)

    def download(self, key, destination):
        url = f"{self.project_url}/storage/v1/object/{quote(self.bucket, safe='-_.~')}/{self._object_path(key)}"
        with self.client.stream("GET", url, headers=self._headers()) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes(self.chunk_size):
                destination.write(chunk)

    def exists(self, key):
        response = self.client.head(
            self.public_url(key), timeout=httpx.Timeout(5, connect=2)
        )
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def delete(self, key):
        url = f"{self.project_url}/storage/v1/object/{quote(self.bucket, safe='-_.~')}"
        response = self.client.request("DELETE", url, headers=self._headers(), json={"prefixes": [key]})
        response.raise_for_status()


def approved_media_src(src):
    if not isinstance(src, str) or not src:
        return False
    if src.startswith(("/media/", "/uploads/")):
        return ".." not in src.split("/") and "\\" not in src
    configured = urlsplit(settings.supabase_url.rstrip("/"))
    actual = urlsplit(src)
    prefix = f"/storage/v1/object/public/{settings.media_bucket}/"
    if (
        not configured.scheme
        or actual.scheme != configured.scheme
        or actual.netloc != configured.netloc
        or not actual.path.startswith(prefix)
        or actual.query
        or actual.fragment
    ):
        return False
    key = unquote(actual.path[len(prefix) :])
    path = PurePosixPath(key)
    return bool(path.parts) and not path.is_absolute() and all(part not in ("", ".", "..") for part in path.parts)


@lru_cache(maxsize=1)
def storage():
    return ObjectStorage()
