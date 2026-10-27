import { mensagemDeErro } from "../api/client";
import { buscarMicrobacia, consultarResultado, consultarStatus, listarAnalises } from "../api/endpoints";
import type { Analise, Microbacia, Resultado, StatusResposta } from "../api/types";
import { CLASSES, ROTULO_STATUS, elemento, formatarData, formatarNumero, idDaUrl, rotuloClasse } from "../utils/format";

const titulo = elemento<HTMLHeadingElement>("tituloResultado");
const mensagem = elemento<HTMLParagraphElement>("mensagemResultado");
const listaClasses = elemento<HTMLUListElement>("listaClasses");
const listaIndicadores = elemento<HTMLUListElement>("listaIndicadores");
const relatorioArea = elemento<HTMLSpanElement>("relatorioArea");
const relatorioData = elemento<HTMLSpanElement>("relatorioData");
const relatorioResultados = elemento<HTMLUListElement>("relatorioResultados");

const maisRecente = (a: Analise, b: Analise) => (a.criado_em > b.criado_em ? a : b);

/**
 * Qual analise mostrar:
 *  ?analise=ID     -> essa analise (vindo do Historico)
 *  ?microbacia=ID  -> a concluida mais recente da microbacia (vindo de Carregar Projeto)
 *  sem parametro   -> a concluida mais recente de todas
 */
async function escolherAnalise(): Promise<Analise | null> {
    const analiseId = idDaUrl("analise");
    if (analiseId !== null) {
        const todas = await listarAnalises();
        return todas.find((a) => a.id === analiseId) ?? null;
    }

    const microbaciaId = idDaUrl("microbacia");
    const filtro = microbaciaId !== null ? { microbacia_id: microbaciaId } : {};
    const analises = await listarAnalises(filtro);
    if (analises.length === 0) {
        return null;
    }
    const concluidas = analises.filter((a) => a.status === "concluida");
    return (concluidas.length > 0 ? concluidas : analises).reduce(maisRecente);
}

function itemIndicador(rotulo: string, valor: string): HTMLLIElement {
    const li = document.createElement("li");
    const span = document.createElement("span");
    span.textContent = rotulo;
    const strong = document.createElement("strong");
    strong.textContent = valor;
    li.append(span, strong);
    return li;
}

function itemTexto(texto: string): HTMLLIElement {
    const li = document.createElement("li");
    li.textContent = texto;
    return li;
}

function mostrarMensagem(texto: string, erro = false): void {
    mensagem.textContent = texto;
    mensagem.classList.toggle("erro", erro);
    mensagem.hidden = false;
}

function renderizarResultado(resultado: Resultado): void {
    const classes = Object.entries(resultado.areas_por_classe);
    const totalHa = classes.reduce((soma, [, area]) => soma + area.hectares, 0);

    listaClasses.replaceChildren(
        ...classes.map(([nome]) => {
            const li = document.createElement("li");
            const dot = document.createElement("span");
            dot.className = "dot";
            dot.style.backgroundColor = CLASSES[nome]?.cor ?? "var(--text-muted)";
            li.append(dot, rotuloClasse(nome));
            return li;
        }),
    );

    const formatar = (ha: number, pct: number) => `${formatarNumero(ha)} ha (${formatarNumero(pct, 1)}%)`;

    listaIndicadores.replaceChildren(
        itemIndicador("Área Total", `${formatarNumero(totalHa)} ha`),
        ...classes.map(([nome, area]) => itemIndicador(rotuloClasse(nome), formatar(area.hectares, area.percentual))),
    );

    relatorioResultados.replaceChildren(
        itemTexto(`Área total analisada: ${formatarNumero(totalHa)} ha`),
        ...classes.map(([nome, area]) => itemTexto(`${rotuloClasse(nome)}: ${formatar(area.hectares, area.percentual)}`)),
    );
}

function renderizarPendente(status: StatusResposta): void {
    const texto =
        status.status === "erro"
            ? `A análise #${status.id} falhou: ${status.mensagem_erro ?? "erro desconhecido"}`
            : `A análise #${status.id} ainda está ${ROTULO_STATUS[status.status].toLowerCase()}. Recarregue a página em instantes.`;
    mostrarMensagem(texto, status.status === "erro");
    listaIndicadores.replaceChildren(itemIndicador("Status", ROTULO_STATUS[status.status]));
}

function renderizarCabecalho(analise: Analise, microbacia: Microbacia): void {
    titulo.textContent = `Resultados - ${microbacia.nome}`;
    const local = [microbacia.cidade, microbacia.estado].filter(Boolean).join(" - ");
    relatorioArea.textContent = local ? `${microbacia.nome} (${local})` : microbacia.nome;
    relatorioData.textContent = formatarData(analise.concluido_em ?? analise.criado_em);
}

async function carregar(): Promise<void> {
    try {
        const analise = await escolherAnalise();
        if (analise === null) {
            mostrarMensagem("Nenhuma análise encontrada. Crie um novo diagnóstico para ver resultados.");
            return;
        }

        const [microbacia, status] = await Promise.all([
            buscarMicrobacia(analise.microbacia_id),
            consultarStatus(analise.id),
        ]);
        renderizarCabecalho(analise, microbacia);

        if (status.status !== "concluida") {
            renderizarPendente(status);
            return;
        }

        renderizarResultado(await consultarResultado(analise.id));
        mensagem.hidden = true;
    } catch (erro) {
        mostrarMensagem(mensagemDeErro(erro), true);
    }
}

carregar();
