import pytest

from config.settings import get_pipeline_config
from erosion.core.contracts import ContractError, validar_ordem_indices


def test_ordem_correta_nao_levanta_erro():
    ordem_oficial = get_pipeline_config().index_order
    validar_ordem_indices(ordem_oficial)


def test_ordem_invertida_levanta_contract_error():
    ordem_oficial = get_pipeline_config().index_order
    ordem_invertida = list(reversed(ordem_oficial))

    with pytest.raises(ContractError):
        validar_ordem_indices(ordem_invertida)


def test_ordem_com_indice_faltando_levanta_contract_error():
    ordem_oficial = get_pipeline_config().index_order

    with pytest.raises(ContractError):
        validar_ordem_indices(ordem_oficial[:-1])
