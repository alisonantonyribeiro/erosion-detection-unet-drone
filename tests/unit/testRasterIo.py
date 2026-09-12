import numpy as np
import rasterio
from rasterio.transform import from_origin

from erosion.core.geo.rasterIo import ler_raster, salvar_raster


def test_salvar_e_ler_preserva_crs_e_transform(tmp_path):
    caminho = tmp_path / "raster.tif"
    dados = np.random.randint(0, 255, (4, 10, 10), dtype=np.uint8)
    transform = from_origin(500000, 7000000, 0.5, 0.5)
    profile = dict(
        driver="GTiff", height=10, width=10, count=4, dtype="uint8",
        crs="EPSG:31982", transform=transform,
    )

    salvar_raster(dados, profile, caminho)
    dados_lidos, profile_lido = ler_raster(caminho)

    assert str(profile_lido["crs"]) == "EPSG:31982"
    assert profile_lido["transform"] == transform
    np.testing.assert_array_equal(dados_lidos, dados)


def test_salvar_raster_aceita_array_2d(tmp_path):
    caminho = tmp_path / "banda_unica.tif"
    dados_2d = np.zeros((5, 5), dtype=np.uint8)
    profile = dict(
        driver="GTiff", height=5, width=5, count=1, dtype="uint8",
        crs="EPSG:31982", transform=from_origin(0, 0, 1, 1),
    )

    salvar_raster(dados_2d, profile, caminho)

    with rasterio.open(caminho) as src:
        assert src.count == 1
        assert src.read().shape == (1, 5, 5)
