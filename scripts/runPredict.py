import argparse

from config.settings import get_pipeline_config
from erosion.core.model.predict import carregar_modelo, prever_a_partir_do_vrt, prever_em_lote


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Roda predicao com o modelo treinado (substitui apendices C, F e G)."
    )
    parser.add_argument("--modelo", required=True, help="Caminho do modelo .h5")
    subparsers = parser.add_subparsers(dest="modo", required=True)

    tile_parser = subparsers.add_parser("tile", help="Prediz um unico tile a partir de um .vrt (apendice C)")
    tile_parser.add_argument("--entrada", required=True)
    tile_parser.add_argument("--saida", required=True)

    lote_parser = subparsers.add_parser("lote", help="Prediz varios tiles a partir de indices empilhados (apendice F)")
    lote_parser.add_argument("--dir-indices", required=True)
    lote_parser.add_argument(
        "--tiles", nargs="+", required=True, help="Nomes dos arquivos de tile (iguais em todas as pastas de indice)"
    )
    lote_parser.add_argument("--dir-saida", required=True)

    args = parser.parse_args()
    modelo = carregar_modelo(args.modelo)

    if args.modo == "tile":
        prever_a_partir_do_vrt(modelo, args.entrada, args.saida)
        print(f"Predicao salva em: {args.saida}")
    else:
        ordem = get_pipeline_config().index_order
        caminhos = prever_em_lote(modelo, args.dir_indices, args.tiles, ordem, args.dir_saida)
        print(f"{len(caminhos)} predicoes salvas em: {args.dir_saida}")


if __name__ == "__main__":
    main()
