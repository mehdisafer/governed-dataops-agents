"""Failure-aware metrics tests; no live model, network or Docker required."""

from governed_dataops.model_server_metrics import (
    COUNTERS,
    model_metric_delta,
    parse_metric_snapshot,
)


def test_allowlisted_llama_metrics_and_non_numeric_samples():
    raw = """
# HELP llamacpp:prompt_tokens_total Prompt processing
llamacpp:prompt_tokens_total 120
llamacpp:tokens_predicted_total 34
llamacpp:prompt_seconds_total 12.5
llamacpp:tokens_predicted_seconds_total 24.250000
llamacpp:requests_processing 0
llamacpp:requests_deferred 0
llamacpp:secret_or_unknown 777
llamacpp:tokens_predicted_total{model="other"} 9000
llamacpp:prompt_seconds_total NaN
"""
    observed = parse_metric_snapshot(raw)
    assert set(observed) == set(COUNTERS) | {
        "llamacpp:requests_processing", "llamacpp:requests_deferred"
    }
    assert observed["llamacpp:tokens_predicted_total"] == 34
    assert observed["llamacpp:prompt_seconds_total"] == 12.5


def test_missing_or_duplicated_metric_stays_unknown():
    observed = parse_metric_snapshot(
        "llamacpp:prompt_tokens_total 7\nllamacpp:prompt_tokens_total 8\n"
        "llamacpp:tokens_predicted_total Inf\n"
        "llamacpp:requests_processing -1\n"
        "llamacpp:requests_deferred 2\n"
    )
    assert observed == {"llamacpp:requests_deferred": 2}


def test_full_counter_delta_preserves_duration_and_boundary_gauges():
    before = {
        "llamacpp:prompt_tokens_total": 100,
        "llamacpp:tokens_predicted_total": 20,
        "llamacpp:prompt_seconds_total": 3.2,
        "llamacpp:tokens_predicted_seconds_total": 5.25,
        "llamacpp:requests_processing": 0,
        "llamacpp:requests_deferred": 0,
    }
    after = {
        "llamacpp:prompt_tokens_total": 180,
        "llamacpp:tokens_predicted_total": 48,
        "llamacpp:prompt_seconds_total": 5.7,
        "llamacpp:tokens_predicted_seconds_total": 14.75,
        "llamacpp:requests_processing": 0,
        "llamacpp:requests_deferred": 0,
    }
    report = model_metric_delta(before, after)
    assert report["status"] == "observed"
    assert report["counter_deltas"]["llamacpp:prompt_tokens_total"] == 80
    assert report["counter_deltas"]["llamacpp:tokens_predicted_seconds_total"] == 9.5
    assert report["boundary_gauges"]["llamacpp:requests_deferred"] == {
        "before": 0, "after": 0
    }
    assert any("cannot establish transient server queue" in x for x in report["limits"])


def test_missing_scrape_and_counter_reset_cannot_become_zero_work():
    reset = model_metric_delta(
        {"llamacpp:prompt_tokens_total": 150, "llamacpp:tokens_predicted_total": 12},
        {"llamacpp:prompt_tokens_total": 2, "llamacpp:tokens_predicted_total": 18},
    )
    assert reset["status"] == "partial"
    assert reset["counter_deltas"]["llamacpp:prompt_tokens_total"] is None
    assert reset["counter_deltas"]["llamacpp:tokens_predicted_total"] == 6
    assert reset["counter_resets"] == ["llamacpp:prompt_tokens_total"]
    missing = model_metric_delta(None, {"llamacpp:prompt_tokens_total": 0})
    assert missing["status"] == "unavailable"
    assert all(value is None for value in missing["counter_deltas"].values())


def test_no_server_samples_never_claim_inference_only_timing():
    report = model_metric_delta(
        parse_metric_snapshot("llamacpp:requests_deferred 0\n"),
        parse_metric_snapshot("llamacpp:requests_deferred 0\n"),
    )
    assert report["status"] == "unavailable"
    assert report["boundary_gauges"]["llamacpp:requests_deferred"] == {
        "before": 0, "after": 0
    }
