from datetime import datetime, timezone

from sqlalchemy.orm import Session

from erosion.repositories.models import Analise, StatusAnalise


def criar_analise(db: Session, microbacia_id: int, modelo_id: int) -> Analise:
    analise = Analise(microbacia_id=microbacia_id, modelo_id=modelo_id, status=StatusAnalise.PENDENTE)
    db.add(analise)
    db.commit()
    db.refresh(analise)
    return analise


def buscar_por_id(db: Session, analise_id: int) -> Analise | None:
    return db.get(Analise, analise_id)


def listar_todas(db: Session) -> list[Analise]:
    return db.query(Analise).order_by(Analise.criado_em.desc()).all()


def atualizar_status(
    db: Session, analise_id: int, status: StatusAnalise, mensagem_erro: str | None = None
) -> Analise | None:
    analise = buscar_por_id(db, analise_id)
    if analise is None:
        return None

    analise.status = status
    if mensagem_erro:
        analise.mensagem_erro = mensagem_erro
    if status == StatusAnalise.CONCLUIDA:
        analise.concluido_em = datetime.now(timezone.utc)

    db.commit()
    db.refresh(analise)
    return analise


def salvar_resultado(db: Session, analise_id: int, caminho_mosaico: str) -> Analise | None:
    analise = buscar_por_id(db, analise_id)
    if analise is None:
        return None

    analise.caminho_mosaico_resultado = caminho_mosaico
    db.commit()
    db.refresh(analise)
    return analise
