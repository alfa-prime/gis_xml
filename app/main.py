from fastapi import FastAPI

from app.router import health_router


tags_metadata = []

app = FastAPI(
    tags=tags_metadata,
    root_path="/gis_oms",
    title="GIS-OMS",
    description="GIS-OMS",
    version="0.1.0",
    swagger_ui_parameters={"persistAuthorization": True}, # для разработки вводим API KEY один раз
)


app.include_router(health_router)