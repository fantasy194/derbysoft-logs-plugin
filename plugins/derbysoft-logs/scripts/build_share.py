"""Build a relocatable private marketplace from an explicit file allowlist."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package_files(root: Path = ROOT) -> list[Path]:
    names = json.loads((root / "package-files.json").read_text(encoding="utf-8"))
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise ValueError("package-files.json must be an explicit list of relative file paths")
    paths = [root / name for name in names]
    for path in paths:
        if path.name.lower().startswith(("credentials", "profiles", ".env")):
            raise ValueError("Credential/profile files cannot be distributed")
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Package files must be regular files inside the plugin.")
    return sorted(set(paths))


def main() -> None:
    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    name, version = manifest["name"], manifest["version"]
    destination = ROOT / "dist" / f"{name}-{version}.zip"
    destination.parent.mkdir(exist_ok=True)
    marketplace = {
        "name": "derbysoft-logs", "interface": {"displayName": "DerbySoft Logs"},
        "plugins": [{"name": name, "source": {"source": "local", "path": f"./plugins/{name}"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"}],
    }
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(".agents/plugins/marketplace.json", json.dumps(marketplace, indent=2) + "\n")
        archive.writestr("README.md", "# DerbySoft Logs\n\n内部分享包，不含用户凭证。\n\n"
            "解压后运行：\n\n```sh\nuv sync --frozen --project plugins/derbysoft-logs\n"
            "codex plugin marketplace add .\n"
            "codex plugin add derbysoft-logs@derbysoft-logs\n```\n\n"
            "在插件详情页的 Structured Settings 中创建环境、设置地址和默认索引，通过配置凭证按钮保存认证。\n\n"
            "完整说明见 [插件 README](plugins/derbysoft-logs/README.md)。\n")
        for path in package_files():
            archive.write(path, f"plugins/{name}/{path.relative_to(ROOT).as_posix()}")
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Share archive verification failed")
    print(destination)


if __name__ == "__main__":
    main()
