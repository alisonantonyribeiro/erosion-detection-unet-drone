from sqlalchemy.orm import Session

from erosion.core.geo.mosaic import gerar_mosaico_cog
from erosion.core.geo.rasterIo import salvar_raster
from erosion.core.model.predict import pre_processar_stack, prever_tile
from erosion.core.preprocessing.indices import calcular_todos_indices, empilhar_na_ordem_oficial
from erosion.core.preprocessing.tiling import gerar_tiles
from erosion.repositories import analiseRepository as repo
from erosion.repositories.models import Modelo, StatusAnalise
from erosion.services import modeloService, resultadoService
from erosion.storage.fileStore import caminho_analise


def rodar_analise(db: Session, analise_id: int, caminho_imagem: str, modelo: Modelo) -> dict:
    """Orquestra o caso de uso completo: tiles -> indices -> predicao -> mosaico -> persistencia.

    Pensado para rodar dentro de uma task assincrona (workers/tasks.py),
    ja que uma imagem completa gera muitos tiles e pode demorar.
    """
    repo.atualizar_status(db, analise_id, StatusAnalise.PROCESSANDO)

    try:
        modelo_keras = modeloService.carregar_modelo_keras(modelo)
        caminhos_predicoes = []

        for i, (tile_data, tile_profile) in enumerate(gerar_tiles(caminho_imagem)):
            R, G, B, NIR = tile_data[0], tile_data[1], tile_data[2], tile_data[3]
            indices = calcular_todos_indices(R, G, B, NIR)
            stack = empilhar_na_ordem_oficial(indices)

            mapa_predicao = prever_tile(modelo_keras, pre_processar_stack(stack))

            profile_predicao = tile_profile.copy()
            profile_predicao.update(count=1, dtype="uint8", compress="lzw")
            caminho_predicao = caminho_analise(analise_id, "predicoes", f"tile_{i:05d}.tif")
            salvar_raster(mapa_predicao, profile_predicao, caminho_predicao)
            caminhos_predicoes.append(str(caminho_predicao))

        caminho_mosaico = caminho_analise(analise_id, "mosaico_final.tif")
        gerar_mosaico_cog(caminhos_predicoes, caminho_mosaico)

        repo.salvar_resultado(db, analise_id, str(caminho_mosaico))
        repo.atualizar_status(db, analise_id, StatusAnalise.CONCLUIDA)

        return resultadoService.calcular_areas_a_partir_do_mosaico(caminho_mosaico)

    except Exception as erro:
        repo.atualizar_status(db, analise_id, StatusAnalise.ERRO, mensagem_erro=str(erro))
        raise
