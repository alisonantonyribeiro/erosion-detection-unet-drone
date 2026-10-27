import { mensagemDeErro } from "../api/client";
import { listarAnalises, listarMicrobacias } from "../api/endpoints";
import type { Analise, Microbacia } from "../api/types";
import { ROTULO_STATUS, elemento, formatarData } from "../utils/format";

const tabela = elemento<HTMLTableSectionElement>("tabelaAnalises");

function mensagem(texto: string, erro = false): void {
    const linha = tabela.insertRow();
    const celula = linha.insertCell();
    celula.colSpan = 4;
    celula.className = erro ? "table-message erro" : "table-message";
    celula.textContent = texto;
}

function linhaAnalise(analise: Analise, microbacia: Microbacia | undefined): HTMLTableRowElement {
    const linha = document.createElement("tr");

    linha.insertCell().textContent = formatarData(analise.criado_em);
    linha.insertCell().textContent = microbacia?.nome ?? `Microbacia #${analise.microbacia_id}`;

    const badge = document.createElement("span");
    badge.className = `status-badge status-${analise.status}`;
    badge.textContent = ROTULO_STATUS[analise.status];
    linha.insertCell().append(badge);

    const acoes = linha.insertCell();
    acoes.className = "actions-cell";
    const ver = document.createElement("a");
    ver.href = `relatorios.html?analise=${analise.id}`;
    ver.title = "Visualizar";
    ver.innerHTML = '<i class="fa-regular fa-eye"></i>';
    acoes.append(ver);

    return linha;
}

async function carregar(): Promise<void> {
    try {
        const [analises, microbacias] = await Promise.all([listarAnalises(), listarMicrobacias()]);
        const porId = new Map(microbacias.map((m) => [m.id, m]));

        tabela.replaceChildren();
        if (analises.length === 0) {
            mensagem("Nenhuma análise cadastrada ainda.");
            return;
        }

        // Mais recentes primeiro
        analises
            .sort((a, b) => b.criado_em.localeCompare(a.criado_em))
            .forEach((analise) => tabela.append(linhaAnalise(analise, porId.get(analise.microbacia_id))));
    } catch (erro) {
        tabela.replaceChildren();
        mensagem(mensagemDeErro(erro), true);
    }
}

carregar();
