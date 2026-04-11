# Erosion Detection with U-Net and DRONE imagery

**Metodologia integrada VANT + U-Net + RUSLE para diagnóstico erosivo em microbacias rurais**

> Tese de Doutorado — Universidade Estadual do Oeste do Paraná (UNIOESTE)
> Autora: Alison | Orientador: Pedro Melo-Pinto | Co-autor: Armin Feiden
> Publicação alvo: *Remote Sensing Applications: Society and Environment* (Elsevier)

---

## Sobre este repositório

Este repositório disponibiliza os scripts Python desenvolvidos para a tese de doutorado intitulada:

**"Geotecnologias e inteligência artificial aplicadas à gestão hídrica em microbacias rurais: diagnóstico erosivo, simulação de cenários e validação por RUSLE nas nascentes da microbacia do Arroio Fundo, Paraná"**

A metodologia integra:
- Levantamento aerofotogramétrico por **VANT** (DJI Phantom 4 RTK) com resolução de 3,7 cm/pixel
- Cálculo de **índices espectrais** multitemporais (BI, BI2, BSI, SATVI, NDVI, NDMI)
- Segmentação semântica por **rede neural convolucional U-Net** (TensorFlow/Keras)
- Validação quantitativa independente por **RUSLE** (Equação Universal de Perda de Solo Revisada)
- Modelagem de cenários prospectivos no **QGIS**

---

## Área de Estudo

Nascentes da microbacia do Arroio Fundo — manancial de abastecimento público do município de Marechal Cândido Rondon, localizada na divisa com Quatro Pontes, oeste do Paraná, Brasil.

- **Área monitorada:** 59,24 hectares
- **Resolução espacial:** 3,7 cm/pixel (GSD médio)
- **Sistema de coordenadas:** SIRGAS 2000 / UTM fuso 22S (EPSG:31982)
- **Período de monitoramento:** agosto de 2024 a novembro de 2025

---

## Estrutura do Repositório

```
📁 erosion-detection-unet-drone/
│
├── 📄 README.md                          # Este arquivo
│
├── 📁 apendice_A_preprocessing/
│   └── A-optimized_pipeline.py           # Pipeline completa de pré-processamento
│
├── 📁 apendice_B_training/
│   ├── B-treinar_modelo.py               # Treinamento base — Modelos V1 a V4
│   ├── D-treinar_modelo_com_augmentation.py  # Data Augmentation — Modelo V5
│   └── E-treinar_modelo_pesos.py         # Class Weights — Modelo Final V9
│
├── 📁 apendice_C_prediction/
│   ├── C-fazer_predicao.py               # Predição individual de tile
│   ├── F-predicao_em_lote-todas_as_imagens.py  # Predição em lote — microbacia completa
│   └── G-criar_mosaico_vrt.py            # Geração do mosaico VRT final
│
└── 📄 requirements.txt                   # Dependências Python
```

---

## Instalação

### Requisitos

- Python 3.10+
- GPU NVIDIA com CUDA (recomendado para treinamento)
- QGIS 3.28+ (para etapas de geoprocessamento)

### Instalação das dependências

```bash
pip install -r requirements.txt
```

---

## Como Usar

### Etapa 1 — Pré-processamento (Apêndice A)

Processa as imagens do VANT, gera tiles de 512×512px e calcula os 6 índices espectrais:

```bash
python A-optimized_pipeline.py
```

**Configure antes de executar:**
```python
# Em A-optimized_pipeline.py, ajuste:
BASE_PROJECT_DIR = r"C:\SEU_CAMINHO\dados"
IMAGES_TO_PROCESS = {
    "train": ["imagem_treino_1.tif", "imagem_treino_2.tif"],
    "test":  ["imagem_teste_1.tif"]
}
```

### Etapa 2 — Treinamento (Apêndice B)

**Versão base (V1–V4):**
```bash
python B-treinar_modelo.py
```

**Com Data Augmentation (V5):**
```bash
python D-treinar_modelo_com_augmentation.py
```

**Com Ponderação de Classes — Modelo Final V9 (V6–V9):**
```bash
python E-treinar_modelo_pesos.py
```

