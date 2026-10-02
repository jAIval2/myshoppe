import json
import subprocess
from pathlib import Path


def process_video(source: str, destination: str):
    source, destination = Path(source), Path(destination)
    details = json.loads(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of",
                "json",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        ).stdout
    )
    video = next((s for s in details["streams"] if s["codec_type"] == "video"), None)
    if (
        not video
        or float(details["format"]["duration"]) > 60
        or video["width"] * video["height"] > 16_000_000
    ):
        raise ValueError("Video must be under 60 seconds and 16 megapixels")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-an",
            "-vf",
            "scale='min(1280,iw)':-2",
            "-c:v",
            "libx264",
            "-crf",
            "25",
            "-preset",
            "fast",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        capture_output=True,
        check=True,
        timeout=180,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(destination), "-frames:v", "1", str(destination.with_suffix(".jpg"))],
        capture_output=True,
        check=True,
        timeout=30,
    )
