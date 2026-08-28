from fastapi import FastAPI

from app.router import health_router


tags_metadata = []

app = FastAPI(
    tags=tags_metadata,
    root_path="/gis_oms",
    title="GIS-OMS",
    description="GIS-OMS",
    version="0.0.1",
)


app.include_router(health_router)