import os
import rasterio
from rasterio.windows import Window
import numpy as np
from glob import glob
import subprocess
from multiprocessing import Pool, cpu_count
from tqdm.notebook import tqdm # Usar tqdm.notebook para Jupyter

# --- 1. CONFIGURAÇÕES GLOBAIS (AJUSTE AQUI) ---
# Caminho base para os dados do projeto
BASE_PROJECT_DIR = r"C:\UNIOESTE"

# Diretórios de entrada e saída
INPUT_IMAGES_DIR = os.path.join(BASE_PROJECT_DIR, "imagens_renderizadas")
OUTPUT_TILES_DIR = os.path.join(BASE_PROJECT_DIR, "dados_processados", "tiles")
OUTPUT_INDICES_DIR = os.path.join(BASE_PROJECT_DIR, "dados_processados", "indices")
OUTPUT_MOSAICS_DIR = os.path.join(BASE_PROJECT_DIR, "dados_processados", "mosaicos_finais")

# Parâmetros para o corte em tiles
TILE_SIZE = 512     # Dimensão de cada tile (em pixels)
STRIDE = TILE_SIZE // 2     # Sobreposição dos tiles (50%)

# Lista de imagens originais para processar (treino e teste)
IMAGES_TO_PROCESS = {
    "train": [
        "120m - 27-09.tif",
        "120m - 18-10.tif",
        "120m - 10-11-25.tif"
    ],
    "test": [
        "120m - 14-11.tif",
        "120m - 19-11-25.tif"
    ]
}

# Lista de índices a calcular (nomes internos e ordem das bandas)
# B1:Red, B2:Green, B3:Blue, B4:NIR
INDEX_DEFINITIONS = [
    {"name": "bi", "bands": ["R", "G"], "formula": lambda R, G, B, NIR, SWIR: np.sqrt((R**2 + G**2) / 2)},
    {"name": "bi2", "bands": ["R", "G", "B"], "formula": lambda R, G, B, NIR, SWIR: np.sqrt((R**2 + G**2 + B**2) / 3)},
    {"name": "bsi", "bands": ["R", "G", "B", "NIR", "SWIR"], "formula": lambda R, G, B, NIR, SWIR: ((SWIR + R) - (NIR + B)) / ((SWIR + R) + (NIR + B) + 1e-6)},
    {"name": "satvi", "bands": ["R", "SWIR"], "formula": lambda R, G, B, NIR, SWIR: ((SWIR - R) / (SWIR + R + 0.5) + 1e-6) * (1 + 0.5)}, # L=0.5
    {"name": "ndvi", "bands": ["R", "NIR"], "formula": lambda R, G, B, NIR, SWIR: (NIR - R) / (NIR + R + 1e-6)},
    {"name": "ndmi", "bands": ["NIR", "SWIR"], "formula": lambda R, G, B, NIR, SWIR: (SWIR - NIR) / (SWIR + NIR + 1e-6)}, # Renomeado de ndbrsmi para ndmi
]

# --- 2. FUNÇÕES AUXILIARES ---
def create_directories():
    """Cria todos os diretórios de saída necessários."""
    os.makedirs(OUTPUT_TILES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_INDICES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MOSAICS_DIR, exist_ok=True)
    for split in IMAGES_TO_PROCESS.keys():
        os.makedirs(os.path.join(OUTPUT_TILES_DIR, split), exist_ok=True)
        os.makedirs(os.path.join(OUTPUT_INDICES_DIR, split), exist_ok=True)
        for index_def in INDEX_DEFINITIONS:
            os.makedirs(os.path.join(OUTPUT_INDICES_DIR, split, index_def["name"]), exist_ok=True)
    print("Diretórios de saída criados/verificados.")

