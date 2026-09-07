from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    source_database_dsn: SecretStr = SecretStr("dbname=pubnub_development host=/tmp")
    battery_floor_v: float = Field(default=305.2, gt=0, allow_inf_nan=False)

    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://pap:pap_local_only@127.0.0.1:55432/pap"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            valid = url.drivername == "postgresql+psycopg" and url.host and url.database
        except (ArgumentError, ValueError):
            valid = False
        if not valid:
            raise ValueError("Use a postgresql+psycopg URL with a host and database name")
        return value
