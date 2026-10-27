import { http } from "./client";
import type {
    Analise,
    AnaliseFiltros,
    AnaliseRequest,
    Health,
    Imagem,
    Microbacia,
    MicrobaciaRequest,
    Modelo,
    Resultado,
    StatusResposta,
} from "./types";

export async function verificarSaude(): Promise<Health> {
    const { data } = await http.get<Health>("/health");
    return data;
}

export async function listarModelos(): Promise<Modelo[]> {
    const { data } = await http.get<Modelo[]>("/modelos");
    return data;
}

export async function listarMicrobacias(): Promise<Microbacia[]> {
    const { data } = await http.get<Microbacia[]>("/microbacias");
    return data;
}

export async function buscarMicrobacia(id: number): Promise<Microbacia> {
    const { data } = await http.get<Microbacia>(`/microbacias/${id}`);
    return data;
}

export async function criarMicrobacia(payload: MicrobaciaRequest): Promise<Microbacia> {
    const { data } = await http.post<Microbacia>("/microbacias", payload);
    return data;
}

export async function enviarImagem(arquivo: File): Promise<Imagem> {
    const form = new FormData();
    form.append("arquivo", arquivo);
    // GeoTIFF de drone pode ter centenas de MB: sem timeout no upload
    const { data } = await http.post<Imagem>("/imagens", form, { timeout: 0 });
    return data;
}

export async function listarAnalises(filtros: AnaliseFiltros = {}): Promise<Analise[]> {
    const { data } = await http.get<Analise[]>("/analises", { params: filtros });
    return data;
}

export async function criarAnalise(payload: AnaliseRequest): Promise<Analise> {
    const { data } = await http.post<Analise>("/analises", payload);
    return data;
}

export async function consultarStatus(analiseId: number): Promise<StatusResposta> {
    const { data } = await http.get<StatusResposta>(`/analises/${analiseId}/status`);
    return data;
}

export async function consultarResultado(analiseId: number): Promise<Resultado> {
    const { data } = await http.get<Resultado>(`/analises/${analiseId}/resultado`);
    return data;
}
