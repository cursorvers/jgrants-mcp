from jgrants_mcp_server import placeholder


def test_placeholder_returns_text() -> None:
    assert placeholder().startswith("jgrants_mcp_server")
