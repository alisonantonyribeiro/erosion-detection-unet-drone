import numpy as np

from config.settings import get_pipeline_config


def normalizar_percentil(banda: np.ndarray, p_min: int, p_max: int) -> np.ndarray:
    min_val = np.percentile(banda, p_min)
    max_val = np.percentile(banda, p_max)

    if max_val > min_val:
        return np.clip((banda - min_val) / (max_val - min_val), 0, 1)
    return np.zeros_like(banda, dtype=np.float32)


def normalizar_banda(banda: np.ndarray) -> np.ndarray:
    p_min, p_max = get_pipeline_config().normalize_percentiles
    return normalizar_percentil(banda, p_min, p_max)
