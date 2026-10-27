from fastapi import FastAPI

from erosion.api.router import analises, health, imagens, microbacias, modelos

app = FastAPI(title="GeoProcessamento - Erosion Detection API")

app.include_router(health.router)
app.include_router(modelos.router)
app.include_router(microbacias.router)
app.include_router(imagens.router)
app.include_router(analises.router)
