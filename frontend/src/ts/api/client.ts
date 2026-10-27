import axios, { AxiosError } from "axios";

// Em dev o Vite faz proxy de /api para o FastAPI (ver vite.config.ts).
// Para apontar direto para outra API, defina VITE_API_URL no .env do frontend.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "/api";

export const http = axios.create({
    baseURL: API_URL,
    timeout: 30_000,
});

interface DetalheFastApi {
    detail?: string | { loc: (string | number)[]; msg: string }[];
}

/** Converte o erro do axios na mensagem que o FastAPI mandou em `detail`. */
export function mensagemDeErro(erro: unknown): string {
    if (!(erro instanceof AxiosError)) {
        return erro instanceof Error ? erro.message : String(erro);
    }
    if (!erro.response) {
        return "Nao foi possivel conectar a API. Ela esta rodando?";
    }

    const detail = (erro.response.data as DetalheFastApi | undefined)?.detail;
    if (typeof detail === "string") {
        return detail;
    }
    // 422 de validacao do Pydantic: lista de { loc, msg }
    if (Array.isArray(detail)) {
        return detail.map((item) => `${item.loc.slice(1).join(".")}: ${item.msg}`).join("; ");
    }
    return `Erro ${erro.response.status}`;
}

export function statusHttp(erro: unknown): number | undefined {
    return erro instanceof AxiosError ? erro.response?.status : undefined;
}
