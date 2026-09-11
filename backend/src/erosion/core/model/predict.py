from pathlib import Path

import numpy as np
import rasterio
import tensorflow as tf

from erosion.core.contracts import validar_ordem_indices
from erosion.core.geo.rasterIo import salvar_raster
from erosion.core.preprocessing.normalize import normalizar_banda


def carregar_modelo(caminho_modelo: str) -> tf.keras.Model:
    return tf.keras.models.load_model(caminho_modelo)


def pre_processar_stack(stack: np.ndarray) -> np.ndarray:
    """stack: (H, W, num_bands). Normaliza cada banda e adiciona dimensao de lote."""
    stack = stack.astype(np.float32).copy()
    for i in range(stack.shape[-1]):
        stack[:, :, i] = normalizar_banda(stack[:, :, i])
    return np.expand_dims(stack, axis=0)


def prever_tile(modelo: tf.keras.Model, stack_pre_processado: np.ndarray) -> np.ndarray:
    predicao = modelo.predict(stack_pre_processado, verbose=0)
    return np.argmax(predicao[0], axis=-1).astype(np.uint8)


def prever_a_partir_do_vrt(modelo: tf.keras.Model, caminho_vrt: str, caminho_saida: str) -> None:
    """Equivalente ao apendice C: predicao de um unico tile ja empilhado em .vrt."""
    with rasterio.open(caminho_vrt) as src:
        transform, crs = src.transform, src.crs
        dados = src.read().transpose((1, 2, 0))

    mapa_predicao = prever_tile(modelo, pre_processar_stack(dados))

    profile = dict(
        driver="GTiff",
        height=mapa_predicao.shape[0],
        width=mapa_predicao.shape[1],
        count=1,
        dtype=mapa_predicao.dtype,
        crs=crs,
        transform=transform,
        compress="lzw",
    )
    salvar_raster(mapa_predicao, profile, caminho_saida)


def prever_em_lote(
    modelo: tf.keras.Model,
    dir_indices: str,
    nomes_tiles: list[str],
    nomes_indices: list[str],
    dir_saida: str,
) -> list[str]:
    """Equivalente ao apendice F: empilha os indices por nome de pasta e prediz em lote.

    `nomes_indices` e a ordem em que os indices serao empilhados, validada contra
    o pipeline.yaml antes de qualquer predicao -- era exatamente nessa lista
    (INDICES_LIST no apendice F) que a ordem divergia silenciosamente do apendice A.
    """
    validar_ordem_indices(nomes_indices)

    caminhos_saida = []
    for nome_tile in nomes_tiles:
        bandas = []
        ref_profile = None
        for nome_indice in nomes_indices:
            caminho = Path(dir_indices) / nome_indice / nome_tile
            with rasterio.open(caminho) as src:
                if ref_profile is None:
                    ref_profile = src.profile.copy()
                bandas.append(src.read(1).astype(np.float32))

        stack = np.stack(bandas, axis=-1)
        mapa_predicao = prever_tile(modelo, pre_processar_stack(stack))

        ref_profile.update(count=1, dtype="uint8", compress="lzw", driver="GTiff")
        caminho_saida = str(Path(dir_saida) / nome_tile)
        salvar_raster(mapa_predicao, ref_profile, caminho_saida)
        caminhos_saida.append(caminho_saida)

    return caminhos_saida
