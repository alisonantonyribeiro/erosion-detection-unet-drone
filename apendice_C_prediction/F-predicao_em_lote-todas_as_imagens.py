import os
import glob
import numpy as np
import rasterio
import tensorflow as tf
from tqdm import tqdm

# --- CONFIGURAÇÃO (AJUSTE AQUI) ---

# 1. Onde estão os seus índices? 
# Aponte para a pasta que contém as subpastas 'bi', 'ndvi', etc.
# Exemplo: Se seus novos dados estão em 'train', use o caminho do train.
INDICES_BASE_DIR = r"C:\UNIOESTE\dados_processados\indices\train_selecionadas" 

# 2. Onde salvar as predições?
OUTPUT_DIR = r"C:\UNIOESTE\dados_processados\MAPA_2025-indices_FINAL"

# 3. Qual modelo usar? (O V9 Campeão)
MODEL_PATH = r"C:\UNIOESTE\dados_processados\TESE_IA_TREINAMENTO\modelo_erosao_unet_V9_calibrated.h5"

# --- PARÂMETROS ---
TILE_SIZE = 512
INDICES_LIST = ["ndmi", "ndvi", "satvi", "bsi", "bi2", "bi"] # A ordem deve ser a mesma do treinamento!

# --- FUNÇÃO DE PRÉ-PROCESSAMENTO ---
def preprocess_image(image_stack):
    # Normalização (igual ao treinamento)
    img = image_stack.astype(np.float32)
    for i in range(img.shape[2]):
        band = img[:, :, i]
        min_val, max_val = np.percentile(band, 2), np.percentile(band, 98)
        if max_val > min_val:
            img[:, :, i] = np.clip((band - min_val) / (max_val - min_val), 0, 1)
        else:
            img[:, :, i] = 0
    # Adiciona dimensão de lote
    img = np.expand_dims(img, axis=0)
    return img

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    # Criar pasta de saída se não existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"--- Carregando modelo V9: {MODEL_PATH} ---")
    model = tf.keras.models.load_model(MODEL_PATH)

    # 1. Listar todos os tiles disponíveis (usando a pasta NDVI como referência)
    reference_dir = os.path.join(INDICES_BASE_DIR, "ndvi")
    tile_files = sorted(glob.glob(os.path.join(reference_dir, "*.tif")))
    
    print(f"--- Encontrados {len(tile_files)} tiles para processar em: {INDICES_BASE_DIR} ---")

    # 2. Loop principal
    for tile_path in tqdm(tile_files, desc="Gerando Predições"):
        tile_name = os.path.basename(tile_path)
        output_path = os.path.join(OUTPUT_DIR, tile_name)
        
        # Se já existe, pula (útil se o processo parar e você recomeçar)
        if os.path.exists(output_path):
            continue

        try:
            # 3. Empilhar os índices na memória
            stack_list = []
            ref_profile = None # Guardar o perfil para salvar depois

            for idx_name in INDICES_LIST:
                # Constrói o caminho para cada índice: .../indices/train/INDICE/tile_X.tif
                idx_path = os.path.join(INDICES_BASE_DIR, idx_name, tile_name)
                
                with rasterio.open(idx_path) as src:
                    if idx_name == "bi": # Salva o perfil do primeiro índice
                        ref_profile = src.profile
                    
                    # Lê a banda e garante que é float32
                    band_data = src.read(1).astype(np.float32)
                    
                    # Garante tamanho 512x512 (caso haja erro de arredondamento no corte)
                    if band_data.shape != (TILE_SIZE, TILE_SIZE):
                         # Redimensionamento simples via zoom se necessário (raro)
                         # Aqui assumimos que estão corretos pelo pipeline anterior
                         pass 
                         
                    stack_list.append(band_data)

            # Cria o array (Altura, Largura, Bandas) -> (512, 512, 6)
            image_stack = np.stack(stack_list, axis=-1)

            # 4. Previsão
            input_data = preprocess_image(image_stack)
            prediction = model.predict(input_data, verbose=0) # verbose=0 para não sujar o log
            prediction_map = np.argmax(prediction[0], axis=-1).astype(np.uint8)

            # 5. Salvar resultado
            ref_profile.update(
                count=1,
                dtype='uint8',
                compress='lzw',
                driver='GTiff'
            )

            with rasterio.open(output_path, 'w', **ref_profile) as dst:
                dst.write(prediction_map, 1)

        except Exception as e:
            print(f"ERRO ao processar {tile_name}: {e}")
            continue

    print(f"\n--- Processo Finalizado! ---")
    print(f"Mapas salvos em: {OUTPUT_DIR}")