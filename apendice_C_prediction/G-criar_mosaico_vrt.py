import os
import glob
import subprocess
from tqdm import tqdm

# --- CONFIGURAÇÃO ---
# Pasta onde estão os seus 16 mil tiles classificados (predições)
INPUT_DIR = r"C:\UNIOESTE\dados_processados\indices\MAPA_2025-indices_FINAL"

# Onde salvar o mosaico final e qual nome dar
OUTPUT_VRT = r"C:\UNIOESTE\dados_processados\indices\MAPA_2025-indices_FINAL.vrt"

# Arquivo temporário para a lista (será criado e depois apagado)
LIST_FILE = "lista_arquivos_temp.txt"

# --- PROCESSO ---
if __name__ == "__main__":
    print("--- 1. Listando arquivos... ---")
    # Busca todos os .tif na pasta
    tif_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.tif")))
    
    count = len(tif_files)
    print(f"Encontrados {count} arquivos.")
    
    if count == 0:
        print("ERRO: Nenhum arquivo encontrado. Verifique o caminho.")
        exit()

    print("--- 2. Criando lista de texto... ---")
    # Escreve os caminhos em um arquivo de texto, um por linha
    with open(LIST_FILE, 'w') as f:
        for file_path in tqdm(tif_files):
            f.write(file_path + '\n')
            
    print("--- 3. Executando gdalbuildvrt... ---")
    # Comando para criar o VRT usando a lista de texto
    # -srcnodata 0: Define que 0 é transparente (opcional, remova se 0 for Agricultura importante)
    # Se 0 for agricultura, NÃO use -srcnodata 0. Vamos deixar padrão.
    
    command = f"gdalbuildvrt -input_file_list {LIST_FILE} {OUTPUT_VRT}"
    
    try:
        # Executa o comando no sistema
        subprocess.run(command, shell=True, check=True)
        print(f"\nSUCESSO! Mosaico criado em: {OUTPUT_VRT}")
    except subprocess.CalledProcessError as e:
        print(f"\nERRO ao criar mosaico: {e}")
    finally:
        # Limpeza: remove a lista temporária
        if os.path.exists(LIST_FILE):
            os.remove(LIST_FILE)
            print("Lista temporária removida.")