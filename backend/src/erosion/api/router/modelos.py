from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from erosion.api.deps import get_db_session
from erosion.services import modeloService

router = APIRouter(prefix="/modelos", tags=["modelos"])


class ModeloResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    versao: str
    criado_em: datetime


@router.get("", response_model=list[ModeloResponse])
def listar_modelos(db: Session = Depends(get_db_session)):
    return modeloService.listar_modelos(db)
