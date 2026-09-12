import numpy as np

from erosion.core.preprocessing.indices import (
    calcular_bi,
    calcular_ndvi,
    calcular_todos_indices,
    empilhar_na_ordem_oficial,
)


def test_ndvi_vegetacao_densa():
    R = np.array([10.0])
    NIR = np.array([90.0])
    ndvi = calcular_ndvi(R, None, None, NIR, None)
    assert np.isclose(ndvi[0], 0.8, atol=1e-3)


def test_ndvi_zero_quando_r_igual_nir():
    R = np.array([50.0])
    NIR = np.array([50.0])
    ndvi = calcular_ndvi(R, None, None, NIR, None)
    assert np.isclose(ndvi[0], 0.0, atol=1e-6)


def test_bi_solo_exposto_brilhante():
    R = np.array([200.0])
    G = np.array([200.0])
    bi = calcular_bi(R, G, None, None, None)
    assert np.isclose(bi[0], 200.0, atol=1e-6)


def test_calcular_todos_indices_retorna_as_6_chaves():
    R = np.array([[10.0, 20.0]])
    G = np.array([[15.0, 25.0]])
    B = np.array([[5.0, 10.0]])
    NIR = np.array([[50.0, 60.0]])

    indices = calcular_todos_indices(R, G, B, NIR)

    assert set(indices.keys()) == {"bi", "bi2", "bsi", "satvi", "ndvi", "ndmi"}


def test_empilhar_na_ordem_oficial_gera_6_bandas():
    R = np.array([[10.0]])
    G = np.array([[15.0]])
    B = np.array([[5.0]])
    NIR = np.array([[50.0]])

    indices = calcular_todos_indices(R, G, B, NIR)
    stack = empilhar_na_ordem_oficial(indices)

    assert stack.shape[-1] == 6
