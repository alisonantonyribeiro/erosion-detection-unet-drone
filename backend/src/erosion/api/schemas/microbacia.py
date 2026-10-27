from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MicrobaciaRequest(BaseModel):
    nome: str = Field(min_length=1)
    area_ha: float | None = Field(default=None, gt=0)
    pais: str | None = None
    estado: str | None = None
    cidade: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    descricao: str | None = None


class MicrobaciaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    area_ha: float | None
    pais: str | None
    estado: str | None
    cidade: str | None
    latitude: float | None
    longitude: float | None
    descricao: str | None
    criado_em: datetime | None
