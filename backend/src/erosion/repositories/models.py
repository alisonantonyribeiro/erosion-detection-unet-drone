import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from erosion.repositories.db import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class StatusAnalise(str, enum.Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    ERRO = "erro"


class Microbacia(Base):
    __tablename__ = "microbacias"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    area_ha = Column(Float)

    analises = relationship("Analise", back_populates="microbacia")


class Modelo(Base):
    __tablename__ = "modelos"

    id = Column(Integer, primary_key=True)
    versao = Column(String, nullable=False, unique=True)
    caminho_arquivo = Column(String, nullable=False)
    criado_em = Column(DateTime(timezone=True), default=_agora)

    analises = relationship("Analise", back_populates="modelo")


class Analise(Base):
    __tablename__ = "analises"

    id = Column(Integer, primary_key=True)
    microbacia_id = Column(Integer, ForeignKey("microbacias.id"), nullable=False)
    modelo_id = Column(Integer, ForeignKey("modelos.id"), nullable=False)
    status = Column(Enum(StatusAnalise), default=StatusAnalise.PENDENTE, nullable=False)
    caminho_mosaico_resultado = Column(String, nullable=True)
    criado_em = Column(DateTime(timezone=True), default=_agora)
    concluido_em = Column(DateTime(timezone=True), nullable=True)
    mensagem_erro = Column(String, nullable=True)

    microbacia = relationship("Microbacia", back_populates="analises")
    modelo = relationship("Modelo", back_populates="analises")