def run_gdal_command(command, description="GDAL command"): # Adicionado descrição para melhor log
    """Executa um comando GDAL e imprime a saída/erros."""
    print(f"Executando: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
        if result.stderr:
            # GDAL pode usar stderr para progresso, verificar se é um erro real
            if "error" in result.stderr.lower() or "failed" in result.stderr.lower():
                print(f"STDERR ({description}):\n{result.stderr}")
        # print(f"STDOUT ({description}):\n{result.stdout}") # Descomente para ver o stdout completo
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar o comando GDAL ({description}): {e.cmd}")
        print(f"STDERR: {e.stderr}")
        print(f"STDOUT: {e.stdout}")
        raise # Re-lança a exceção para parar o processo se houver um erro crítico

# VERSÃO NOVA E CORRIGIDA
def save_raster(data_array, profile, out_path):
    """Salva um array numpy (potencialmente multibanda) como um arquivo GeoTIFF."""
    # Se o array for 2D (ex: 512, 512), adiciona uma dimensão de banda na frente.
    if data_array.ndim == 2:
        data_array = np.expand_dims(data_array, axis=0)
    
    # Agora o array está garantido como 3D (ex: 1, 512, 512) ou (4, 512, 512)
    with rasterio.open(out_path, 'w', **profile) as dst:
        dst.write(data_array)


# ---    CÓDIGO DESATUALIZADO
# ---    with rasterio.open(out_path, 'w', **profile) as dst:
# ---        dst.write(data_array, 1)

# --- 3. ETAPA 1: CORTE DE TILES ---
def cut_tiles():
    """Corta as imagens originais em tiles com sobreposição."""
    print("\n--- ETAPA 1: CORTE DE TILES ---")
    for split, image_list in IMAGES_TO_PROCESS.items():
        print(f"Processando imagens para o conjunto: {split.upper()}")
        for image_name in tqdm(image_list, desc=f"Cortando {split} imagens"): # Adicionado tqdm
            image_path = os.path.join(INPUT_IMAGES_DIR, image_name)
            if not os.path.exists(image_path):
                print(f"AVISO: Imagem não encontrada: {image_path}. Pulando.")
                continue

            prefix = os.path.splitext(image_name)[0].replace(" ", "_").replace("-", "_").replace("'", "")
            output_split_dir = os.path.join(OUTPUT_TILES_DIR, split)

            with rasterio.open(image_path) as src:
                width, height = src.width, src.height
                transform = src.transform
                tile_idx = 0

                for y in range(0, height - TILE_SIZE + 1, STRIDE):
                    for x in range(0, width - TILE_SIZE + 1, STRIDE):
                        window = Window(x, y, TILE_SIZE, TILE_SIZE)
                        
                        # Ajustar o profile para o tile
                        tile_profile = src.profile.copy()
                        tile_profile.update({
                            'height': window.height,
                            'width': window.width,
                            'transform': src.window_transform(window) # Usar src.window_transform
                        })

                        tile_data = src.read(window=window)
# Se tile_data tiver 4 dimensões (ex: 1, 4, 512, 512), remove a primeira.
                        if tile_data.ndim == 4 and tile_data.shape[0] == 1:
                            tile_data = tile_data.squeeze(axis=0)
                        # O formato agora está garantido como (4, 512, 512)
                        # --- FIM DA CORREÇÃO ---

                        tile_name = f"{prefix}_tile_{tile_idx:05d}.tif"
                        out_path = os.path.join(output_split_dir, tile_name)
                        
                        # Precisamos ajustar a função save_raster para lidar com múltiplas bandas
                        # Esta é a chamada correta, vamos corrigir a função save_raster também.
                        with rasterio.open(out_path, 'w', **tile_profile) as dst:
                            dst.write(tile_data)

# --- CÓDIGOS ANTIGOS E DESATUALIZADOS
# ---                        tile_name = f"{prefix}_tile_{tile_idx:05d}.tif"
# ---                        out_path = os.path.join(output_split_dir, tile_name)
# ---                        save_raster(tile_data, tile_profile, out_path)
                        tile_idx += 1
                # print(f"  {tile_idx} tiles guardados de {image_name}.") # Removido para usar tqdm
    print("Corte de tiles concluído.")

# --- 4. ETAPA 2: CÁLCULO DE ÍNDICES (SALVA DIRETAMENTE NO PROCESSO) ---
def process_single_tile_for_indices(tile_info):
    """Função para processar um único tile, calcular E SALVAR seus índices."""
    tile_path, output_base_dir_for_split = tile_info
    
    try:
        with rasterio.open(tile_path) as src:
            profile = src.profile.copy()
            
            if src.count < 4:
                return # Pula tiles com menos de 4 bandas

            R = src.read(1).astype(np.float32)
            G = src.read(2).astype(np.float32)
            B = src.read(3).astype(np.float32)
            NIR = src.read(4).astype(np.float32)
            SWIR = (R + G + B) / 3

            profile.update(dtype=rasterio.float32, count=1, compress='lzw')

            for index_def in INDEX_DEFINITIONS:
                index_name = index_def["name"]
                formula = index_def["formula"]
                
                index_data = formula(R, G, B, NIR, SWIR)
                
                tile_filename = os.path.basename(tile_path)
                output_path = os.path.join(output_base_dir_for_split, index_name, tile_filename)
                
                # Salva o arquivo diretamente aqui, dentro do processo trabalhador
                save_raster(index_data, profile, output_path)
        return True # Retorna um valor simples para sinalizar sucesso
    except Exception as e:
        # Captura qualquer erro que possa acontecer no processo e o imprime
        print(f"ERRO ao processar o tile {os.path.basename(tile_path)}: {e}")
        return False # Sinaliza falha

# VERSÃO NOVA (ADAPTADA PARA O NOVO PROCESSO)
def calculate_indices_parallel():
    """Calcula os índices espectrais para todos os tiles usando paralelização."""
    print("\n--- ETAPA 2: CÁLCULO DE ÍNDICES ---")
    all_tile_paths = []
    for split in IMAGES_TO_PROCESS.keys():
        search_path = os.path.join(OUTPUT_TILES_DIR, split, "*.tif")
        tile_files = glob(search_path)
        output_base_dir_for_split = os.path.join(OUTPUT_INDICES_DIR, split)
        for tile_path in tile_files:
            all_tile_paths.append((tile_path, output_base_dir_for_split))

    if not all_tile_paths:
        print("Nenhum tile encontrado para calcular índices. Certifique-se de que a Etapa 1 foi executada.")
        return

    print(f"Calculando índices para {len(all_tile_paths)} tiles usando {cpu_count()} núcleos...")
    
    with Pool(cpu_count()) as pool:
        # O tqdm agora apenas itera sobre os resultados, que são True/False
        # A escrita dos arquivos está acontecendo dentro de process_single_tile_for_indices
        list(tqdm(pool.imap_unordered(process_single_tile_for_indices, all_tile_paths), total=len(all_tile_paths), desc="Calculando Índices"))
        
    print("Cálculo de índices concluído.")

# --- 5. ETAPA 3: GERAÇÃO DE MOSAICOS FINAIS (COG) ---
def generate_final_mosaics():
    """Gera os mosaicos finais em formato COG a partir dos tiles de índices."""
    print("\n--- ETAPA 3: GERAÇÃO DE MOSAICOS FINAIS (COG) ---")
    for split in IMAGES_TO_PROCESS.keys():
        print(f"Processando mosaicos para o conjunto: {split.upper()}")
        for index_def in tqdm(INDEX_DEFINITIONS, desc=f"Gerando mosaicos para {split}"):
            index_name = index_def["name"]
            
            input_index_tiles_dir = os.path.join(OUTPUT_INDICES_DIR, split, index_name)
            
            # Lista todos os tiles .tif para o índice atual.
            tile_files = glob(os.path.join(input_index_tiles_dir, "*.tif"))
            if not tile_files:
                print(f"AVISO: Nenhum tile encontrado para {index_name} no conjunto {split}. Pulando.")
                continue
            
            # Cria um arquivo de texto com a lista de todos os tiles (para gdalbuildvrt)
            tile_list_path = os.path.join(OUTPUT_MOSAICS_DIR, f"{split}_{index_name}_filelist.txt")
            with open(tile_list_path, 'w') as f:
                for tile_path in tile_files:
                    f.write(f'{tile_path}\n')

            vrt_path = os.path.join(OUTPUT_MOSAICS_DIR, f"{split}_{index_name}.vrt")
            final_cog_path = os.path.join(OUTPUT_MOSAICS_DIR, f"{split}_{index_name}_final.tif")

            # ETAPA 3.1: Criação do Mosaico Virtual (.vrt)
            command_vrt = f'gdalbuildvrt -input_file_list "{tile_list_path}" "{vrt_path}"'
            run_gdal_command(command_vrt, description=f"gdalbuildvrt para {split}_{index_name}")

            # ETAPA 3.2: Conversão do Mosaico Virtual para COG Final
            # Usamos -co NUM_THREADS=ALL_CPUS para gdal_translate para otimizar
            command_cog = f'gdal_translate "{vrt_path}" "{final_cog_path}" -of COG -co COMPRESS=LZW -co NUM_THREADS=ALL_CPUS'
            run_gdal_command(command_cog, description=f"gdal_translate para {split}_{index_name}")
            
            # Limpeza: remove o arquivo .vrt e a lista de arquivos temporários
            os.remove(vrt_path)
            os.remove(tile_list_path)

    print("Geração de mosaicos COG concluída.")

# --- 6. EXECUÇÃO DA PIPELINE COMPLETA ---
if __name__ == "__main__":
    print("Iniciando a pipeline de processamento de imagens de drone...")
    create_directories()
    cut_tiles()
    calculate_indices_parallel()
    generate_final_mosaics()
    print("\nPipeline concluída com sucesso!")


