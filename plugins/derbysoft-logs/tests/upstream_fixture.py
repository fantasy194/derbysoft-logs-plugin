"""Real upstream stdio server with only network functions replaced for tests."""
from derbysoft_logs.cli import prepare_opensearch_environment
import tools.tool_filter
import tools.tools

prepare_opensearch_environment({"opensearch": {
    "url": "https://opensearch.example.test", "username": "fixture", "password": "fixture-only",
}})

async def version(*args, **kwargs):
    return "2.19.1"


async def search(*args, **kwargs):
    return {"hits": {"total": {"value": 1, "relation": "eq"}, "hits": [
        {"_index": "perf_fixture", "_id": "fixture-1", "_source": {
            "process": "Book", "process_result": "Success", "echo_token": "fixture-trace",
        }},
    ]}}


tools.tool_filter.get_opensearch_version = version
tools.tools.get_opensearch_version = version
tools.tools.search_index = search

if __name__ == "__main__":
    from derbysoft_logs.cli import launch_opensearch
    launch_opensearch()
