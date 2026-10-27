import { mensagemDeErro } from "../api/client";
import { criarAnalise, criarMicrobacia, enviarImagem, listarModelos } from "../api/endpoints";
import type { MicrobaciaRequest } from "../api/types";
import { elemento } from "../utils/format";

const form = elemento<HTMLFormElement>("localidadeForm");

const modal = elemento<HTMLDivElement>("modalConfirmacao");

const fecharModal = elemento<HTMLButtonElement>("fecharModal");
const cancelarModal = elemento<HTMLButtonElement>("cancelarModal");
const enviarFormulario = elemento<HTMLButtonElement>("enviarFormulario");
const modalErro = elemento<HTMLParagraphElement>("modalErro");

const imagem = elemento<HTMLInputElement>("imagem");
const previewImagem = elemento<HTMLDivElement>("previewImagem");
const previewNome = elemento<HTMLSpanElement>("previewNome");

const pais = elemento<HTMLInputElement>("pais");
const estado = elemento<HTMLInputElement>("estado");
const cidade = elemento<HTMLInputElement>("cidade");
const area = elemento<HTMLInputElement>("area");
const latitude = elemento<HTMLInputElement>("latitude");
const longitude = elemento<HTMLInputElement>("longitude");
const descricao = elemento<HTMLTextAreaElement>("descricao");

// =========================
// CAMPOS DO MODAL
// =========================

const confirmPais = elemento("confirmPais");
const confirmEstado = elemento("confirmEstado");
const confirmCidade = elemento("confirmCidade");
const confirmArea = elemento("confirmArea");
const confirmLatitude = elemento("confirmLatitude");
const confirmLongitude = elemento("confirmLongitude");
const confirmDescricao = elemento("confirmDescricao");

let urlPreview: string | null = null;

// =========================
// ABRIR MODAL
// =========================

form.addEventListener("submit", (event) => {
    // Impede o envio imediato
    event.preventDefault();

    // Validação nativa do HTML
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    // Preenche os dados do modal
    confirmPais.textContent = pais.value;
    confirmEstado.textContent = estado.value;
    confirmCidade.textContent = cidade.value;
    confirmArea.textContent = area.value;
    confirmLatitude.textContent = latitude.value;
    confirmLongitude.textContent = longitude.value;
    confirmDescricao.textContent = descricao.value;

    mostrarPreview(imagem.files?.[0]);
    mostrarErro(null);

    // Abre o modal
    modal.classList.add("active");

    // Impede o scroll da página
    document.body.style.overflow = "hidden";
});

// =========================
// PREVIEW DA IMAGEM
// =========================

// GeoTIFF nao renderiza em <img> na maioria dos navegadores: o nome do arquivo
// fica visivel e a <img> so entra no lugar se o navegador conseguir decodificar
function mostrarPreview(arquivo: File | undefined): void {
    previewImagem.querySelector("img")?.remove();
    if (urlPreview) {
        URL.revokeObjectURL(urlPreview);
        urlPreview = null;
    }
    previewNome.textContent = arquivo?.name ?? "";
    previewNome.hidden = false;

    if (arquivo) {
        urlPreview = URL.createObjectURL(arquivo);
        const img = new Image();
        img.alt = "Imagem selecionada";
        img.addEventListener("load", () => {
            previewNome.hidden = true;
            previewImagem.append(img);
        });
        img.src = urlPreview;
    }
}

function fecharJanela(): void {
    if (enviarFormulario.disabled) {
        return; // nao deixa fechar no meio do envio
    }
    modal.classList.remove("active");
    document.body.style.overflow = "";
}

fecharModal.addEventListener("click", fecharJanela);

cancelarModal.addEventListener("click", fecharJanela);

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        fecharJanela();
    }
});

// =========================
// ENVIO PARA A API
// =========================

function numeroOuNulo(input: HTMLInputElement): number | null {
    return input.value === "" ? null : Number(input.value);
}

function textoOuNulo(valor: string): string | null {
    return valor.trim() === "" ? null : valor.trim();
}

function mostrarErro(mensagem: string | null): void {
    modalErro.textContent = mensagem ?? "";
    modalErro.hidden = mensagem === null;
}

function definirEnviando(texto: string | null): void {
    enviarFormulario.disabled = texto !== null;
    cancelarModal.disabled = texto !== null;
    enviarFormulario.textContent = texto ?? "Enviar";
}

enviarFormulario.addEventListener("click", async () => {
    const arquivo = imagem.files?.[0];
    if (!arquivo) {
        mostrarErro("Selecione a imagem (GeoTIFF) antes de enviar.");
        return;
    }

    const microbacia: MicrobaciaRequest = {
        nome: area.value.trim(),
        pais: textoOuNulo(pais.value),
        estado: textoOuNulo(estado.value),
        cidade: textoOuNulo(cidade.value),
        latitude: numeroOuNulo(latitude),
        longitude: numeroOuNulo(longitude),
        descricao: textoOuNulo(descricao.value),
    };

    mostrarErro(null);
    try {
        definirEnviando("Verificando modelo...");
        const modelos = await listarModelos();
        if (modelos.length === 0) {
            throw new Error("Nenhum modelo cadastrado na API. Cadastre um modelo antes de criar a análise.");
        }
        // Usa o modelo mais recente
        const modelo = modelos.reduce((a, b) => (a.criado_em > b.criado_em ? a : b));

        // Imagem primeiro: se o GeoTIFF for invalido, nao sobra microbacia orfa no banco
        definirEnviando("Enviando imagem...");
        const { caminho_imagem } = await enviarImagem(arquivo);

        definirEnviando("Cadastrando área...");
        const { id: microbacia_id } = await criarMicrobacia(microbacia);

        definirEnviando("Criando análise...");
        await criarAnalise({ microbacia_id, modelo_id: modelo.id, caminho_imagem });

        window.location.href = "historico.html";
    } catch (erro) {
        mostrarErro(mensagemDeErro(erro));
        definirEnviando(null);
    }
});
