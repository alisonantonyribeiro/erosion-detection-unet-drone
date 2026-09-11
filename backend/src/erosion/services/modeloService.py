from sqlalchemy.orm import Session

from erosion.core.model.predict import carregar_modelo
from erosion.repositories.models import Modelo
from erosion.storage.fileStore import caminho_modelo as resolver_caminho_modelo


def registrar_modelo(db: Session, versao: str, nome_arquivo: str) -> Modelo:
    modelo = Modelo(versao=versao, caminho_arquivo=str(resolver_caminho_modelo(nome_arquivo)))
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return modelo


def buscar_por_versao(db: Session, versao: str) -> Modelo | None:
    return db.query(Modelo).filter(Modelo.versao == versao).one_or_none()


def listar_modelos(db: Session) -> list[Modelo]:
    return db.query(Modelo).order_by(Modelo.criado_em.desc()).all()


def carregar_modelo_keras(modelo: Modelo):
    return carregar_modelo(modelo.caminho_arquivo)
