from core.registry.agents import governance_agent_registry


def test_registry_contains_18_governance_agents() -> None:
    agents = governance_agent_registry.list_agents()
    assert len(agents) == 18


def test_registry_exposes_implemented_agents() -> None:
    implemented = governance_agent_registry.list_agents(implemented_only=True)
    implemented_ids = {agent["agent_id"] for agent in implemented}
    assert implemented_ids == {
        "cabinet.coordinator",
        "silijian.approver",
        "censorship.inspector",
        "jinyiwei.advisor",
    }


def test_registry_exposes_local_model_capabilities() -> None:
    agent = governance_agent_registry.get_agent("cabinet.coordinator")
    assert agent is not None
    assert "remote_api" in agent["supported_model_sources"]
    assert "local_distilled" in agent["supported_model_sources"]
    assert "local_full" in agent["supported_model_sources"]
    assert agent["local_model_size_limit"] == "none_by_system"
