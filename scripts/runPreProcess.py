import argparse
from pathlib import Path

from erosion.core.geo.rasterIo import salvar_raster
from erosion.core.preprocessing.indices import calcular_todos_indices
from erosion.core.preprocessing.tiling import gerar_tiles


def processar_imagem(caminho_imagem: str, dir_saida_tiles: str, dir_saida_indices: str) -> None:
    prefixo = Path(caminho_imagem).stem.replace(" ", "_").replace("-", "_")

    for i, (tile_data, tile_profile) in enumerate(gerar_tiles(caminho_imagem)):
        nome_tile = f"{prefixo}_tile_{i:05d}.tif"

        salvar_raster(tile_data, tile_profile, Path(dir_saida_tiles) / nome_tile)

        if tile_data.shape[0] < 4:
            continue

        R, G, B, NIR = tile_data[0], tile_data[1], tile_data[2], tile_data[3]
        indices = calcular_todos_indices(R, G, B, NIR)

        profile_indice = tile_profile.copy()
        profile_indice.update(dtype="float32", count=1, compress="lzw")
        for nome_indice, dados_indice in indices.items():
            caminho_indice = Path(dir_saida_indices) / nome_indice / nome_tile
            salvar_raster(dados_indice, profile_indice, caminho_indice)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Corta imagens em tiles e calcula indices espectrais (substitui apendice A)."
    )
    parser.add_argument("imagens", nargs="+", help="Caminhos das imagens de entrada (.tif)")
    parser.add_argument("--dir-tiles", required=True, help="Diretorio de saida dos tiles")
    parser.add_argument("--dir-indices", required=True, help="Diretorio de saida dos indices")
    args = parser.parse_args()

    for caminho_imagem in args.imagens:
        print(f"Processando {caminho_imagem}...")
        processar_imagem(caminho_imagem, args.dir_tiles, args.dir_indices)

    print("Concluido.")


if __name__ == "__main__":
    main()
