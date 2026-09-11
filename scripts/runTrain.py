import argparse

from erosion.core.model.train import treinar


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina o modelo U-Net (substitui apendices B/D/E).")
    parser.add_argument("--dir-imagens", required=True, help="Diretorio com os .vrt empilhados de treino")
    parser.add_argument("--dir-mascaras", required=True, help="Diretorio com as mascaras .tif")
    parser.add_argument("--nome-modelo", default="modelo_erosao_unet.h5")
    args = parser.parse_args()

    caminho_salvo = treinar(args.dir_imagens, args.dir_mascaras, args.nome_modelo)
    print(f"Modelo salvo em: {caminho_salvo}")


if __name__ == "__main__":
    main()
