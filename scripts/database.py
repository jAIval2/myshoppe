"""Create/start the isolated local PostgreSQL cluster; never touches system clusters."""

import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = root / ".local/postgres"
data.parent.mkdir(exist_ok=True)


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


if not (data / "PG_VERSION").exists():
    run(
        "initdb",
        "-D",
        str(data),
        "-U",
        "myshoppe",
        "--auth-local=trust",
        "--auth-host=trust",
        "--encoding=UTF8",
    )
if subprocess.run(
    ["pg_ctl", "-D", str(data), "status"], stdout=subprocess.DEVNULL, check=False
).returncode:
    run(
        "pg_ctl",
        "-D",
        str(data),
        "-l",
        str(root / ".local/postgres.log"),
        "-o",
        "-p 55432 -h 127.0.0.1 -k /tmp",
        "start",
    )
for name in ("myshoppe", "myshoppe_test"):
    result = run(
        "psql",
        "-h",
        "127.0.0.1",
        "-p",
        "55432",
        "-U",
        "myshoppe",
        "-d",
        "postgres",
        "-Atc",
        f"SELECT 1 FROM pg_database WHERE datname='{name}'",
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() != "1":
        run("createdb", "-h", "127.0.0.1", "-p", "55432", "-U", "myshoppe", name)
print(
    "Development PostgreSQL ready on 127.0.0.1:55432; production must use authenticated access."
)
