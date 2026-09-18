from pathlib import Path

from config.settings import get_settings


def caminho_analise(analise_id: int, *partes: str) -> Path:
    """Resolve um caminho dentro da pasta de dados da analise (cria os diretorios pais).

    Filesystem local no MVP; trocar a implementacao por S3/MinIO depois
    e transparente para quem chama, ja que o resto do backend so
    conhece esta funcao, nao o disco diretamente.
    """
    caminho = get_settings().data_dir / "analises" / str(analise_id) / Path(*partes)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho


def caminho_modelo(nome_arquivo: str) -> Path:
    return get_settings().models_dir / nome_arquivo
