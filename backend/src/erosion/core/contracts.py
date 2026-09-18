from config.settings import get_pipeline_config


class ContractError(Exception):
    "Erro de contrato de dados da Pipeline"


def validar_ordem_indices(indices_recebidos: list[str]) -> None:
    esperado = get_pipeline_config().index_order
    if indices_recebidos != esperado:
        raise ContractError(
            f"Ordem de índices incompatível. Esperado {esperado}, recebido {indices_recebidos}"
        )
