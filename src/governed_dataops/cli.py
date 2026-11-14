"""Small explicit service CLI. Secrets are generated into local files, never stdout."""

import argparse
import asyncio
import json
import os
import secrets
from pathlib import Path


def initialize(directory: Path) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    secret_dir = directory / ".secrets"
    if secret_dir.exists() and any(secret_dir.iterdir()):
        raise SystemExit("Secret directory is not empty; refusing to replace existing credentials")
    if (directory / ".env").exists():
        raise SystemExit("Configuration exists; refusing to overwrite it")
    secret_dir.mkdir(mode=0o700, exist_ok=True)
    config = {
        "DATAOPS_DB_PATH": str(directory / "state" / "dataops.db"),
        "DATAOPS_DEMO_MODE": "true",
        "DATAOPS_ENVIRONMENT": "dev",
        "DATAOPS_SCOPE": "factory-a",
    }
    for role in ("reader", "executor", "operator", "approver"):
        path = secret_dir / f"{role}-token"
        path.write_text(secrets.token_urlsafe(32))
        path.chmod(0o600)
        config[f"DATAOPS_{role.upper()}_TOKEN_FILE"] = str(path)
    key = Ed25519PrivateKey.generate()
    private_path, public_path = secret_dir / "approval-private.pem", secret_dir / "approval-public.pem"
    private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    private_path.chmod(0o600)
    public_path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    config["DATAOPS_APPROVAL_SIGNING_KEY_FILE"] = str(private_path)
    config["DATAOPS_APPROVAL_VERIFY_KEY_FILE"] = str(public_path)
    # JSON-quoted dotenv values support spaces without shell evaluation.
    (directory / ".env").write_text("\n".join(f"{k}={json.dumps(v)}" for k, v in config.items()) + "\n")
    (directory / ".env").chmod(0o600)
    print(f"Created local configuration in {directory}; use --env-file to load it")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--directory", type=Path, default=Path("."))
    serve = sub.add_parser("serve")
    serve.add_argument("service", choices=["api", "target", "worker"])
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int)
    for service, port in (("api", 8080), ("target", 8081)):
        entry = sub.add_parser(service)
        entry.add_argument("--host", default="127.0.0.1")
        entry.add_argument("--port", type=int, default=port)
    sub.add_parser("worker")
    sub.add_parser("mcp")
    sub.add_parser("migrate")
    backup = sub.add_parser("backup")
    backup.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "serve":
        args.command = args.service
        args.port = args.port or {"api": 8080, "target": 8081, "worker": 0}[args.command]
    if args.env_file:
        for line in args.env_file.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            name, value = line.split("=", 1)
            if not name.startswith("DATAOPS_"):
                raise SystemExit("Only DATAOPS_ configuration is accepted")
            if name not in os.environ:
                os.environ[name] = json.loads(value)
    if args.command == "init":
        initialize(args.directory)
    elif args.command in {"api", "target"}:
        import uvicorn

        factory = "create_target_app" if args.command == "target" else "create_app"
        uvicorn.run(f"governed_dataops.{args.command}:{factory}", factory=True, host=args.host, port=args.port, log_config=None)
    elif args.command == "worker":
        from governed_dataops.settings import get_settings
        from governed_dataops.worker import run_worker

        asyncio.run(run_worker(get_settings()))
    elif args.command == "mcp":
        from governed_dataops.mcp_server import main as mcp_main

        mcp_main()
    else:
        from governed_dataops.settings import get_settings
        from governed_dataops.storage import Store

        store = Store(get_settings().db_path)
        if args.command == "backup":
            print(json.dumps(store.backup(args.output), indent=2))
        else:
            print("Database is at schema version 1")


if __name__ == "__main__":
    main()
