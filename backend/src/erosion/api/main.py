from fastapi import FastAPI

from erosion.api.router import analises, health, modelos

app = FastAPI(title="GeoProcessamento - Erosion Detection API")

app.include_router(health.router)
app.include_router(modelos.router)
app.include_router(analises.router)
