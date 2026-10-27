// Espelho dos schemas Pydantic de backend/src/erosion/api/schemas

export type StatusAnalise = "pendente" | "processando" | "concluida" | "erro";

export interface Health {
    api: string;
    gdal: string;
    gpu: string;
}

export interface Modelo {
    id: number;
    versao: string;
    criado_em: string;
}

export interface MicrobaciaRequest {
    nome: string;
    area_ha?: number | null;
    pais?: string | null;
    estado?: string | null;
    cidade?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    descricao?: string | null;
}

export interface Microbacia {
    id: number;
    nome: string;
    area_ha: number | null;
    pais: string | null;
    estado: string | null;
    cidade: string | null;
    latitude: number | null;
    longitude: number | null;
    descricao: string | null;
    criado_em: string | null;
}

export interface Imagem {
    caminho_imagem: string;
    nome_original: string;
    bandas: number;
    largura: number;
    altura: number;
    crs: string | null;
}

export interface AnaliseRequest {
    microbacia_id: number;
    modelo_id: number;
    caminho_imagem: string;
}

export interface Analise {
    id: number;
    microbacia_id: number;
    modelo_id: number;
    status: StatusAnalise;
    caminho_mosaico_resultado: string | null;
    criado_em: string;
    concluido_em: string | null;
}

export interface AnaliseFiltros {
    microbacia_id?: number;
    status?: StatusAnalise;
}

export interface StatusResposta {
    id: number;
    status: StatusAnalise;
    mensagem_erro: string | null;
}

export interface AreaClasse {
    hectares: number;
    percentual: number;
}

export interface Resultado {
    areas_por_classe: Record<string, AreaClasse>;
}
