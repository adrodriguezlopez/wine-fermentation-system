"""
Test suite for IAnalysisEngineClient interface contract.
These tests define the expected behavior that any implementation must follow.
"""
import pytest


def test_analysis_engine_client_interface_methods() -> None:
    """
    Test to ensure IAnalysisEngineClient defines EXACTLY the required methods.
    If a new method is added, this test will fail,
    enforcing TDD and documentation updates.
    """
    try:
        from service_component.interfaces import IAnalysisEngineClient
    except ImportError:
        pytest.fail("IAnalysisEngineClient interface is not defined")

    required_methods = {
        "analyze_sample",
        "get_trend_analysis",
        "predict_completion",
        "detect_anomalies",
        "get_recommendations",
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name
        for name, value in IAnalysisEngineClient.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"
