import os
import glob
import numpy as np
import rasterio
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# --- CONFIGURAÇÃO ---
STACKED_IMAGES_DIR = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\train_images_stacked"
MASKS_DIR = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\train_masks"
MODEL_SAVE_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\modelo_erosao_unet_V9_calibrated.h5"

# --- PARÂMETROS ---
TILE_SIZE = 512
NUM_BANDS = 6
NUM_CLASSES = 5

# --- DEFINIÇÃO DE PESOS (A MUDANÇA MÁGICA) ---
# Aqui dizemos para a IA o quão importante é cada classe.
# 0: Agricultura (Fundo) - Peso 1 (Normal)
# 1: Erosão - Peso 10 (CRÍTICO! A IA vai focar muito aqui)
# 2: Rio / Água - Peso 5 (Importante para diferenciar de estrada)
# 3: Vegetação Densa - Peso 2 (Para recuperar as árvores perdidas)
# 4: Construção - Peso 2 (Para ajudar a definir melhor estradas)
# CLASS_WEIGHTS = {0: 1.0, 1: 10.0, 2: 5.0, 3: 2.0, 4: 2.0}
#-----------------------------------------------------------------------------
# --- NOVOS PESOS PARA O V7 (CALIBRAGEM FINA) ---
# 0: Agricultura - SUBIR para 2.0 (Para proteger a soja da 'água')
# 1: Erosão - BAIXAR para 7.0 (Para reduzir ruído na borda da estrada)
# 2: Água - BAIXAR para 3.0 (Para parar de invadir a estrada)
# 3: Vegetação - MANTER 2.0 (Time que está ganhando não se mexe)
# 4: Construção - SUBIR para 5.0 (Prioridade para consertar a estrada)
#CLASS_WEIGHTS = {0: 2.0, 1: 7.0, 2: 3.0, 3: 2.0, 4: 5.0}
#-----------------------------------------------------------------------------
# --- PESOS DO V8 (RESGATE DAS ÁRVORES E PROTEÇÃO DA SOJA) ---
# 0: Agricultura - SUBIR para 3.0 (Para brigar de igual para igual com a água)
# 1: Erosão - MANTER 6.0 (Ainda é prioridade, mas equilibrado)
# 2: Água - BAIXAR para 1.0 (Peso mínimo. Só marque água se tiver CERTEZA ABSOLUTA)
# 3: Vegetação - SUBIR para 4.0 (Para recuperar a densidade das árvores perdidas)
# 4: Construção - MANTER 5.0 (Para garantir que a estrada continue correta)
#CLASS_WEIGHTS = {0: 3.0, 1: 6.0, 2: 1.0, 3: 4.0, 4: 5.0}
#-----------------------------------------------------------------------------
# --- PESOS DO V9 (O MODELO FINAL?) ---
# Aumentamos a Vegetação para 6.0 para recuperar a densidade do V6.
# Mantemos os outros pesos que garantiram a limpeza da soja e da estrada.
CLASS_WEIGHTS = {0: 3.0, 1: 6.0, 2: 1.0, 3: 6.0, 4: 5.0}  # V9 — MODELO FINAL
#-----------------------------------------------------------------------------
# --- PESOS DO V10 (ESCUDO DA SOJA E PRIORIDADE MÁXIMA NA EROSÃO) ---
# 0: Agricultura - SUBIR para 6.0 (Para esmagar a confusão com a água)
# 1: Erosão - SUBIR para 7.0 (Prioridade máxima absoluta)
# 2: Água - MANTER 1.0 (Peso mínimo)
# 3: Vegetação - MANTER 6.0 (Funcionou bem no V9)
# 4: Construção - BAIXAR para 4.0 (Para parar de confundir com erosão)

#CLASS_WEIGHTS = {0: 6.0, 1: 7.0, 2: 1.0, 3: 6.0, 4: 4.0}  # V10 (não utilizado)


# --- FUNÇÃO DE CARREGAMENTO (IGUAL) ---
def load_data(image_dir, mask_dir):
    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.vrt")))
    mask_paths = sorted(glob.glob(os.path.join(mask_dir, "*.tif")))
    images = []
    masks = []
    print(f"Carregando {len(image_paths)} pares...")
    for img_path, mask_path in tqdm(zip(image_paths, mask_paths), total=len(image_paths)):
        with rasterio.open(img_path) as src:
            if src.count != 6: continue
            img = src.read().transpose((1, 2, 0))
            for i in range(img.shape[2]):
                band = img[:, :, i]
                min_val, max_val = np.percentile(band, 2), np.percentile(band, 98)
                if max_val > min_val:
                    img[:, :, i] = np.clip((band - min_val) / (max_val - min_val), 0, 1)
                else:
                    img[:, :, i] = 0
            img = tf.image.resize(img, [TILE_SIZE, TILE_SIZE])
            images.append(img)
        with rasterio.open(mask_path) as src:
            mask = src.read(1)
            mask = np.expand_dims(mask, axis=-1)
            mask = tf.image.resize(mask, [TILE_SIZE, TILE_SIZE], method='nearest')
            mask = tf.squeeze(mask, axis=-1)
            masks.append(mask)
    return np.array(images, dtype=np.float32), np.array(masks, dtype=np.uint8)

