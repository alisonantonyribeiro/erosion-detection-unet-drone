import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

import rasterio
from rasterio.errors import RasterioIOError

from config.settings import get_pipeline_config
from erosion.storage.fileStore import caminho_upload

EXTENSOES_ACEITAS = {".tif", ".tiff"}
BANDAS_MINIMAS = 4  # R, G, B, NIR -- ordem esperada por analiseService


class ImagemInvalidaError(Exception):
    "Arquivo enviado nao serve como entrada do pipeline"


def salvar_upload(arquivo: BinaryIO, nome_original: str) -> dict:
    """Grava o GeoTIFF enviado em data/uploads e valida se o pipeline consegue usa-lo.

    Valida aqui, no upload, porque o erro de imagem errada (ex.: RGB sem NIR)
    so apareceria minutos depois, dentro da task do worker.
    """
    extensao = Path(nome_original).suffix.lower()
    if extensao not in EXTENSOES_ACEITAS:
        raise ImagemInvalidaError(f"Extensao {extensao or '(nenhuma)'} nao aceita. Envie um GeoTIFF (.tif/.tiff)")

    destino = caminho_upload(f"{uuid.uuid4().hex}{extensao}")
    with open(destino, "wb") as saida:
        shutil.copyfileobj(arquivo, saida)

    try:
        metadados = _validar_geotiff(destino)
    except ImagemInvalidaError:
        destino.unlink(missing_ok=True)
        raise

    # as_posix: com "\" do Windows o caminho quebra o JSON quando o cliente
    # o cola no corpo do POST /analises (ex.: "C:\Users" vira escape invalido)
    return {"caminho_imagem": destino.as_posix(), "nome_original": nome_original, **metadados}


def _validar_geotiff(caminho: Path) -> dict:
    tile_size = get_pipeline_config().tile_size
    try:
        with rasterio.open(caminho) as src:
            bandas, largura, altura, crs = src.count, src.width, src.height, src.crs
    except RasterioIOError as erro:
        raise ImagemInvalidaError("Arquivo nao e um GeoTIFF legivel") from erro

    if bandas < BANDAS_MINIMAS:
        raise ImagemInvalidaError(
            f"Imagem tem {bandas} banda(s); o modelo precisa de {BANDAS_MINIMAS} (R, G, B, NIR)"
        )
    if largura < tile_size or altura < tile_size:
        raise ImagemInvalidaError(f"Imagem {largura}x{altura} menor que o tile de {tile_size}x{tile_size}")

    return {"bandas": bandas, "largura": largura, "altura": altura, "crs": str(crs) if crs else None}
