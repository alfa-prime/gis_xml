import asyncio
import json

from fastapi import APIRouter, Security
from loguru import logger

from app.core.dependencies import GatewayServiceDep, verify_api_key
from app.core.error import GatewayError
from app.schema.gateway import GatewayRequest
from app.schema.med_case import MedicalCase
from app.service.gateway import GatewayService

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[Security(verify_api_key)],
)

PAY_TYPE_IDS = {
    "oms": "3010101000000048",
}

CASE_CONCURRENCY = 10


async def fetch_implants(gateway_service: GatewayService, event_service_id: str):
    """
    Получение данных об имплантах
    """
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "EvnUsluga",
                "m": "loadUslugaImplantTypeLinkList",
            },
            "data": {
                "EvnUsluga_id": event_service_id,
            },
        }
    )
    return await gateway_service.make_request(payload)


async def fetch_diagnoses(gateway_service: GatewayService, event_section_id: str):
    """
    Получение данных о диагнозах
    """
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "EvnDiag",
                "m": "loadEvnDiagPSGrid",
            },
            "data": {
                "class": "EvnDiagPSSect",
                "EvnDiagPS_pid": event_section_id,
            },
        }
    )
    return await gateway_service.make_request(payload)


async def fetch_services(gateway_service: GatewayService, event_id: str):
    """
    Получение данных об оказанных услугах
    """
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "EvnUsluga",
                "m": "loadEvnUslugaGrid",
            },
            "data": {
                "pid": event_id,
                "parent": "EvnPS",
            },
        }
    )
    return await gateway_service.make_request(payload)


async def fetch_movements(gateway_service: GatewayService, event_id: str):
    """
    Получение данных о движениях в рамках одной госпитализации
    """
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "EvnSection",
                "m": "loadEvnSectionGrid",
            },
            "data": {
                "EvnSection_pid": event_id,
            },
        }
    )
    return await gateway_service.make_request(payload)


async def fetch_person(
    gateway_service: GatewayService,
    person_id: str,
    server_id: str,
    event_set_date: str,
):
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "Common",
                "m": "loadPersonData",
            },
            "data": {
                "onExpand": "true",
                "Person_id": person_id,
                "Server_id": server_id,
                "Evn_setDT": event_set_date,
                "LoadShort": "false",
                "mode": "PersonInfoPanel",
                "additionalFields": "[]",
            },
        }
    )
    return await gateway_service.make_request(payload)


async def fetch_direction(gateway_service: GatewayService, event_id: str):
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "EvnPS",
                "m": "loadEvnPSEditForm",
            },
            "data": {
                "EvnPS_id": event_id,
                "archiveRecord": "0",
                "delDocsView": "0",
                "attrObjects": '[{"object":"EvnPSEditWindow","identField":"EvnPS_id"}]',
            },
        }
    )
    return await gateway_service.make_request(payload)


async def search_medical_cases(gateway_service: GatewayService):
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "Search",
                "m": "searchData",
            },
            "data": {
                "PersonPeriodicType_id": "1",
                "SearchFormType": "EvnPS",
                # "Person_Surname": "Гаряев", # 2 KSG
                # "Person_Surname": "Чичин",  # сопутствующие диагнозы
                # "Person_Surname": "Азева",  # импланты
                "PayType_id": PAY_TYPE_IDS["oms"],
                "Okei_id": "100",
                "Date_Type": "1",
                "Person_citizen": "1",
                "PersonCardStateType_id": "1",
                "EvnSection_disDate_Range": "01.08.2026 - 03.08.2026",
                "Ksg_Year": "2026",
                "limit": "1000",
                "start": "0",
            },
        }
    )
    result = await gateway_service.make_request(payload)
    return result.get("data", [])


async def process_medical_case(
    gateway_service: GatewayService,
    medical_case: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    async with semaphore:
        event_id: str = medical_case.get("EvnPS_id", "")
        person_id: str = medical_case.get("Person_id", "")
        server_id: str = medical_case.get("Server_id", "")
        event_set_date: str = medical_case.get("EvnPS_setDate", "")

        try:
            person_info, direction, movements, services = await asyncio.gather(
                fetch_person(
                    gateway_service,
                    person_id,
                    server_id,
                    event_set_date,
                ),
                fetch_direction(
                    gateway_service,
                    event_id,
                ),
                fetch_movements(
                    gateway_service,
                    event_id,
                ),
                fetch_services(
                    gateway_service,
                    event_id,
                ),
            )

            medical_case["person_info"] = person_info
            medical_case["direction"] = direction

            movements.sort(key=lambda move: move.get("EvnSection_setDate", ""))

            for movement in movements:
                event_section_id = movement.get("EvnSection_id", "")

                movement["diagnoses"] = await fetch_diagnoses(
                    gateway_service,
                    event_section_id,
                )

                current_services = [
                    service
                    for service in services
                    if service.get("EvnUsluga_pid") == event_section_id
                ]

                for service in current_services:
                    service_code = service.get("Usluga_Code", "")
                    event_service_id = service.get("EvnUsluga_id", "")

                    if service_code == "A16.12.028" or service_code.startswith(
                        "A16.12.026"
                    ):
                        service["implants"] = await fetch_implants(
                            gateway_service,
                            event_service_id,
                        )

                movement["services"] = current_services

            medical_case["movements"] = movements

        except GatewayError as exc:
            logger.error(
                "Ошибка получения медицинского случая | event_id={} | type={}",
                event_id,
                type(exc).__name__,
            )

            medical_case["_load_error"] = {
                "type": type(exc).__name__,
            }

            return medical_case

        finally:
            await asyncio.sleep(0.7)

        return medical_case


@router.post("/medical_cases")
async def get_medical_cases(
    gateway_service: GatewayServiceDep,
):
    medical_cases = await search_medical_cases(gateway_service)

    semaphore = asyncio.Semaphore(CASE_CONCURRENCY)

    medical_cases_raw = await asyncio.gather(
        *[
            process_medical_case(
                gateway_service,
                case,
                semaphore,
            )
            for case in medical_cases
        ]
    )

    # сохраняем сырой ответ
    with open("./debug/medical_cases_raw.json", "w", encoding="utf-8") as f:
        json.dump(
            medical_cases_raw,
            f,
            indent=4,
            ensure_ascii=False,
        )

    # преобразуем через Pydantic-модель
    medical_case_models = [
        MedicalCase.model_validate(case) for case in medical_cases_raw
    ]

    # превращаем модели обратно в обычные dict
    medical_cases_normalized = [
        case.model_dump(exclude_none=True)
        for case in medical_case_models
    ]

    # сохраняем уже очищенную структуру
    with open("./debug/medical_cases_normalized.json", "w", encoding="utf-8") as f:
        json.dump(
            medical_cases_normalized,
            f,
            indent=4,
            ensure_ascii=False,
        )

    return {
        "result": "success",
        "cases_count": len(medical_cases_raw),
    }
