import pytest
from incidents import ALL, AUTH_DENIED_SPIKE, NO_LOGS, PAYMENT_ERRORS, TRUNCATED

from chatbot_rag.adapters.input.dto import ContexteIncidentDTO


@pytest.mark.parametrize("payload", ALL, ids=[p["incident_id"] for p in ALL])
def test_fake_incidents_are_valid(payload):
    assert ContexteIncidentDTO(**payload).to_trace()


def test_trace_lists_features_with_sign_and_logs_in_order():
    trace = ContexteIncidentDTO(**PAYMENT_ERRORS).to_trace()
    assert "basecamp-payment__success_count: -4.3" in trace
    assert trace.index("ERROR status=500") < trace.index("CRITICAL status=503")


def test_trace_flags_truncated_logs():
    assert "(3/5000, tronqués)" in ContexteIncidentDTO(**TRUNCATED).to_trace()
    assert "tronqués" not in ContexteIncidentDTO(**AUTH_DENIED_SPIKE).to_trace()


def test_trace_without_logs_or_features():
    trace = ContexteIncidentDTO(**NO_LOGS).to_trace()
    assert "(0/0):" in trace
