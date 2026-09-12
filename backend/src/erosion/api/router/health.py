from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def verificar_saude() -> dict:
    status = {"api": "ok"}

    try:
        import rasterio  # noqa: F401

        status["gdal"] = "ok"
    except ImportError:
        status["gdal"] = "indisponivel"

    try:
        import tensorflow as tf

        status["gpu"] = "disponivel" if tf.config.list_physical_devices("GPU") else "cpu_apenas"
    except ImportError:
        status["gpu"] = "tensorflow_indisponivel"

    return status
