"""Evidence-backed Markdown semantics: matching, history and safe writes."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path

import pytest

from derbysoft_logs import config, semantics


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    return tmp_path


CODE = [{"kind": "code", "locator": "src/Dispatch.java:42@abc123", "summary": "The dispatch method emits this process."}]
LOG = [{"kind": "log", "locator": "uat/index/record-id", "summary": "Observed one dispatch attempt."}]
SCOPE = {"project": "rate-parity", "service": "manager", "log_type": "perflog"}
SELECTORS = {"process": "LiveCheckDispatch", "ext.messageType": "ATTEMPTED"}


def save(*, scope=None, selectors=None, title="Dispatch attempt", body="# Meaning\n\nThis process records an attempt.",
         status="verified", evidence=None, reason="Record code evidence", revision=0):
    return semantics.save(scope or SCOPE, selectors or SELECTORS, title, body, status,
                          CODE if evidence is None else evidence, reason, revision)


def search(**kwargs):
    return semantics.search(project="rate-parity", service="manager", log_type="perflog",
                            selectors=kwargs.pop("selectors", SELECTORS), **kwargs)


def test_markdown_survives_server_restart_and_does_not_depend_on_default_environment(isolated, monkeypatch):
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "not-an-environment")
    result = save(body="# 业务含义\n\nATTEMPTED 表示尝试派发。\n")
    path = Path(result["path"])
    assert path.is_relative_to(isolated / "knowledge" / "business-semantics")
    assert path.name == "000001.md" and path.is_file()
    source = path.read_text(encoding="utf-8")
    assert source.startswith("---\n{") and "# 业务含义" in source
    metadata = json.loads(source[4:].split("\n---\n", 1)[0])
    assert metadata["scope"]["environment"] is None
    loaded = semantics.get(result["entry_id"])
    assert loaded["body"].endswith("派发。\n") and loaded["revision"] == 1
    assert "untrusted data" in loaded["note"]
    assert search()["results"][0]["match"] == "applicable"


def test_empty_library_reports_location_without_creating_sample_or_other_knowledge(isolated):
    result = semantics.search()
    assert result["results"] == [] and result["knowledge_root"] == str(isolated / "knowledge" / "business-semantics")
    assert result["status"] == "ok" and result["next_offset"] is None
    assert not (isolated / "knowledge").exists()


def test_same_process_is_isolated_by_project_service_and_complete_selector_context(isolated):
    first = save()
    second = save(scope={**SCOPE, "service": "notifier"}, body="# Meaning\n\nA different stage.")
    third = save(selectors={"process": "LiveCheckDispatch", "ext.messageType": "ACCEPTED"},
                 body="# Meaning\n\nAcceptance, not an attempt.")
    other_project = save(scope={**SCOPE, "project": "different-product"})
    matching = search()["results"]
    assert [item["entry_id"] for item in matching] == [first["entry_id"]]
    assert {item["entry_id"] for item in semantics.search(project="rate-parity", selectors={"process": "LiveCheckDispatch"})["results"]} == {
        first["entry_id"], second["entry_id"], third["entry_id"]}
    incomplete = search(selectors={"process": "LiveCheckDispatch"})["results"]
    assert {item["entry_id"] for item in incomplete} == {first["entry_id"], third["entry_id"]}
    assert all(item["match"] == "candidate" and "selectors.ext.messageType" in item["missing_context"] for item in incomplete)
    assert other_project["entry_id"] not in {item["entry_id"] for item in incomplete}
    assert semantics.search(query="attempt", project="rate-parity")["results"]
    assert all(item["match"] == "candidate" for item in semantics.search(query="attempt", project="rate-parity")["results"])


@pytest.mark.parametrize("value", [1, "1", True])
def test_selector_values_preserve_type_and_are_never_interchangeable(isolated, value):
    for target in (1, "1", True):
        save(selectors={"process": "Dispatch", "processType": target}, title=f"type {type(target).__name__}")
    result = search(selectors={"process": "Dispatch", "processType": value})["results"]
    assert len(result) == 1
    assert type(result[0]["selectors"]["processType"]) is type(value)
    assert result[0]["selectors"]["processType"] == value
    assert result[0]["match"] == "applicable"


@pytest.mark.parametrize("invalid", [1.5, None, [], {}, 2**63])
def test_selector_values_reject_unsupported_types(isolated, invalid):
    with pytest.raises(config.ConfigurationError):
        save(selectors={"process": "Dispatch", "processType": invalid})
    assert not (isolated / "knowledge").exists()


def test_candidate_status_and_scoped_versions_require_evidence_and_context(isolated):
    with pytest.raises(config.ConfigurationError, match="logs alone"):
        save(evidence=LOG, status="verified")
    candidate = save(scope={**SCOPE, "environment": "uat", "source_version": "abc123"},
                     evidence=LOG, status="candidate")
    all_context = search(environment="uat", source_version="abc123")["results"][0]
    assert all_context["entry_id"] == candidate["entry_id"] and all_context["match"] == "candidate"
    assert all_context["missing_context"] == []
    missing = search()["results"][0]
    assert set(missing["missing_context"]) == {"environment", "source_version"}
    assert search(environment="prod")["results"] == []
    assert search(environment="uat", source_version="different")["results"] == []
    verified = save(scope={**SCOPE, "environment": "uat", "source_version": "abc123"},
                    revision=1, reason="Code independently confirmed", status="verified")
    assert verified["revision"] == 2
    assert search(environment="uat", source_version="abc123")["results"][0]["match"] == "applicable"
    assert search(environment="uat")["results"][0]["match"] == "candidate"


def test_optimistic_revisions_preserve_history_and_allow_explicit_restore(isolated):
    first = save()
    assert save(revision=1)["changed"] is False
    second = save(body="# Meaning\n\nRevised wording.", reason="Add evidence", revision=1)
    assert second["entry_id"] == first["entry_id"] and second["revision"] == 2
    with pytest.raises(config.ConfigurationError, match="revision conflict"):
        save(body="stale", revision=1)
    deprecated = save(body=second["body"], status="deprecated", reason="Code no longer emits this", revision=2)
    assert deprecated["revision"] == 3
    assert search()["results"] == []
    assert search(include_deprecated=True)["results"][0]["match"] == "candidate"
    assert semantics.get(first["entry_id"], 1)["body"] == first["body"]
    history = semantics.history(first["entry_id"], offset=0, limit=2)
    assert [item["revision"] for item in history["revisions"]] == [3, 2]
    assert history["next_offset"] == 2 and history["total"] == 3
    assert [item["revision"] for item in semantics.history(first["entry_id"], offset=2, limit=2)["revisions"]] == [1]
    restored = save(body=first["body"], status="verified", reason="Restore prior interpretation", revision=3)
    assert restored["revision"] == 4 and Path(first["path"]).is_file()


def test_changed_scope_must_create_distinct_entry_not_mutate_existing_identity(isolated):
    original = save()
    with pytest.raises(config.ConfigurationError, match="revision conflict"):
        save(scope={**SCOPE, "service": "other"}, revision=1)
    different = save(scope={**SCOPE, "service": "other"}, revision=0)
    assert original["entry_id"] != different["entry_id"]
    assert semantics.get(original["entry_id"])["scope"]["service"] == "manager"


def test_two_concurrent_edits_cannot_overwrite_each_other(isolated):
    first = save()
    def edit(n):
        try:
            return save(body=f"# Meaning\n\nIndependent update {n}.", reason=f"Update {n}", revision=1)
        except config.ConfigurationError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, (1, 2)))
    assert sum(isinstance(item, dict) for item in results) == 1
    assert sum(isinstance(item, str) and "revision conflict" in item for item in results) == 1
    assert len(semantics.history(first["entry_id"])["revisions"]) == 2


def test_corrupt_latest_never_falls_back_to_earlier_verified_semantics(isolated):
    first = save()
    second = save(body="# New revision", reason="Update", revision=1)
    Path(second["path"]).write_text("not valid frontmatter", encoding="utf-8")
    response = search()
    assert response["results"] == [] and response["invalid_entries"] == 1 and response["status"] == "partial"
    with pytest.raises(config.ConfigurationError, match="no older revision"):
        semantics.get(first["entry_id"])
    assert semantics.get(first["entry_id"], revision=1)["body"] == first["body"]
    with pytest.raises(config.ConfigurationError, match="no older revision"):
        save(body="overwrite corrupt", revision=2)


def test_pagination_and_sensitive_values_rejected_without_echo(isolated):
    for number in range(3):
        save(selectors={"process": "Dispatch", "processType": number}, title=f"Dispatch {number}")
    first = semantics.search(project="rate-parity", service="manager", log_type="perflog", offset=0, limit=2)
    second = semantics.search(project="rate-parity", service="manager", log_type="perflog", offset=2, limit=2)
    assert first["total"] == 3 and first["next_offset"] == 2
    assert len(second["results"]) == 1 and second["next_offset"] is None
    assert {x["entry_id"] for x in first["results"]}.isdisjoint({x["entry_id"] for x in second["results"]})
    for secret in ("password=unsafe-test-value", "Authorization: Bearer unsafe-test-value", "https://user:unsafe-test-value@example.test/a"):
        with pytest.raises(config.ConfigurationError) as failure:
            save(selectors={"process": "Sensitive"}, body=secret)
        assert "unsafe-test-value" not in str(failure.value)
    with pytest.raises(config.ConfigurationError):
        save(selectors={"process": "Sensitive", "access_token": "abc"})


def test_invalid_identifier_traversal_and_atomic_failure_do_not_damage_existing_revision(isolated, monkeypatch):
    first = save()
    before = Path(first["path"]).read_bytes()
    with pytest.raises(config.ConfigurationError):
        semantics.get("../other")
    def fail_replace(*args):
        raise OSError("fixture failure")
    monkeypatch.setattr(semantics.os, "replace", fail_replace)
    with pytest.raises(config.ConfigurationError, match="Cannot save"):
        save(body="A valid update", reason="Update", revision=1)
    assert Path(first["path"]).read_bytes() == before
    assert semantics.get(first["entry_id"])["revision"] == 1
    assert not list(Path(first["path"]).parent.glob("*.tmp"))


def test_revision_symlinks_never_escape_local_library(isolated, tmp_path):
    first = save()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    malicious = Path(first["path"]).parent / "000002.md"
    try:
        os.symlink(outside, malicious)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")
    result = search()
    assert result["results"] == [] and result["invalid_entries"] == 1
    with pytest.raises(config.ConfigurationError):
        semantics.get(first["entry_id"])
    assert outside.read_text(encoding="utf-8") == "outside"


def test_symlink_revision_rejected_even_on_hosts_without_symlink_privilege(isolated, monkeypatch):
    first = save()
    suspicious = Path(first["path"]).parent / "000002.md"
    suspicious.write_text("not an authorized revision", encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == suspicious or original(path))
    result = search()
    assert result["results"] == [] and result["invalid_entries"] == 1
    with pytest.raises(config.ConfigurationError):
        semantics.get(first["entry_id"])


def test_overview_shows_full_current_semantics_evidence_and_revision_link(isolated):
    full_body = "# Interpretation\n\n" + "business stage detail " * 12 + "the final qualifying condition"
    first = save(body=full_body)
    overview = Path(first["index_path"])
    rendered = overview.read_text(encoding="utf-8")
    assert first["saved"] is True and "index_warning" not in first
    assert "rate-parity / manager" in rendered and "ext.messageType" in rendered
    assert "Dispatch attempt" in rendered and "已验证" in rendered
    assert "the final qualifying condition" in rendered
    assert "src/Dispatch.java:42@abc123" in rendered
    assert f"{first['entry_id']}/000001.md" in rendered
    second = save(body="# Updated\n\nNew business semantics.", reason="Update", revision=1)
    rendered = overview.read_text(encoding="utf-8")
    assert "New business semantics." in rendered and "the final qualifying condition" not in rendered
    assert f"{first['entry_id']}/000002.md" in rendered and Path(first["path"]).is_file()
    save(body=second["body"], status="deprecated", reason="No longer emitted", revision=2)
    rendered = overview.read_text(encoding="utf-8")
    assert "已停用" in rendered and f"{first['entry_id']}/000003.md" in rendered
    assert semantics.search()["index_path"] == str(overview)
    assert semantics.get(first["entry_id"])["index_path"] == str(overview)


def test_overview_failure_reports_saved_revision_and_can_be_rebuilt(isolated, monkeypatch):
    original_replace = semantics.os.replace
    def fail_overview(source, destination):
        if Path(destination).name == "business-semantics.md":
            raise OSError("simulated overview failure")
        return original_replace(source, destination)
    monkeypatch.setattr(semantics.os, "replace", fail_overview)
    saved = save()
    assert saved["saved"] is True and saved["changed"] is True and saved["revision"] == 1
    assert "index_warning" in saved and Path(saved["path"]).is_file()
    assert semantics.get(saved["entry_id"])["revision"] == 1
    monkeypatch.setattr(semantics.os, "replace", original_replace)
    rebuilt = semantics.rebuild_overview()
    assert rebuilt["entries"] == 1 and rebuilt["invalid_entries"] == 0
    assert "Dispatch attempt" in Path(rebuilt["index_path"]).read_text(encoding="utf-8")
    assert semantics.history(saved["entry_id"])["total"] == 1


def test_save_confirms_success_if_rename_completed_before_reported_error(isolated, monkeypatch):
    original_replace = semantics.os.replace
    def completed_then_error(source, destination):
        original_replace(source, destination)
        if Path(destination).name == "000001.md":
            raise OSError("simulated ambiguous rename result")
    monkeypatch.setattr(semantics.os, "replace", completed_then_error)
    saved = save()
    assert saved["saved"] is True and saved["changed"] is True and saved["revision"] == 1
    assert semantics.get(saved["entry_id"])["body"] == saved["body"]
    assert "Dispatch attempt" in Path(saved["index_path"]).read_text(encoding="utf-8")
    assert semantics.history(saved["entry_id"])["total"] == 1


def test_rebuilt_overview_reports_corruption_without_reusing_old_revision(isolated):
    first = save(body="# Old meaning\n\nMust not be reused.")
    latest = save(body="# Current meaning", reason="Update", revision=1)
    Path(latest["path"]).write_text("damaged", encoding="utf-8")
    rebuilt = semantics.rebuild_overview()
    assert rebuilt["invalid_entries"] == 1 and rebuilt["entries"] == 0
    rendered = Path(rebuilt["index_path"]).read_text(encoding="utf-8")
    assert "不可读取" in rendered and "Must not be reused" not in rendered
    assert semantics.get(first["entry_id"], revision=1)["body"].startswith("# Old meaning")


def test_missing_revision_is_reported_not_silently_ignored(isolated):
    first = save()
    second = save(body="# Revision 2", reason="Update", revision=1)
    Path(first["path"]).unlink()
    assert Path(second["path"]).exists()
    assert search()["invalid_entries"] == 1
    with pytest.raises(config.ConfigurationError, match="history is incomplete"):
        semantics.get(first["entry_id"])
