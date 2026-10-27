from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from erosion.api.deps import get_db_session
from erosion.api.schemas.microbacia import MicrobaciaRequest, MicrobaciaResponse
from erosion.repositories import microbaciaRepository as repo

router = APIRouter(prefix="/microbacias", tags=["microbacias"])


@router.post("", response_model=MicrobaciaResponse, status_code=status.HTTP_201_CREATED)
def criar_microbacia(payload: MicrobaciaRequest, db: Session = Depends(get_db_session)):
    return repo.criar_microbacia(db, **payload.model_dump())


@router.get("", response_model=list[MicrobaciaResponse])
def listar_microbacias(db: Session = Depends(get_db_session)):
    return repo.listar_todas(db)


@router.get("/{microbacia_id}", response_model=MicrobaciaResponse)
def buscar_microbacia(microbacia_id: int, db: Session = Depends(get_db_session)):
    microbacia = repo.buscar_por_id(db, microbacia_id)
    if microbacia is None:
        raise HTTPException(status_code=404, detail="Microbacia nao encontrada")
    return microbacia
