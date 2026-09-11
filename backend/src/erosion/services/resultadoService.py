from pathlib import Path

import numpy as np
import rasterio

from config.settings import get_pipeline_config


def calcular_areas_por_classe(mapa_classes: np.ndarray, transform) -> dict[str, dict]:
    """Hectares e percentual por classe, usando os nomes/ids do pipeline.yaml."""
    pixel_area_m2 = abs(transform.a * transform.e)
    total_pixels = mapa_classes.size

    resultado = {}
    for classe in get_pipeline_config().classes:
        n_pixels = int(np.count_nonzero(mapa_classes == classe.id))
        resultado[classe.nome] = {
            "hectares": round(n_pixels * pixel_area_m2 / 10_000, 4),
            "percentual": round(100 * n_pixels / total_pixels, 2) if total_pixels else 0.0,
        }
    return resultado


def calcular_areas_a_partir_do_mosaico(caminho_mosaico: str | Path) -> dict[str, dict]:
    with rasterio.open(caminho_mosaico) as src:
        mapa = src.read(1)
        transform = src.transform
    return calcular_areas_por_classe(mapa, transform)
