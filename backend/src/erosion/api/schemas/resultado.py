from pydantic import BaseModel


class AreaClasse(BaseModel):
    hectares: float
    percentual: float


class ResultadoResponse(BaseModel):
    areas_por_classe: dict[str, AreaClasse]
