"""Regression coverage for the computer-use schema contract (#109656)."""


def test_schema_qualifies_minimized_windows_support():
    from tools.computer_use.schema import COMPUTER_USE_SCHEMA

    description = COMPUTER_USE_SCHEMA["description"]
    assert "hidden/minimized windows" not in description
    assert "window_minimized" in description
    assert "returned verdict" in description
    assert "capture again" in description
