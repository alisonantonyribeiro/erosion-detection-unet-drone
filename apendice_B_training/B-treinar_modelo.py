import os
import glob
import numpy as np
import rasterio
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# --- CONFIGURAÇÃO (AJUSTE OS CAMINHOS AQUI) ---
STACKED_IMAGES_DIR = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\train_images_stacked"
MASKS_DIR = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\train_masks"
MODEL_SAVE_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\modelo_erosao_unet_V4.h5"

# --- PARÂMETROS DO MODELO ---
TILE_SIZE = 512
NUM_BANDS = 6  # Número de índices que você empilhou
NUM_CLASSES = 5 # Número de classes que você rotulou (0 a 4)

# --- 1. FUNÇÕES DE CARREGAMENTO DE DADOS (VERSÃO DIAGNÓSTICO) ---
def load_data(image_dir, mask_dir):
    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.vrt")))
    mask_paths = sorted(glob.glob(os.path.join(mask_dir, "*.tif")))
    
    images = []
    masks = []
    
    print(f"Verificando {len(image_paths)} pares de imagem/máscara...")
    
    for img_path, mask_path in tqdm(zip(image_paths, mask_paths), total=len(image_paths)):
        # --- CARREGAR IMAGEM ---
        with rasterio.open(img_path) as src:
            # Verifica o número de bandas
            if src.count != 6:
                print(f"\nERRO FATAL ENCONTRADO!")
                print(f"ARQUIVO COM PROBLEMA: {os.path.basename(img_path)}")
                print(f"Número de bandas detectado: {src.count}")
                print(f"Número de bandas esperado: 6")
                print("Solução: Refaça o arquivo .vrt para este tile no QGIS.")
                raise ValueError("Número de bandas incorreto detectado.")

            img = src.read().transpose((1, 2, 0))
            
            # Normalização
            for i in range(img.shape[2]):
                band = img[:, :, i]
                min_val, max_val = np.percentile(band, 2), np.percentile(band, 98)
                if max_val > min_val:
                    img[:, :, i] = np.clip((band - min_val) / (max_val - min_val), 0, 1)
                else:
                    img[:, :, i] = 0
            
            # Redimensionar imagem
            img = tf.image.resize(img, [TILE_SIZE, TILE_SIZE])
            images.append(img)
            
        # --- CARREGAR MÁSCARA ---
        with rasterio.open(mask_path) as src:
            mask = src.read(1)
            
            # Redimensionar máscara
            mask = np.expand_dims(mask, axis=-1)
            mask = tf.image.resize(mask, [TILE_SIZE, TILE_SIZE], method='nearest')
            mask = tf.squeeze(mask, axis=-1)
            masks.append(mask)
            
    return np.array(images, dtype=np.float32), np.array(masks, dtype=np.uint8)

# --- 2. CONSTRUÇÃO DO MODELO U-NET ---
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
    u2 = tf.keras.layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(c_mid)
    u2 = tf.keras.layers.concatenate([u2, c2])
    c_up2 = tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u2)
    
    u1 = tf.keras.layers.Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(c_up2)
    u1 = tf.keras.layers.concatenate([u1, c1])
    c_up1 = tf.keras.layers.Conv2D(16, (3, 3), activation='relu', padding='same')(u1)
    
    outputs = tf.keras.layers.Conv2D(num_classes, (1, 1), activation='softmax')(c_up1)
    
    model = tf.keras.Model(inputs=[inputs], outputs=[outputs])
    return model

# --- 3. FLUXO PRINCIPAL DE TREINAMENTO ---
if __name__ == "__main__":
    # Carregar e pré-processar os dados
    images, masks = load_data(STACKED_IMAGES_DIR, MASKS_DIR)
    
    # Adicionar uma dimensão para o canal nas máscaras (exigido pelo TensorFlow)
    masks = np.expand_dims(masks, axis=-1)
    
    print(f"\nFormato dos dados de imagem: {images.shape}")
    print(f"Formato dos dados de máscara: {masks.shape}")
    
    # Dividir em conjuntos de treino e validação (80% treino, 20% validação)
    X_train, X_val, y_train, y_val = train_test_split(images, masks, test_size=0.2, random_state=42)
    
    print(f"\nTamanho do conjunto de treino: {len(X_train)} amostras")
    print(f"Tamanho do conjunto de validação: {len(X_val)} amostras")
    
    # Construir o modelo
    model = unet_model()
    
    # Compilar o modelo
    model.compile(optimizer='adam', 
                  loss='sparse_categorical_crossentropy', 
                  metrics=['accuracy'])
    
    model.summary()
    
    # Treinar o modelo
    print("\n--- INICIANDO O TREINAMENTO ---")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=4,  # Ajuste o batch_size dependendo da memória da sua GPU
        epochs=50      # 50 épocas é um bom ponto de partida
    )
    
    # Salvar o modelo treinado
    print(f"\n--- TREINAMENTO CONCLUÍDO. SALVANDO MODELO EM: {MODEL_SAVE_PATH} ---")
    model.save(MODEL_SAVE_PATH)
    
    print("Processo finalizado com sucesso!")