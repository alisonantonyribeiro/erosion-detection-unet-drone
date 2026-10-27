import { mensagemDeErro } from "../api/client";
import { listarMicrobacias } from "../api/endpoints";
import type { Microbacia } from "../api/types";
import { elemento } from "../utils/format";

const grid = elemento<HTMLDivElement>("areaGrid");
const adicionar = elemento<HTMLAnchorElement>("areaAdicionar");
const mensagem = elemento<HTMLParagraphElement>("areaMensagem");

const TOTAL_THUMBS = 5; // .thumb-1 a .thumb-5 em carregar-projeto.css

function cardMicrobacia(microbacia: Microbacia, indice: number): HTMLAnchorElement {
    const card = document.createElement("a");
    card.className = "area-card";
    card.href = `relatorios.html?microbacia=${microbacia.id}`;

    const thumb = document.createElement("div");
    thumb.className = `area-thumb thumb-${(indice % TOTAL_THUMBS) + 1}`;

    const info = document.createElement("div");
    info.className = "area-info";
    const nome = document.createElement("strong");
    nome.textContent = microbacia.nome;
    const local = document.createElement("span");
    local.textContent = [microbacia.cidade, microbacia.estado].filter(Boolean).join(" - ") || "Local não informado";
    info.append(nome, local);

    card.append(thumb, info);
    return card;
}

async function carregar(): Promise<void> {
    try {
        const microbacias = await listarMicrobacias();
        microbacias.forEach((m, i) => grid.insertBefore(cardMicrobacia(m, i), adicionar));

        mensagem.hidden = microbacias.length > 0;
        mensagem.textContent = "Nenhuma área cadastrada ainda. Comece por um novo diagnóstico.";
    } catch (erro) {
        mensagem.textContent = mensagemDeErro(erro);
        mensagem.classList.add("erro");
    }
}

carregar();
