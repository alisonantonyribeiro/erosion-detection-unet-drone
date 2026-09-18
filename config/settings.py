# config/settings.py
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict



PIPELINE_YAML_PATH = Path(__file__).parent / "pipeline.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: Path
    models_dir: Path
    database_url: str = "sqlite:///./erosion.db"
    redis_url: str = "redis://localhost:6379/0"


class ClasseConfig(BaseModel):
    id: int
    nome: str
    valor_c_rusle: float


class TrainingConfig(BaseModel):
    epochs: int
    batch_size: int


class PipelineConfig(BaseModel):
    tile_size: int
    stride: int
    num_bands: int
    num_classes: int
    normalize_percentiles: tuple[int, int]
    index_order: list[str]
    classes: list[ClasseConfig]
    class_weights: dict[int, float]
    training: TrainingConfig

@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_pipeline_config() -> PipelineConfig:
    with open(PIPELINE_YAML_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return PipelineConfig(**raw)