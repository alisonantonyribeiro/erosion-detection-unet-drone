from pathlib import Path
from typing import Iterator

import numpy as np
import rasterio
from rasterio.windows import Window

from config.settings import get_pipeline_config


def gerar_tiles(
    caminho_imagem: str | Path,
    tile_size: int | None = None,
    stride: int | None = None,
) -> Iterator[tuple[np.ndarray, dict]]:
    """Corta uma imagem em tiles com sobreposicao, igual ao apendice A (cut_tiles)."""
    cfg = get_pipeline_config()
    tile_size = tile_size or cfg.tile_size
    stride = stride or cfg.stride

    with rasterio.open(caminho_imagem) as src:
        for y in range(0, src.height - tile_size + 1, stride):
            for x in range(0, src.width - tile_size + 1, stride):
                window = Window(x, y, tile_size, tile_size)

                tile_profile = src.profile.copy()
                tile_profile.update(
                    height=window.height,
                    width=window.width,
                    transform=src.window_transform(window),
                )

                tile_data = src.read(window=window)
                if tile_data.ndim == 4 and tile_data.shape[0] == 1:
                    tile_data = tile_data.squeeze(axis=0)

                yield tile_data, tile_profile
