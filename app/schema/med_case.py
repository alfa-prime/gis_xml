from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Person(BaseModel):
    model_config = ConfigDict(extra="ignore")

    surname: str | None = Field(None, validation_alias="Person_Surname")
    first_name: str | None = Field(None, validation_alias="Person_Firname")
    second_name: str | None = Field(None, validation_alias="Person_Secname")

    document_type: str | None = Field(None, validation_alias="DocumentType_Name")
    document_number: str | None = Field(None, validation_alias="Document_Num")
    document_series: str | None = Field(None, validation_alias="Document_Ser")
    document_date: str | None = Field(None, validation_alias="Document_begDate")

    inn: str | None = Field(None, validation_alias="Person_Inn")
    snils: str | None = Field(None, validation_alias="Person_Snils")

    polis_number: str | None = Field(None, validation_alias="Polis_Num")
    polis_date: str | None = Field(None, validation_alias="Polis_begDate")


class MedicalCase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    person: Person | None = Field(
        default=None,
        validation_alias="person_info",
    )

    @field_validator("person", mode="before")
    @classmethod
    def extract_person_info(cls, value: Any) -> Any:
        if isinstance(value, list):
            return value[0] if value else None

        return value