from datetime import datetime

from pydantic import BaseModel, ConfigDict

from erosion.repositories.models import StatusAnalise


class AnaliseRequest(BaseModel):
    microbacia_id: int
    modelo_id: int
    caminho_imagem: str


class AnaliseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    microbacia_id: int
    modelo_id: int
    status: StatusAnalise
    caminho_mosaico_resultado: str | None
    criado_em: datetime
    concluido_em: datetime | None


class StatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusAnalise
    mensagem_erro: str | None
