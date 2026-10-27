import type { StatusAnalise } from "../api/types";

export const ROTULO_STATUS: Record<StatusAnalise, string> = {
    pendente: "Pendente",
    processando: "Processando",
    concluida: "Concluído",
    erro: "Erro",
};

// Nomes vem do config/pipeline.yaml; classe desconhecida cai no nome cru
export const CLASSES: Record<string, { rotulo: string; cor: string }> = {
    agricultura: { rotulo: "Agricultura", cor: "var(--agricultura)" },
    erosao: { rotulo: "Erosão", cor: "var(--risco)" },
    agua: { rotulo: "Água", cor: "var(--agua)" },
    vegetacao: { rotulo: "Vegetação", cor: "var(--vegetacao)" },
    construcao: { rotulo: "Construção", cor: "var(--urbana)" },
};

export function rotuloClasse(nome: string): string {
    return CLASSES[nome]?.rotulo ?? nome;
}

export function formatarData(iso: string | null): string {
    return iso ? new Date(iso).toLocaleDateString("pt-BR") : "-";
}

export function formatarNumero(valor: number, casas = 2): string {
    return valor.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
}

/** Le um id inteiro positivo da query string (ex.: ?analise=3). */
export function idDaUrl(parametro: string): number | null {
    const valor = Number(new URLSearchParams(window.location.search).get(parametro));
    return Number.isInteger(valor) && valor > 0 ? valor : null;
}

export function elemento<T extends HTMLElement>(id: string): T {
    const el = document.getElementById(id);
    if (!el) {
        throw new Error(`Elemento #${id} nao encontrado`);
    }
    return el as T;
}
