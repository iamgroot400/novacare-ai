from app.agent.tools import build_tools


def _tool(name):
    return next(t for t in build_tools() if t.name == name)


def test_escalate_does_not_ask_the_model_for_the_conversation_id():
    # The model invented ids like "3"; Groq rejected the call (400) and the turn failed.
    assert set(_tool("escalate_to_human").args) == {"reason"}


def test_bad_tool_arguments_go_back_to_the_model_as_text():
    # Validation fails before the tool body runs, so no run context is needed.
    out = _tool("get_order").invoke({"order_id": "not-an-order"})
    assert isinstance(out, str) and out
