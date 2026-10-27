from sqlalchemy.orm import Session

from erosion.repositories.models import Microbacia


def criar_microbacia(db: Session, **campos) -> Microbacia:
    microbacia = Microbacia(**campos)
    db.add(microbacia)
    db.commit()
    db.refresh(microbacia)
    return microbacia


def buscar_por_id(db: Session, microbacia_id: int) -> Microbacia | None:
    return db.get(Microbacia, microbacia_id)


def listar_todas(db: Session) -> list[Microbacia]:
    return db.query(Microbacia).order_by(Microbacia.nome).all()
