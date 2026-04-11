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
MODEL_SAVE_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\modelo_erosao_unet_V5_aug.h5" # Note o V5_aug

# --- PARÂMETROS ---
TILE_SIZE = 512
NUM_BANDS = 6
NUM_CLASSES = 5

# --- FUNÇÃO DE CARREGAMENTO (A MESMA DO ANTERIOR) ---
def load_data(image_dir, mask_dir):
    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.vrt")))
    mask_paths = sorted(glob.glob(os.path.join(mask_dir, "*.tif")))
    
    images = []
    masks = []
    
    print(f"Carregando {len(image_paths)} pares de imagem/máscara...")
    for img_path, mask_path in tqdm(zip(image_paths, mask_paths), total=len(image_paths)):
        with rasterio.open(img_path) as src:
            if src.count != 6:
                continue # Pula arquivos com erro
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

# --- NOVA FUNÇÃO: DATA AUGMENTATION ---
def augment_data(images, masks):
    """
    Multiplica os dados aplicando rotações e espelhamentos.
    Transforma 1 imagem em 6 (Original + 3 Rotações + 2 Flips).
    """
    aug_images = []
    aug_masks = []
    
    print("Aplicando Data Augmentation (Multiplicando dados por 6)...")
    
    for x, y in tqdm(zip(images, masks), total=len(images)):
        # 1. Original
        aug_images.append(x)
        aug_masks.append(y)
        
        # 2. Rotação 90 graus
        aug_images.append(tf.image.rot90(x, k=1))
        aug_masks.append(tf.image.rot90(y, k=1))
        
        # 3. Rotação 180 graus
        aug_images.append(tf.image.rot90(x, k=2))
        aug_masks.append(tf.image.rot90(y, k=2))
        
        # 4. Rotação 270 graus
        aug_images.append(tf.image.rot90(x, k=3))
        aug_masks.append(tf.image.rot90(y, k=3))
        
        # 5. Flip Horizontal (Espelhamento)
        aug_images.append(tf.image.flip_left_right(x))
        aug_masks.append(tf.image.flip_left_right(y))
        
        # 6. Flip Vertical
        aug_images.append(tf.image.flip_up_down(x))
        aug_masks.append(tf.image.flip_up_down(y))
        
    return np.array(aug_images), np.array(aug_masks)

# --- MODELO U-NET (MESMO DO ANTERIOR) ---
def unet_model(input_size=(TILE_SIZE, TILE_SIZE, NUM_BANDS), num_classes=NUM_CLASSES):
    inputs = tf.keras.layers.Input(input_size)
    c1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(inputs)
    c1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(c1)
    p1 = tf.keras.layers.MaxPooling2D((2, 2))(c1)
    c2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(p1)
    c2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(c2)
    p2 = tf.keras.layers.MaxPooling2D((2, 2))(c2)
    c_mid = tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same')(p2)
    u2 = tf.keras.layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(c_mid)
    u2 = tf.keras.layers.concatenate([u2, c2])
    c_up2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u2)
    u1 = tf.keras.layers.Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(c_up2)
    u1 = tf.keras.layers.concatenate([u1, c1])
    c_up1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(u1)
    outputs = tf.keras.layers.Conv2D(num_classes, (1, 1), activation='softmax')(c_up1)
    model = tf.keras.Model(inputs=[inputs], outputs=[outputs])
    return model

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    # 1. Carregar dados originais
    images, masks = load_data(STACKED_IMAGES_DIR, MASKS_DIR)
    masks = np.expand_dims(masks, axis=-1)
    print(f"Dados Originais: {len(images)} amostras")
    
    # 2. Aplicar Augmentation (A MÁGICA ACONTECE AQUI)
    images_aug, masks_aug = augment_data(images, masks)
    print(f"Dados Após Augmentation: {len(images_aug)} amostras")
    
    # 3. Dividir treino/validação
    X_train, X_val, y_train, y_val = train_test_split(images_aug, masks_aug, test_size=0.2, random_state=42)
    
    print(f"Treino: {len(X_train)} | Validação: {len(X_val)}")
    
    # 4. Treinar
    model = unet_model()
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=4, 
        epochs=50 
    )
    
    model.save(MODEL_SAVE_PATH)
    print(f"Modelo salvo em: {MODEL_SAVE_PATH}")