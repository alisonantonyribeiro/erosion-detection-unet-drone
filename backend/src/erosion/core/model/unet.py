import tensorflow as tf

from config.settings import get_pipeline_config


def construir_unet(
    input_size: tuple[int, int, int] | None = None,
    num_classes: int | None = None,
) -> tf.keras.Model:
    """Arquitetura U-Net do modelo V9 (apendice E), parametrizada pelo pipeline.yaml."""
    cfg = get_pipeline_config()
    input_size = input_size or (cfg.tile_size, cfg.tile_size, cfg.num_bands)
    num_classes = num_classes or cfg.num_classes

    inputs = tf.keras.layers.Input(input_size)

    c1 = tf.keras.layers.Conv2D(16, (3, 3), activation="relu", padding="same")(inputs)
    c1 = tf.keras.layers.Conv2D(16, (3, 3), activation="relu", padding="same")(c1)
    p1 = tf.keras.layers.MaxPooling2D((2, 2))(c1)

    c2 = tf.keras.layers.Conv2D(32, (3, 3), activation="relu", padding="same")(p1)
    c2 = tf.keras.layers.Conv2D(32, (3, 3), activation="relu", padding="same")(c2)
    p2 = tf.keras.layers.MaxPooling2D((2, 2))(c2)

    c_mid = tf.keras.layers.Conv2D(64, (3, 3), activation="relu", padding="same")(p2)

    u2 = tf.keras.layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding="same")(c_mid)
    u2 = tf.keras.layers.concatenate([u2, c2])
    c_up2 = tf.keras.layers.Conv2D(32, (3, 3), activation="relu", padding="same")(u2)

    u1 = tf.keras.layers.Conv2DTranspose(16, (2, 2), strides=(2, 2), padding="same")(c_up2)
    u1 = tf.keras.layers.concatenate([u1, c1])
    c_up1 = tf.keras.layers.Conv2D(16, (3, 3), activation="relu", padding="same")(u1)

    outputs = tf.keras.layers.Conv2D(num_classes, (1, 1), activation="softmax")(c_up1)

    return tf.keras.Model(inputs=[inputs], outputs=[outputs])