### Etapa 3 — Predição (Apêndice C)

**Predição de um tile individual:**
```bash
python C-fazer_predicao.py
```

**Predição em lote — microbacia completa:**
```bash
python F-predicao_em_lote-todas_as_imagens.py
```

**Geração do mosaico final:**
```bash
python G-criar_mosaico_vrt.py
```

---

## Classes do Modelo

| Código | Classe | Valor C (RUSLE) | Descrição |
|--------|--------|-----------------|-----------|
| 0 | Agricultura | 0,200 | Cultivo agrícola ativo (soja, milho) |
| 1 | Erosão | 0,800 | Processos erosivos ativos (sulcos, ravinas) |
| 2 | Água | 0,000 | Corpos d'água superficiais |
| 3 | Vegetação | 0,001 | Vegetação nativa, matas ciliares |
| 4 | Construção | 0,001 | Edificações, estradas, superfícies impermeáveis |

---

## Índices Espectrais Utilizados

| Índice | Nome completo | Finalidade |
|--------|--------------|------------|
| NDVI | Normalized Difference Vegetation Index | Densidade e vigor da cobertura vegetal |
| NDMI | Normalized Difference Moisture Index | Variações de umidade do solo e vegetação |
| BSI | Bare Soil Index | Realce de áreas de solo exposto |
| BI | Brightness Index | Indicador geral de brilho da superfície |
| BI2 | Brightness Index 2 | Complementa o BI com a banda NIR |
| SATVI | Soil Adjusted Total Vegetation Index | Discriminação de solo exposto em vegetação esparsa |

---

## Resultados

| Cenário | Alto Risco (ha) | Risco Crítico (ha) | Baixo Risco (ha) |
|---------|----------------|--------------------|-----------------|
| 2025 — Atual | 35,73 (60,31%) | 1,61 (2,72%) | 10,70 (18,06%) |
| 2035 — APP Restaurada | 9,70 (16,38%) | 0,00 (0,00%) | 44,94 (75,85%) |

**Validação RUSLE — Perda de solo por classe de risco (cenário 2025):**

| Classe de Risco | Perda média (t ha⁻¹ ano⁻¹) |
|----------------|---------------------------|
| Baixo (1) | 0,20 |
| Médio (3) | 8,01 |
| Alto (5) | 77,50 |
| Crítico (10) | 114,52 |

---

## Desempenho do Modelo

| Versão | Acurácia | Loss | Estratégia |
|--------|----------|------|------------|
| V1 | 63,5% | 0,99 | Baseline — 50 tiles |
| V3 | 71,8% | 0,85 | 120 tiles |
| V5 | 80,1% | 0,53 | Data Augmentation ×4 |
| **V9** | **76,7%** | **0,10** | **Class Weights — Modelo Final** |

---

## Requisitos Mínimos para Replicação

- VANT com câmera de alta resolução (≥ 20 MP, preferencialmente RGB + NIR)
- Software QGIS (versão 3.28 ou superior) — gratuito
- Python 3.10 com as bibliotecas listadas em `requirements.txt`
- GPU NVIDIA (recomendado) ou CPU para inferência

---

## Citação

Se você utilizar este código em sua pesquisa, por favor cite:

```bibtex
@phdthesis{arroio_fundo_2026,
  title     = {Geotecnologias e intelig{\^e}ncia artificial aplicadas {\`a} gest{\~a}o h{\'i}drica
               em microbacias rurais: diagn{\'o}stico erosivo, simula{\c{c}}{\~a}o de cen{\'a}rios
               e valida{\c{c}}{\~a}o por RUSLE nas nascentes da microbacia do Arroio Fundo, Paran{\'a}},
  author    = {[Alison]},
  school    = {Universidade Estadual do Oeste do Paran{\'a} -- UNIOESTE},
  year      = {2026},
  address   = {Marechal C{\^a}ndido Rondon, PR, Brasil}
}
```

---

## Licença

Este projeto está licenciado sob a **Licença MIT** — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Contato

Para dúvidas sobre a metodologia ou replicação:
- Abra uma **Issue** neste repositório
- Ou entre em contato pelo e-mail institucional da UNIOESTE
