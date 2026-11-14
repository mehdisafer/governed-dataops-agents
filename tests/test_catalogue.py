"""Published capability metadata must not drift from the wire contract."""

import json
from importlib.resources import files

from governed_dataops.contracts import CATALOG_VERSION, CONTRACT_VERSION, POLICY_VERSION, ToolName


def test_catalogue_versions_and_tools_match_the_typed_boundary():
    catalogue = json.loads(files("governed_dataops").joinpath("catalogue-v1.json").read_text())
    assert catalogue["catalog_version"] == CATALOG_VERSION
    assert catalogue["contract_version"] == CONTRACT_VERSION
    assert catalogue["policy_version"] == POLICY_VERSION
    assert {tool["name"] for tool in catalogue["tools"]} == {tool.value for tool in ToolName}
    assert all(
        profile["catalog_version"] == CATALOG_VERSION for profile in catalogue["profiles"].values()
    )
    assert catalogue["profiles"]["diagnostic-agent"]["model_tools"] == []
    assert catalogue["profiles"]["deterministic-runbook"]["model_used"] is False
