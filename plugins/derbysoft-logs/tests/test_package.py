import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_references_and_stdio_launchers():
    plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert (ROOT / plugin["skills"]).is_dir()
    assert (ROOT / plugin["extensions"]["com.openai"]["onboardingSkill"]).is_file()
    config = json.loads((ROOT / plugin["mcpServers"]).read_text(encoding="utf-8"))
    assert set(config["mcpServers"]) == {"opensearch", "streamlog", "loki", "settings", "semantics"}
    assert config["mcpServers"]["semantics"]["env_vars"] == ["DERBYSOFT_LOGS_HOME"]
    for server in config["mcpServers"].values():
        assert server["command"] == "uv"
        assert server["cwd"] == "."
        assert "--frozen" in server["args"] and "-I" in server["args"]
        assert "env" not in server  # no packaged secrets/default credentials


def test_share_allowlist_excludes_local_environment_and_profiles(tmp_path):
    spec = importlib.util.spec_from_file_location("build_share", ROOT / "scripts/build_share.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    included_names = ["README.md", "src/main.py", "package-files.json"]
    (tmp_path / "README.md").write_text("fixture")
    (tmp_path / "package-files.json").write_text(json.dumps(included_names), encoding="utf-8")
    for excluded in (".env", "credentials.json", "profiles.json", "local.log"):
        (tmp_path / excluded).write_text("secret-fixture")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv/secret.json").write_text("secret-fixture")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.py").write_text("pass\n")
    (tmp_path / "src/credentials.json").write_text("secret-fixture")
    (tmp_path / "src/live-business-records.json").write_text("private-fixture")
    included = {str(path.relative_to(tmp_path)).replace("\\", "/") for path in module.package_files(tmp_path)}
    assert included == set(included_names)
