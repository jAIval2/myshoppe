"""Run the API, outbox worker and Next.js together. Ctrl-C stops this process group."""

import argparse
import os
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def environment():
    env = os.environ.copy()
    source = ROOT / ".env"
    if source.exists():
        for line in source.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env.setdefault(key.strip(), value.strip().strip("\"'"))
    env.setdefault("DEV_LOGIN_ENABLED", "true")
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--production-build",
        action="store_true",
        help="Serve an existing next build; does not enable live payments",
    )
    args = parser.parse_args()
    env = environment()
    commands = [
        (
            [
                str(ROOT / ".venv/bin/uvicorn"),
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            ROOT / "backend",
        ),
        ([str(ROOT / ".venv/bin/python"), "-m", "app.worker"], ROOT / "backend"),
        (["npm", "run", "start" if args.production_build else "dev"], ROOT / "web"),
    ]
    processes = []

    def stop(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        for command, cwd in commands:
            processes.append(
                subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True)
            )
        print(
            "MyShoppe: http://localhost:3000 | Admin: /admin | Ctrl-C to stop",
            flush=True,
        )
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
        if any(p.returncode for p in processes if p.poll() is not None):
            raise SystemExit("A service failed. See its log above.")
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
        for p in processes:
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)


if __name__ == "__main__":
    main()
