import glob
import os

import numpy as np
import rasterio
import tensorflow as tf
from sklearn.model_selection import train_test_split

from config.settings import get_pipeline_config, get_settings
from erosion.core.model.unet import construir_unet
from erosion.core.preprocessing.normalize import normalizar_banda


def carregar_dados(dir_imagens: str, dir_mascaras: str) -> tuple[np.ndarray, np.ndarray]:
    cfg = get_pipeline_config()
    caminhos_imagens = sorted(glob.glob(os.path.join(dir_imagens, "*.vrt")))
    caminhos_mascaras = sorted(glob.glob(os.path.join(dir_mascaras, "*.tif")))

    imagens, mascaras = [], []
    for caminho_img, caminho_mask in zip(caminhos_imagens, caminhos_mascaras):
        with rasterio.open(caminho_img) as src:
            if src.count != cfg.num_bands:
                continue
            img = src.read().transpose((1, 2, 0)).astype(np.float32)
            for i in range(img.shape[2]):
                img[:, :, i] = normalizar_banda(img[:, :, i])
            img = tf.image.resize(img, [cfg.tile_size, cfg.tile_size])
            imagens.append(img)

        with rasterio.open(caminho_mask) as src:
            mask = np.expand_dims(src.read(1), axis=-1)
            mask = tf.image.resize(mask, [cfg.tile_size, cfg.tile_size], method="nearest")
            mascaras.append(tf.squeeze(mask, axis=-1))

    return np.array(imagens, dtype=np.float32), np.array(mascaras, dtype=np.uint8)


def aumentar_dados(imagens: np.ndarray, mascaras: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    imagens_aug, mascaras_aug = [], []
    for x, y in zip(imagens, mascaras):
        imagens_aug += [x, tf.image.rot90(x, k=1), tf.image.rot90(x, k=2), tf.image.flip_left_right(x)]
        mascaras_aug += [y, tf.image.rot90(y, k=1), tf.image.rot90(y, k=2), tf.image.flip_left_right(y)]
    return np.array(imagens_aug), np.array(mascaras_aug)


def pesos_por_amostra(imagem, mascara):
    cfg = get_pipeline_config()
    pesos_classe = tf.constant([cfg.class_weights[i] for i in range(cfg.num_classes)])
    pesos_classe = pesos_classe / tf.reduce_sum(pesos_classe)
    pesos_amostra = tf.gather(pesos_classe, indices=tf.cast(mascara, tf.int32))
    return imagem, mascara, pesos_amostra


def treinar(dir_imagens: str, dir_mascaras: str, nome_modelo: str = "modelo_erosao_unet.h5") -> str:
    cfg = get_pipeline_config()
    settings = get_settings()

    imagens, mascaras = carregar_dados(dir_imagens, dir_mascaras)
    mascaras = np.expand_dims(mascaras, axis=-1)
    imagens, mascaras = aumentar_dados(imagens, mascaras)

    X_train, X_val, y_train, y_val = train_test_split(imagens, mascaras, test_size=0.2, random_state=42)

    train_ds = (
        tf.data.Dataset.from_tensor_slices((X_train, y_train))
        .map(pesos_por_amostra)
        .batch(cfg.training.batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )
    val_ds = (
        tf.data.Dataset.from_tensor_slices((X_val, y_val))
        .map(pesos_por_amostra)
        .batch(cfg.training.batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )

    modelo = construir_unet()
    modelo.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    modelo.fit(train_ds, validation_data=val_ds, epochs=cfg.training.epochs)

    settings.models_dir.mkdir(parents=True, exist_ok=True)
    caminho_saida = settings.models_dir / nome_modelo
    modelo.save(caminho_saida)
    return str(caminho_saida)
