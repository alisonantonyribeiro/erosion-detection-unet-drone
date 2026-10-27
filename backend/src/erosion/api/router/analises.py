from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erosion.api.deps import get_db_session
from erosion.api.schemas.analise import AnaliseRequest, AnaliseResponse, StatusResponse
from erosion.api.schemas.resultado import ResultadoResponse
from erosion.repositories import analiseRepository as repo
from erosion.repositories import microbaciaRepository
from erosion.repositories.models import Modelo, StatusAnalise
from erosion.services import resultadoService
from workers.celeryApp import celery_app

router = APIRouter(prefix="/analises", tags=["analises"])


@router.get("", response_model=list[AnaliseResponse])
def listar_analises(
    microbacia_id: int | None = None,
    status: StatusAnalise | None = None,
    db: Session = Depends(get_db_session),
):
    return repo.listar_todas(db, microbacia_id=microbacia_id, status=status)


@router.post("", response_model=AnaliseResponse)
def criar_analise(payload: AnaliseRequest, db: Session = Depends(get_db_session)):
    # SQLite nao checa FK por padrao: sem isso a analise so falharia depois, no worker
    if microbaciaRepository.buscar_por_id(db, payload.microbacia_id) is None:
        raise HTTPException(status_code=404, detail="Microbacia nao encontrada")
    if db.get(Modelo, payload.modelo_id) is None:
        raise HTTPException(status_code=404, detail="Modelo nao encontrado")

    analise = repo.criar_analise(db, payload.microbacia_id, payload.modelo_id)
    celery_app.send_task("processar_analise", args=[analise.id, payload.caminho_imagem])
    return analise


@router.get("/{analise_id}/status", response_model=StatusResponse)
def consultar_status(analise_id: int, db: Session = Depends(get_db_session)):
    analise = repo.buscar_por_id(db, analise_id)
    if analise is None:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")
    return analise


@router.get("/{analise_id}/resultado", response_model=ResultadoResponse)
def consultar_resultado(analise_id: int, db: Session = Depends(get_db_session)):
    analise = repo.buscar_por_id(db, analise_id)
    if analise is None:
        raise HTTPException(status_code=404, detail="Analise nao encontrada")
    if not analise.caminho_mosaico_resultado:
        raise HTTPException(status_code=409, detail="Analise ainda nao foi concluida")

    areas = resultadoService.calcular_areas_a_partir_do_mosaico(analise.caminho_mosaico_resultado)
    return {"areas_por_classe": areas}
