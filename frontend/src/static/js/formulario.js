const form = document.getElementById("localidadeForm");

const modal = document.getElementById("modalConfirmacao");

const fecharModal = document.getElementById("fecharModal");
const cancelarModal = document.getElementById("cancelarModal");
const enviarFormulario = document.getElementById("enviarFormulario");

const imagem = document.getElementById("imagem");
const previewImagem = document.getElementById("previewImagem");


const pais = document.getElementById("pais");
const estado = document.getElementById("estado");
const cidade = document.getElementById("cidade");
const area = document.getElementById("area");
const latitude = document.getElementById("latitude");
const longitude = document.getElementById("longitude");
const descricao = document.getElementById("descricao");


// =========================
// CAMPOS DO MODAL
// =========================

const confirmPais = document.getElementById("confirmPais");
const confirmEstado = document.getElementById("confirmEstado");
const confirmCidade = document.getElementById("confirmCidade");
const confirmArea = document.getElementById("confirmArea");
const confirmLatitude = document.getElementById("confirmLatitude");
const confirmLongitude = document.getElementById("confirmLongitude");
const confirmDescricao = document.getElementById("confirmDescricao");


// =========================
// ABRIR MODAL
// =========================

form.addEventListener("submit", function (event) {

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


// =========================
// PREVIEW DA IMAGEM
// =========================

const arquivo = imagem.files[0];

if (arquivo) {

const leitor = new FileReader();

leitor.onload = function (event) {
previewImagem.src = event.target.result;
};

leitor.readAsDataURL(arquivo);
}


// Abre o modal
modal.classList.add("active");

// Impede o scroll da página
document.body.style.overflow = "hidden";
});


function fecharJanela() {

modal.classList.remove("active");

document.body.style.overflow = "";
}

fecharModal.addEventListener("click", fecharJanela);

cancelarModal.addEventListener("click", fecharJanela);

modal.addEventListener("click", function (event) {

if (event.target === modal) {
fecharJanela();
}

});


enviarFormulario.addEventListener("click", function () {

/*
* Agora sim o formulário é enviado.
*
* requestSubmit() mantém a validação e
* o comportamento normal do formulário.
*/

form.submit();

});