from pathlib import Path

from core.registry.agents import governance_agent_registry


def test_registry_contains_18_governance_agents() -> None:
    agents = governance_agent_registry.list_agents()
    assert len(agents) == 18


def test_registry_exposes_implemented_agents() -> None:
    implemented = governance_agent_registry.list_agents(implemented_only=True)
    assert len(implemented) == 18


def test_every_agent_has_soul_file_and_style_contract() -> None:
    agents = governance_agent_registry.list_agents()
    for agent in agents:
        assert agent["soul_path"] is not None
        assert Path(agent["soul_path"]).exists()
        assert agent["style_contract"] is not None
        assert agent["style_contract"]["input_fields"]
        assert agent["style_contract"]["output_fields"]


def test_registry_exposes_local_model_capabilities() -> None:
    agent = governance_agent_registry.get_agent("cabinet.coordinator")
    assert agent is not None
    assert "remote_api" in agent["supported_model_sources"]
    assert "local_distilled" in agent["supported_model_sources"]
    assert "local_full" in agent["supported_model_sources"]
    assert agent["local_model_size_limit"] == "none_by_system"


def test_registry_exposes_style_contracts_listing() -> None:
    contracts = governance_agent_registry.list_style_contracts()
    style_ids = {item["style_id"] for item in contracts}
    assert "coordinator" in style_ids
    assert "repair_advisor" in style_ids
