from pathlib import Path

import numpy as np
import rasterio


def ler_raster(caminho: str | Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(caminho) as src:
        return src.read(), src.profile.copy()


def salvar_raster(dados: np.ndarray, profile: dict, caminho: str | Path) -> None:
    if dados.ndim == 2:
        dados = np.expand_dims(dados, axis=0)

    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(caminho, "w", **profile) as dst:
        dst.write(dados)
