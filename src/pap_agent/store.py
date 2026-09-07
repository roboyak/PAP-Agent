"""Explicit SQL keeps this small repository layer easy to follow."""

import json

from sqlalchemy import text

from pap_agent.database import Database
from pap_agent.domain import Scenario


def save_episode(database: Database, payload: dict) -> None:
    with database.session() as session:
        session.execute(
            text("""INSERT INTO episode_records (id, payload)
            VALUES (:id, CAST(:payload AS jsonb)) ON CONFLICT (id) DO NOTHING"""),
            {"id": payload["episode_id"], "payload": json.dumps(payload)},
        )


def get_episode(database: Database, episode_id) -> dict | None:
    with database.session() as session:
        return session.execute(
            text("SELECT payload FROM episode_records WHERE id = :id"), {"id": episode_id}
        ).scalar_one_or_none()


def save_evidence(database: Database, payload: dict) -> None:
    with database.session() as session:
        session.execute(
            text("""INSERT INTO evidence_records (id, payload)
            VALUES (:id, CAST(:payload AS jsonb)) ON CONFLICT (id) DO NOTHING"""),
            {"id": payload["id"], "payload": json.dumps(payload)},
        )


def save_calculation(database: Database, payload: dict) -> None:
    with database.session() as session:
        session.execute(
            text("""INSERT INTO calculation_records (id, evidence_id, payload)
            VALUES (:id, :evidence_id, CAST(:payload AS jsonb)) ON CONFLICT (id) DO NOTHING"""),
            {
                "id": payload["id"],
                "evidence_id": payload["evidence_id"],
                "payload": json.dumps(payload),
            },
        )


def get_evidence(database: Database, record_id) -> dict | None:
    with database.session() as session:
        return session.execute(
            text("SELECT payload FROM evidence_records WHERE id = :id"), {"id": record_id}
        ).scalar_one_or_none()


def get_calculation(database: Database, record_id) -> dict | None:
    with database.session() as session:
        return session.execute(
            text("SELECT payload FROM calculation_records WHERE id = :id"), {"id": record_id}
        ).scalar_one_or_none()


def save_scenario(database: Database, scenario: Scenario) -> None:
    with database.session() as session:
        session.execute(
            text("""INSERT INTO telemetry_snapshots
                (id, observed_at, battery_voltage_v, solar_power_kw, load_power_kw,
                 source, data_mode, measurement_time_verified)
                VALUES (:id, :observed_at, :battery_voltage_v, :solar_power_kw, :load_power_kw,
                        :source, :data_mode, :measurement_time_verified)
                ON CONFLICT (id) DO NOTHING"""),
            scenario.telemetry.model_dump(),
        )
        session.execute(
            text("""INSERT INTO reserve_policies
                (id, label, min_battery_voltage_v, max_extra_power_kw)
                VALUES (:id, :label, :min_battery_voltage_v, :max_extra_power_kw)
                ON CONFLICT (id) DO NOTHING"""),
            scenario.policy.model_dump(),
        )
        session.execute(
            text("""INSERT INTO scenarios (name, label, telemetry_id, policy_id)
                VALUES (:name, :label, :telemetry_id, :policy_id)
                ON CONFLICT (name) DO NOTHING"""),
            {
                "name": scenario.name,
                "label": scenario.label,
                "telemetry_id": scenario.telemetry.id,
                "policy_id": scenario.policy.id,
            },
        )
        session.execute(
            text("""INSERT INTO weather_intervals
                (scenario_name, starts_at, ends_at, solar_factor, source)
                VALUES (:scenario_name, :starts_at, :ends_at, :solar_factor, :source)
                ON CONFLICT (scenario_name, starts_at) DO NOTHING"""),
            [{"scenario_name": scenario.name, **item.model_dump()} for item in scenario.weather],
        )


def list_scenarios(database: Database) -> list[dict]:
    with database.session() as session:
        return [
            dict(row)
            for row in session.execute(
                text("SELECT name, label FROM scenarios ORDER BY name")
            ).mappings()
        ]


def get_scenario(database: Database, name: str) -> Scenario | None:
    with database.session() as session:
        scenario = (
            session.execute(text("SELECT * FROM scenarios WHERE name = :name"), {"name": name})
            .mappings()
            .one_or_none()
        )
        if scenario is None:
            return None
        telemetry = (
            session.execute(
                text("SELECT * FROM telemetry_snapshots WHERE id = :id"),
                {"id": scenario["telemetry_id"]},
            )
            .mappings()
            .one()
        )
        policy = (
            session.execute(
                text("SELECT * FROM reserve_policies WHERE id = :id"), {"id": scenario["policy_id"]}
            )
            .mappings()
            .one()
        )
        weather = (
            session.execute(
                text(
                    "SELECT * FROM weather_intervals WHERE scenario_name = :name ORDER BY starts_at"
                ),
                {"name": name},
            )
            .mappings()
            .all()
        )
        return Scenario(
            name=name, label=scenario["label"], telemetry=telemetry, policy=policy, weather=weather
        )
