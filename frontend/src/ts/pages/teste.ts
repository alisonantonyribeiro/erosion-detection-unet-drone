import { AxiosError } from "axios";

import { API_URL, http, mensagemDeErro } from "../api/client";
import {
    buscarMicrobacia,
    consultarResultado,
    consultarStatus,
    criarAnalise,
    criarMicrobacia,
    enviarImagem,
    listarAnalises,
    listarMicrobacias,
    listarModelos,
    verificarSaude,
} from "../api/endpoints";
import type { AnaliseFiltros, AnaliseRequest, MicrobaciaRequest, StatusAnalise } from "../api/types";
import { elemento } from "../utils/format";

// As funcoes de endpoints.ts devolvem so o corpo; o status HTTP vem por este interceptor
let ultimoStatus = 0;
http.interceptors.response.use((resposta) => {
    ultimoStatus = resposta.status;
    return resposta;
});

elemento("apiUrl").textContent = API_URL;

type Chamada = (form: HTMLFormElement) => Promise<unknown>;

function campo<T extends HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(form: HTMLFormElement, nome: string): T {
    return form.elements.namedItem(nome) as T;
}

function idDoCampo(form: HTMLFormElement): number {
    return Number(campo<HTMLInputElement>(form, "id").value);
}

function lerJson<T>(form: HTMLFormElement): T {
    const texto = campo<HTMLTextAreaElement>(form, "corpo").value;
    try {
        return JSON.parse(texto) as T;
    } catch {
        throw new Error("JSON inválido no corpo da requisição");
    }
}

/** Atualiza um campo do JSON de outro card, mantendo o resto do que o usuario digitou. */
function atualizarJson(formId: string, chave: string, valor: unknown): void {
    const textarea = campo<HTMLTextAreaElement>(elemento<HTMLFormElement>(formId), "corpo");
    try {
        const corpo = JSON.parse(textarea.value) as Record<string, unknown>;
        corpo[chave] = valor;
        textarea.value = JSON.stringify(corpo, null, 2);
    } catch {
        // JSON editado a mao e invalido: nao mexe
    }
}

function preencherId(formId: string, valor: number): void {
    campo<HTMLInputElement>(elemento<HTMLFormElement>(formId), "id").value = String(valor);
}

function mostrarResposta(saida: HTMLPreElement, ok: boolean, cabecalho: string, corpo: unknown): void {
    saida.hidden = false;
    saida.className = `resposta ${ok ? "sucesso" : "falha"}`;
    const texto = typeof corpo === "string" ? corpo : JSON.stringify(corpo, null, 2);
    saida.textContent = `${cabecalho}\n\n${texto}`;
}

async function executar(form: HTMLFormElement, chamada: Chamada): Promise<boolean> {
    const saida = form.querySelector<HTMLPreElement>(".resposta")!;
    const botao = form.querySelector<HTMLButtonElement>("button[type=submit]")!;

    botao.disabled = true;
    const inicio = performance.now();
    try {
        const dados = await chamada(form);
        const ms = Math.round(performance.now() - inicio);
        mostrarResposta(saida, true, `${ultimoStatus} OK · ${ms} ms`, dados);
        return true;
    } catch (erro) {
        const ms = Math.round(performance.now() - inicio);
        if (erro instanceof AxiosError && erro.response) {
            mostrarResposta(saida, false, `${erro.response.status} ${erro.response.statusText} · ${ms} ms`, erro.response.data);
        } else {
            mostrarResposta(saida, false, "Sem resposta da API", mensagemDeErro(erro));
        }
        return false;
    } finally {
        botao.disabled = false;
    }
}

// =========================
// CHAMADAS DE CADA CARD
// =========================

const chamadas: Record<string, Chamada> = {
    tHealth: () => verificarSaude(),

    tModelos: async () => {
        const modelos = await listarModelos();
        if (modelos.length > 0) {
            const recente = modelos.reduce((a, b) => (a.criado_em > b.criado_em ? a : b));
            atualizarJson("tAnalisesCriar", "modelo_id", recente.id);
        }
        return modelos;
    },

    tMicrobaciasListar: () => listarMicrobacias(),

    tMicrobaciasBuscar: (form) => buscarMicrobacia(idDoCampo(form)),

    tMicrobaciasCriar: async (form) => {
        const microbacia = await criarMicrobacia(lerJson<MicrobaciaRequest>(form));
        preencherId("tMicrobaciasBuscar", microbacia.id);
        atualizarJson("tAnalisesCriar", "microbacia_id", microbacia.id);
        return microbacia;
    },

    tImagens: async (form) => {
        const arquivo = campo<HTMLInputElement>(form, "arquivo").files?.[0];
        if (!arquivo) {
            throw new Error("Selecione um arquivo");
        }
        const imagem = await enviarImagem(arquivo);
        atualizarJson("tAnalisesCriar", "caminho_imagem", imagem.caminho_imagem);
        return imagem;
    },

    tAnalisesListar: (form) => {
        const filtros: AnaliseFiltros = {};
        const microbaciaId = campo<HTMLInputElement>(form, "microbacia_id").value;
        const status = campo<HTMLSelectElement>(form, "status").value;
        if (microbaciaId) filtros.microbacia_id = Number(microbaciaId);
        if (status) filtros.status = status as StatusAnalise;
        return listarAnalises(filtros);
    },

    tAnalisesCriar: async (form) => {
        const analise = await criarAnalise(lerJson<AnaliseRequest>(form));
        preencherId("tAnalisesStatus", analise.id);
        preencherId("tAnalisesResultado", analise.id);
        return analise;
    },

    tAnalisesStatus: (form) => consultarStatus(idDoCampo(form)),

    tAnalisesResultado: (form) => consultarResultado(idDoCampo(form)),
};

for (const [formId, chamada] of Object.entries(chamadas)) {
    const form = elemento<HTMLFormElement>(formId);
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        executar(form, chamada);
    });
}

// =========================
// RODAR TODOS OS GET SEM PARAMETRO
// =========================

const GETS_SEM_PARAMETRO = ["tHealth", "tModelos", "tMicrobaciasListar", "tAnalisesListar"];

const botaoTodos = elemento<HTMLButtonElement>("testarTodosGet");
botaoTodos.addEventListener("click", async () => {
    botaoTodos.disabled = true;
    // Em sequencia: o interceptor guarda o status da ultima resposta
    let falhas = 0;
    for (const formId of GETS_SEM_PARAMETRO) {
        const ok = await executar(elemento<HTMLFormElement>(formId), chamadas[formId]);
        if (!ok) falhas++;
    }
    botaoTodos.disabled = false;
    botaoTodos.textContent = falhas === 0 ? "Rodar todos os GET (todos OK)" : `Rodar todos os GET (${falhas} falha(s))`;
});
