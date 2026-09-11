from erosion.repositories import analiseRepository as repo
from erosion.repositories.db import SessionLocal
from erosion.services import analiseService
from workers.celeryApp import celery_app


@celery_app.task(name="processar_analise")
def processar_analise(analise_id: int, caminho_imagem: str) -> dict:
    """Task assincrona que roda o pipeline completo de uma analise.

    Existe porque a predicao em lote (apendice F) e lenta e nao pode
    travar a requisicao HTTP que a disparou.
    """
    db = SessionLocal()
    try:
        analise = repo.buscar_por_id(db, analise_id)
        if analise is None:
            raise ValueError(f"Analise {analise_id} nao encontrada")
        return analiseService.rodar_analise(db, analise_id, caminho_imagem, analise.modelo)
    finally:
        db.close()
