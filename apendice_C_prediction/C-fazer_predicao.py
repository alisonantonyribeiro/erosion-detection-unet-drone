import os
import rasterio
import numpy as np
import tensorflow as tf
from tqdm import tqdm

# --- CONFIGURAÇÃO (AJUSTE OS CAMINHOS AQUI) ---
MODEL_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\modelo_erosao_unet_V9_calibrated.h5"
INPUT_STACK_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\dados_para_predicao\120m___14_11_tile_02212.vrt"
OUTPUT_PREDICTION_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\dados_para_predicao\120m___14_11_tile_02212_V9.tif"

# --- PARÂMETROS (DEVEM SER OS MESMOS DO TREINAMENTO) ---
TILE_SIZE = 512
NUM_BANDS = 6

# --- FUNÇÃO DE PRÉ-PROCESSAMENTO ---
def preprocess_image(image_stack):
    img = image_stack.transpose((1, 2, 0))
    for i in range(img.shape[2]):
        band = img[:, :, i]
        min_val, max_val = np.percentile(band, 2), np.percentile(band, 98)
        if max_val > min_val:
            img[:, :, i] = np.clip((band - min_val) / (max_val - min_val), 0, 1)
        else:
            img[:, :, i] = 0
    img = np.expand_dims(img, axis=0)
    return img.astype(np.float32)

# --- FLUXO PRINCIPAL DE PREDIÇÃO ---
if __name__ == "__main__":
    print(f"--- Carregando modelo de: {MODEL_PATH} ---")
    model = tf.keras.models.load_model(MODEL_PATH)
    
    print(f"--- Lendo e pré-processando imagem de entrada: {INPUT_STACK_PATH} ---")
    # Abrimos o VRT para ler os dados e metadados essenciais
    with rasterio.open(INPUT_STACK_PATH) as src:
        # Copiamos as informações geoespaciais importantes
        transform = src.transform
        crs = src.crs
        # Lemos os dados
        image_data = src.read()
    
    processed_image = preprocess_image(image_data)
    
    print(f"--- Realizando predição... ---")
    prediction = model.predict(processed_image)
    
    prediction_map = np.argmax(prediction[0], axis=-1).astype(np.uint8)
    
    print(f"--- Predição concluída. Salvando resultado em: {OUTPUT_PREDICTION_PATH} ---")
    
    # --- MUDANÇA PRINCIPAL AQUI ---
    # Em vez de copiar o profile do VRT, criamos um novo profile limpo para o GeoTIFF de saída
    output_profile = {
        'driver': 'GTiff',
        'height': prediction_map.shape[0],
        'width': prediction_map.shape[1],
        'count': 1,
        'dtype': prediction_map.dtype,
        'crs': crs,
        'transform': transform,
        'compress': 'lzw'
    }
    
    with rasterio.open(OUTPUT_PREDICTION_PATH, 'w', **output_profile) as dst:
        dst.write(prediction_map, 1)
        
    print("Processo finalizado com sucesso!")