# Calibration maintenance

Checkpoint 6.1 feedback asked for ongoing threshold re-tuning as operating conditions change.
PR21 makes that maintenance visible without changing T5/T6 authority.

## What is measured

PAP compares predicted solar power with later observed point-power samples. Positive bias
means solar was overestimated. The policy checks the newest 20 eligible outcomes, rather
than averaging all history. With 40 outcomes, it also compares the newest 20 with the
preceding 20; an absolute change in mean error is the drift signal. Fewer samples explicitly
show insufficient data for drift. Overestimation can still trigger the conservative demo
rule from one observation; that is not statistical calibration evidence.

Live outcomes expire from escalation statistics after the configured review interval.
Existing RAG memory retrieval retains its separate eligibility rules; this change does not
expire outcome documents from memory. Each wing and forecast version
has its own history; synthetic outcomes remain separate. Historical simulation cannot update
or use live outcome feedback. Existing outcomes and legacy summaries remain stored.

The defaults are demonstration values, not validated operating thresholds:

| ENV setting | Default | Purpose |
| --- | --- | --- |
| `CALIBRATION_BIAS_LIMIT_KW` | `0.25` | Escalate when recent mean overestimation exceeds this |
| `CALIBRATION_DRIFT_LIMIT_KW` | `0.25` | Escalate when absolute error-mean change exceeds this |
| `CALIBRATION_WINDOW_SAMPLES` | `20` | Size of each of the two adjacent windows |
| `CALIBRATION_REVIEW_DAYS` | `7` | Review cadence and maximum live-outcome age in escalation statistics |
| `CALIBRATION_REVIEWED_AT` | Unset | Operator-configured date of threshold review |

Signals invoke the existing bounded reasoning flow and lower qualitative confidence.
Expired feedback lowers confidence and requests fresh outcomes; it cannot drive a model
search from old errors. An overdue review is an operator reminder, not a new model call.
When outcome feedback exists, the graph saves its policy hash, settings, sample IDs and
decision in the assessment record; publication reuses that snapshot. With no outcomes, the
assessment records no feedback and publication preserves that absence. Retuning later cannot rewrite or change a resumed run's
assessment. T5/T6 voltage, surplus/cap checks and T7 final publication checks retain authority.

## Review and re-tune

1. Evaluate genuinely newer live readings in Inspector. Review after a site/load/weather
   change or an error alert, and at least at the configured cadence.
2. Open **Memory → Current calibration maintenance → Check current calibration**. Check
   the source, sample counts, recent errors, drift availability and review date.
3. Check measurement quality and operating context. Choose candidate thresholds using
   operational tolerances and new evidence; avoid raising a threshold simply to clear an alert.
4. Preview candidate settings with the CLI below. It only reads PAP outcome records and
   does not change the running service or source database. Check candidate behavior against
   separate subsequent outcomes before adopting it; the preview is not an accuracy benchmark.
5. Update ENV thresholds and the review timestamp after review, then restart. Preserve the
   reason/evidence for the change in a terse git comment. New runs with outcome feedback record the new policy ID.

From the repository root, with the local PAP database running:

```bash
uv run --locked python -m pap_agent.calibration --wing 1.24
# Example candidate only; choose actual settings from your reviewed evidence.
CALIBRATION_BIAS_LIMIT_KW=0.5 CALIBRATION_DRIFT_LIMIT_KW=0.4 \
  uv run --locked python -m pap_agent.calibration --wing 1.24
```

Defaults are shared across wings, while measurements stay isolated. Per-wing threshold
policies, automatic tuning and scheduled notifications are deferred. The review date is
configured metadata, not proof that a human reviewed a policy; changing that date alone
does not clear measured error signals.

Current live calibration uses `solar-persistence-stored-weather-v1`. Previous runs using
synthetic weather keep their original `solar-persistence-demo-v1` outcomes and saved
feedback, but those outcomes cannot trigger escalation or enter outcome memory for the new
predictor. The sunny demo continues to use its original version. New live runs initially
have no matching outcomes until fresh feedback is collected.

## Metric limits

ECE is unavailable: this MVP publishes qualitative confidence labels, not probabilities.
ECE compares predicted confidence with observed correctness; implementing it would require
a defined prediction event, numeric probabilities and suitable held-out outcomes.
[Guo et al., 2017](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf).

Error drift is a maintenance proxy for changing conditions, not a formal distribution-shift
test. Good calibration on one data distribution does not establish reliability after a
shift. [Ovadia et al., 2019](https://arxiv.org/abs/1906.02530).
Earlier synthetic weather, conservative stored-weather ratios, overlapping point forecasts
and small samples limit the current evidence.
