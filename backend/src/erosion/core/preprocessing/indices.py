import numpy as np

from config.settings import get_pipeline_config

EPS = 1e-6


def calcular_bi(R, G, B, NIR, SWIR):
    return np.sqrt((R ** 2 + G ** 2) / 2)


def calcular_bi2(R, G, B, NIR, SWIR):
    return np.sqrt((R ** 2 + G ** 2 + B ** 2) / 3)


def calcular_bsi(R, G, B, NIR, SWIR):
    return ((SWIR + R) - (NIR + B)) / ((SWIR + R) + (NIR + B) + EPS)


def calcular_satvi(R, G, B, NIR, SWIR, L=0.5):
    return ((SWIR - R) / (SWIR + R + L) + EPS) * (1 + L)


def calcular_ndvi(R, G, B, NIR, SWIR):
    return (NIR - R) / (NIR + R + EPS)


def calcular_ndmi(R, G, B, NIR, SWIR):
    return (SWIR - NIR) / (SWIR + NIR + EPS)


INDICE_FUNCOES = {
    "bi": calcular_bi,
    "bi2": calcular_bi2,
    "bsi": calcular_bsi,
    "satvi": calcular_satvi,
    "ndvi": calcular_ndvi,
    "ndmi": calcular_ndmi,
}


def calcular_todos_indices(R: np.ndarray, G: np.ndarray, B: np.ndarray, NIR: np.ndarray) -> dict[str, np.ndarray]:
    R, G, B, NIR = (banda.astype(np.float32) for banda in (R, G, B, NIR))
    SWIR = (R + G + B) / 3
    return {nome: funcao(R, G, B, NIR, SWIR) for nome, funcao in INDICE_FUNCOES.items()}


def empilhar_na_ordem_oficial(indices: dict[str, np.ndarray]) -> np.ndarray:
    ordem = get_pipeline_config().index_order
    return np.stack([indices[nome] for nome in ordem], axis=-1)
