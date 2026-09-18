from pathlib import Path

import rasterio
from rasterio.merge import merge


def gerar_mosaico_cog(caminhos_tiles: list[str | Path], caminho_saida: str | Path) -> None:
    """Mosaico final em Cloud Optimized GeoTIFF, substituindo o par
    gdalbuildvrt + gdal_translate -of COG dos apendices A e G.

    Usa rasterio.merge (biblioteca) em vez de chamar o CLI do GDAL via
    subprocess/shell, evitando depender de gdalbuildvrt/gdal_translate
    estarem instalados e no PATH.
    """
    fontes = [rasterio.open(caminho) for caminho in caminhos_tiles]
    try:
        mosaico, transform = merge(fontes)

        profile = fontes[0].profile.copy()
        profile.update(
            driver="COG",
            height=mosaico.shape[1],
            width=mosaico.shape[2],
            transform=transform,
            compress="lzw",
        )

        Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(caminho_saida, "w", **profile) as dst:
            dst.write(mosaico)
    finally:
        for fonte in fontes:
            fonte.close()
