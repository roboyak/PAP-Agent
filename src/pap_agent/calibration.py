"""Maintain point-error escalation rules; qualitative labels are not probabilities."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from statistics import mean

from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.database import Database


def calibration_report(
    database: Database,
    source_kind: str,
    forecast_version: str,
    *,
    now: datetime | None = None,
) -> dict:
    now, settings = now or datetime.now(UTC), Settings()
    window = settings.calibration_window_samples
    reviewed_at = settings.calibration_reviewed_at
    policy = {
        "bias_limit_kw": settings.calibration_bias_limit_kw,
        "drift_limit_kw": settings.calibration_drift_limit_kw,
        "window_samples": window,
        "review_days": settings.calibration_review_days,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
    }
    policy_id = (
        "point-error-v2-"
        + hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()[:12]
    )
    with database.session() as session:
        rows = (
            session.execute(
                text("""SELECT o.id, m.solar_bias_kw,
                (m.payload->>'availability_error_kw')::float AS availability_error_kw,
                (o.payload->'sample'->>'observed_at')::timestamptz AS observed_at
            FROM outcome_metrics m JOIN outcome_records o USING (id)
            WHERE m.source_kind = :source AND m.forecast_version = :version
            ORDER BY (o.payload->'sample'->>'observed_at')::timestamptz DESC, o.id
            LIMIT :limit"""),
                {"source": source_kind, "version": forecast_version, "limit": 2 * window},
            )
            .mappings()
            .all()
        )
    # Real feedback expires. Synthetic demonstration clocks never become live evidence.
    cutoff = now - timedelta(days=policy["review_days"])
    eligible = (
        [row for row in rows if cutoff <= row["observed_at"] <= now]
        if source_kind.startswith("live")
        else rows
    )
    recent, prior = eligible[:window], eligible[window:]
    bias = mean(row["solar_bias_kw"] for row in recent) if recent else None
    previous = mean(row["solar_bias_kw"] for row in prior) if len(prior) == window else None
    drift = bias - previous if previous is not None else None
    signals = []
    if bias is not None and bias > policy["bias_limit_kw"]:
        signals.append("solar_overestimation")
    if drift is not None and abs(drift) > policy["drift_limit_kw"]:
        signals.append("error_drift")
    due_at = reviewed_at + timedelta(days=policy["review_days"]) if reviewed_at else None
    review_due = reviewed_at is None or reviewed_at > now or now >= due_at
    stale = bool(rows and not eligible)
    escalate = bool(signals)
    guidance = (
        "Recent solar overestimation; review thresholds and refresh solar evidence"
        if "solar_overestimation" in signals
        else "Recent forecast errors changed; review thresholds for current conditions"
        if "error_drift" in signals
        else "Feedback expired; collect new outcomes before re-tuning"
        if stale
        else "No overestimation signal in recent outcomes"
        if recent
        else "No outcome feedback yet; collect measured comparisons"
    )
    return {
        "source_kind": source_kind,
        "forecast_version": forecast_version,
        "evaluated_at": now.isoformat(),
        "policy_id": policy_id,
        "policy": policy,
        "samples": len(recent),
        "comparison_samples": len(prior),
        "outcome_ids": [str(row["id"]) for row in eligible],
        "mean_solar_bias_kw": bias,
        "prior_mean_solar_bias_kw": previous,
        "mean_availability_error_kw": mean(row["availability_error_kw"] for row in recent)
        if recent
        else None,
        "error_drift_kw": drift,
        "drift_status": "measured" if drift is not None else "insufficient_data",
        "last_observed_at": rows[0]["observed_at"].isoformat() if rows else None,
        "stale": stale,
        "signals": signals,
        "escalate": escalate,
        "confidence": "low" if escalate or stale else "reduced",
        "guidance": guidance,
        "review_due_at": due_at.isoformat() if due_at else None,
        "review_due": review_due,
        "review_required": review_due or stale or escalate,
        "ece": {
            "status": "unavailable",
            "reason": "Qualitative labels; probability calibration is unavailable.",
        },
        "distribution_shift": "Error-mean drift proxy only; not a formal distribution-shift test.",
    }


def calibration(database: Database, source_kind: str, forecast_version: str) -> dict | None:
    report = calibration_report(database, source_kind, forecast_version)
    return report if report["last_observed_at"] else None


if __name__ == "__main__":
    import argparse

    from pap_agent.core import FORECAST_VERSION, STORED_WEATHER_VERSION
    from pap_agent.selection import WING_FLOORS, RunSelection

    parser = argparse.ArgumentParser(description="Read-only preview of current calibration policy.")
    parser.add_argument("--wing", choices=list(WING_FLOORS), default="1.24")
    parser.add_argument("--source", choices=["live", "synthetic"], default="live")
    args = parser.parse_args()
    database = Database(Settings())
    try:
        source = RunSelection(wing=args.wing).feedback_scope(args.source)
        version = FORECAST_VERSION if args.source == "synthetic" else STORED_WEATHER_VERSION
        print(json.dumps(calibration_report(database, source, version), indent=2))
    finally:
        database.close()
