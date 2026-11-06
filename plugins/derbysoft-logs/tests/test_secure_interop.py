"""Real stdio server accepts the WebCrypto browser encryption format."""
import asyncio
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

from mcp import Client, StdioServerParameters
import pytest


NODE = shutil.which("node")
FIXTURE = Path(__file__).with_name("secure_stdio_fixture.py")

JS_ENCRYPT = r"""
const { webcrypto } = require('node:crypto');
const { readFileSync } = require('node:fs');
const input = JSON.parse(readFileSync(0, 'utf8'));
(async () => {
  const { subtle, getRandomValues } = webcrypto;
  const encoder = new TextEncoder();
  const publicKey = await subtle.importKey('spki', Buffer.from(input.public_key_spki, 'base64'),
    {name: 'RSA-OAEP', hash: 'SHA-256'}, false, ['wrapKey']);
  const aes = await subtle.generateKey({name:'AES-GCM', length:256}, true, ['encrypt']);
  const iv = getRandomValues.call(webcrypto, new Uint8Array(12));
  const wrapped = await subtle.wrapKey('raw', aes, publicKey, {name:'RSA-OAEP'});
  const sealed = await subtle.encrypt({name:'AES-GCM', iv,
    additionalData: encoder.encode(input.session_id), tagLength:128},
    aes, encoder.encode(JSON.stringify(input.plaintext)));
  const b64 = v => Buffer.from(v).toString('base64');
  process.stdout.write(JSON.stringify({session_id:input.session_id,
    encrypted_key:b64(wrapped), iv:b64(iv), ciphertext:b64(sealed)}));
})().catch(() => { process.stderr.write('encryption failed'); process.exit(1); });
"""


def encrypt_in_webcrypto(session, plaintext):
    """Exchange plaintext with a local fixture process, not the MCP server."""
    request = {"session_id": session["session_id"], "public_key_spki": session["public_key_spki"],
               "plaintext": plaintext}
    result = subprocess.run([NODE, "-e", JS_ENCRYPT], input=json.dumps(request), capture_output=True,
                            text=True, check=True, timeout=20)
    return json.loads(result.stdout)


@pytest.mark.skipif(NODE is None, reason="Node WebCrypto is not installed")
@pytest.mark.asyncio
async def test_webcrypto_payload_is_saved_by_real_stdio_server_without_plaintext_on_wire(tmp_path):
    secret = "合成-$'\"`-" + secrets.token_urlsafe(24)
    environment = {k: v for k, v in os.environ.items()
                   if not k.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    environment.update(DERBYSOFT_LOGS_HOME=str(tmp_path), DERBYSOFT_FIXTURE_SECRET=secret)
    command = StdioServerParameters(command=sys.executable, args=["-I", str(FIXTURE)], env=environment)
    async with asyncio.timeout(35), Client(command, mode="legacy", read_timeout_seconds=20) as session:
        draft = await session.call_tool("settings_update", {"set": {"new_environment_id": "uat"}})
        assert not draft.is_error
        created = await session.call_tool("create_environment", {})
        assert not created.is_error
        current = await session.call_tool("settings_read", {})
        metadata = current.structured_content["metadata"]
        begin = await session.call_tool("begin_settings_save", {"environments": ["uat"],
            "expected_revisions": {"uat": metadata["environments"]["uat"]["revision"]},
            "expected_settings_revision": metadata["settings_revision"]})
        assert not begin.is_error
        plaintext = {"set": {"env__uat__opensearch__url": "https://uat.example.test",
                             "env__uat__opensearch__username": "fixture-user",
                             "env__uat__opensearch__default_index": "fixture-*"},
                     "secrets": {"uat": {"opensearch": secret}}}
        encrypted = await asyncio.to_thread(encrypt_in_webcrypto, begin.structured_content, plaintext)
        assert secret not in json.dumps(encrypted, ensure_ascii=False)
        saved = await session.call_tool("save_settings_secure", encrypted)
        assert not saved.is_error
        assert secret not in json.dumps(saved.structured_content, ensure_ascii=False)
        assert secret not in json.dumps([item.model_dump() for item in saved.content], ensure_ascii=False)
        check = await session.call_tool("fixture_credential_matches", {})
        assert check.structured_content == {"matches": True}
        read = await session.call_tool("settings_read", {})
        assert read.structured_content["values"]["env__uat__opensearch__default_index"] == "fixture-*"
        assert secret not in json.dumps(read.structured_content, ensure_ascii=False)
        replay = await session.call_tool("save_settings_secure", encrypted)
        assert replay.is_error

        # A session bound to UAT cannot smuggle a PROD secret into the same
        # atomic edit, and its public UAT changes must not be partially saved.
        draft = await session.call_tool("settings_update", {"set": {"new_environment_id": "prod"}})
        assert not draft.is_error
        assert not (await session.call_tool("create_environment", {})).is_error
        read = await session.call_tool("settings_read", {})
        metadata = read.structured_content["metadata"]
        second = await session.call_tool("begin_settings_save", {"environments": ["uat"],
            "expected_revisions": {"uat": metadata["environments"]["uat"]["revision"]},
            "expected_settings_revision": metadata["settings_revision"]})
        assert not second.is_error
        before = (tmp_path / "uat.json").read_bytes()
        attack = {"set": {"env__uat__opensearch__username": "wrong-user"},
                  "secrets": {"prod": {"opensearch": secret}}}
        encrypted_attack = await asyncio.to_thread(encrypt_in_webcrypto, second.structured_content, attack)
        rejected = await session.call_tool("save_settings_secure", encrypted_attack)
        assert rejected.is_error
        assert secret not in json.dumps([item.model_dump() for item in rejected.content], ensure_ascii=False)
        assert (tmp_path / "uat.json").read_bytes() == before
        assert (await session.call_tool("fixture_credential_matches", {})).structured_content == {"matches": True}

        # A competing editor after begin must prevent an outdated secret or
        # public setting from overwriting its fresh profile.
        fresh = await session.call_tool("settings_read", {})
        metadata = fresh.structured_content["metadata"]
        pending = await session.call_tool("begin_settings_save", {"environments": ["uat"],
            "expected_revisions": {"uat": metadata["environments"]["uat"]["revision"]},
            "expected_settings_revision": metadata["settings_revision"]})
        assert not pending.is_error
        assert not (await session.call_tool("settings_update", {"set": {
            "env__uat__opensearch__default_index": "newer-*"}})).is_error
        before = (tmp_path / "uat.json").read_bytes()
        encrypted_stale = await asyncio.to_thread(encrypt_in_webcrypto, pending.structured_content, plaintext)
        assert (await session.call_tool("save_settings_secure", encrypted_stale)).is_error
        assert (tmp_path / "uat.json").read_bytes() == before
        assert (await session.call_tool("fixture_credential_matches", {})).structured_content == {"matches": True}
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()