# --- AUGMENTATION (IGUAL - MANTENHA, É BOM) ---
def augment_data(images, masks):
    aug_images = []
    aug_masks = []
    print("Aplicando Augmentation...")
    for x, y in tqdm(zip(images, masks), total=len(images)):
        aug_images.append(x); aug_masks.append(y)
        aug_images.append(tf.image.rot90(x, k=1)); aug_masks.append(tf.image.rot90(y, k=1))
        aug_images.append(tf.image.rot90(x, k=2)); aug_masks.append(tf.image.rot90(y, k=2))
        aug_images.append(tf.image.flip_left_right(x)); aug_masks.append(tf.image.flip_left_right(y))
        # Reduzi um pouco o augmentation para não demorar tanto, tirando 270 graus e flip vertical
        # Se quiser manter total, adicione as linhas de volta.
    return np.array(aug_images), np.array(aug_masks)

# --- MODELO U-NET (VERSÃO CORRIGIDA) ---
def unet_model(input_size=(TILE_SIZE, TILE_SIZE, NUM_BANDS), num_classes=NUM_CLASSES):
    inputs = tf.keras.layers.Input(input_size)
    
    # Encoder
    c1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(inputs)
    c1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(c1)
    p1 = tf.keras.layers.MaxPooling2D((2, 2))(c1)
    
    c2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(p1)
    c2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(c2)
    p2 = tf.keras.layers.MaxPooling2D((2, 2))(c2)
    
    # Bottleneck
    c_mid = tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same')(p2)
    
    # Decoder
    # Bloco 1 de expansão (conecta com c2)
    u2 = tf.keras.layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(c_mid)
    u2 = tf.keras.layers.concatenate([u2, c2])
    c_up2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u2)
    
    # Bloco 2 de expansão (conecta com c1)
    # A CORREÇÃO ESTÁ AQUI EMBAIXO: (c_up2) em vez de (c_up1)
    u1 = tf.keras.layers.Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(c_up2)
    u1 = tf.keras.layers.concatenate([u1, c1])
    c_up1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(u1)
    
    outputs = tf.keras.layers.Conv2D(num_classes, (1, 1), activation='softmax')(c_up1)
    
    model = tf.keras.Model(inputs=[inputs], outputs=[outputs])
    return model

# --- O TRUQUE: MAPEAR PESOS PARA PIXELS ---
def add_sample_weights(image, mask):
    # Cria um mapa de pesos com o mesmo tamanho da máscara
    class_weights = tf.constant([CLASS_WEIGHTS[i] for i in range(NUM_CLASSES)])
    class_weights = class_weights / tf.reduce_sum(class_weights) # Normaliza
    
    # Cria uma matriz de pesos baseada na máscara
    sample_weights = tf.gather(class_weights, indices=tf.cast(mask, tf.int32))
    return image, mask, sample_weights

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    images, masks = load_data(STACKED_IMAGES_DIR, MASKS_DIR)
    masks = np.expand_dims(masks, axis=-1)
    
    # Aplica augmentation
    images, masks = augment_data(images, masks)
    
    X_train, X_val, y_train, y_val = train_test_split(images, masks, test_size=0.2, random_state=42)
    
    # Prepara os dados com pesos (Usando tf.data para eficiência)
    train_dataset = tf.data.Dataset.from_tensor_slices((X_train, y_train))
    train_dataset = train_dataset.map(add_sample_weights).batch(4).prefetch(tf.data.AUTOTUNE)
    
    val_dataset = tf.data.Dataset.from_tensor_slices((X_val, y_val))
    val_dataset = val_dataset.map(add_sample_weights).batch(4).prefetch(tf.data.AUTOTUNE)

    model = unet_model()
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    print("\n--- TREINANDO COM PESOS DE CLASSE (V9) ---")
    print(f"Pesos definidos: {CLASS_WEIGHTS}")
    
    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=50
    )
    
    model.save(MODEL_SAVE_PATH)
    print("Modelo V9 salvo!")