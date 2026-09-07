"""T7 publishes validated evaluations; repeated calls preserve the original decision."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid5

from pydantic import AwareDatetime, BaseModel, Field

from pap_agent.agents import validated_advice
from pap_agent.core import Calculation, validate_candidate
from pap_agent.database import Database
from pap_agent.domain import PAP, Scenario
from pap_agent.evidence import Evidence
from pap_agent.outcomes import calibration
from pap_agent.reasoning import get_record
from pap_agent.store import get_calculation, get_evidence, get_publication, save_publication


class PublishedPAP(BaseModel):
    id: UUID
    episode_id: UUID
    evidence_id: UUID
    calculation_id: UUID | None
    generated_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Literal["valid", "withheld"]
    profile: PAP | None = None
    evidence: Scenario | None = None
    observed_age_seconds: float | None = None
    reason: str
    evaluation_only: Literal[True] = True
    feedback: dict | None = None
    interpretation: dict | None = None


def publish(
    database: Database,
    episode_id: UUID,
    evidence_id: UUID,
    calculation_id: UUID | None,
    *,
    interpretation_id=None,
    retrieval_id=None,
) -> PublishedPAP:
    publication_id = uuid5(episode_id, "publication")
    stored = get_publication(database, publication_id)
    if stored:
        return PublishedPAP.model_validate(stored)
    evidence = Evidence.model_validate(get_evidence(database, evidence_id))
    result = PublishedPAP(
        id=publication_id,
        episode_id=episode_id,
        evidence_id=evidence_id,
        calculation_id=calculation_id,
        status="withheld",
        evidence=evidence.scenario,
        reason=evidence.reason,
    )
    if calculation_id and evidence.scenario:
        calculation = Calculation.model_validate(get_calculation(database, calculation_id))
        result.reason = "; ".join(calculation.validation) or "T6 passed; evaluation baseline"
        scenario = evidence.scenario
        age = (result.generated_at - scenario.telemetry.observed_at).total_seconds()
        result.observed_age_seconds = (
            round(age, 1) if scenario.telemetry.data_mode == "live" else None
        )
        if scenario.telemetry.data_mode == "live" and not 0 <= age <= 300:
            result.reason = "Evidence became stale before publication"
        elif (
            evidence.status == calculation.status == "valid"
            and calculation.pap
            and (calculation.evidence_id == evidence.id)
        ):
            errors = validate_candidate(scenario, calculation.forecast, calculation.pap.intervals)
            if errors:
                result.reason = "; ".join(errors)
            else:
                result.status, result.profile = "valid", calculation.pap
                result.feedback = calibration(
                    database, scenario.telemetry.data_mode, calculation.forecast_version
                )
                if result.feedback:
                    result.profile.confidence = result.feedback["confidence"]
                if interpretation_id:
                    record = get_record(database, interpretation_id)
                    selected = get_record(database, retrieval_id)["selected"]
                    advice = validated_advice(record, str(evidence_id), selected)
                    result.interpretation = {
                        "record_id": interpretation_id,
                        "accepted": advice is not None,
                        "advice": advice.model_dump() if advice else None,
                    }
                    if advice is None or advice.confidence == "lower" or advice.insufficient:
                        result.profile.confidence = "low"
    save_publication(database, result.model_dump(mode="json"))
    return PublishedPAP.model_validate(get_publication(database, publication_id))
