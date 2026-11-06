"""Test-only stdio host with an in-memory credential store."""
import hmac
import os

from derbysoft_logs import config, settings_server


store = {}
config.keyring.set_password = lambda service, account, value: store.update({(service, account): value})
config.keyring.get_password = lambda service, account: store.get((service, account))
config.keyring.delete_password = lambda service, account: store.pop((service, account), None)


@settings_server.mcp.tool()
def fixture_credential_matches() -> dict[str, bool]:
    try:
        value = config.load_profile("uat").get("opensearch", {}).get("password", "")
    except config.ConfigurationError:
        value = ""
    return {"matches": hmac.compare_digest(value.encode(), os.environ["DERBYSOFT_FIXTURE_SECRET"].encode())}


if __name__ == "__main__":
    settings_server.main()
