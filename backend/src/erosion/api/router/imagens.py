from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from erosion.services import imagemService

router = APIRouter(prefix="/imagens", tags=["imagens"])


class ImagemResponse(BaseModel):
    caminho_imagem: str
    nome_original: str
    bandas: int
    largura: int
    altura: int
    crs: str | None


@router.post("", response_model=ImagemResponse, status_code=status.HTTP_201_CREATED)
def enviar_imagem(arquivo: UploadFile = File(...)):
    """Recebe o ortomosaico; o `caminho_imagem` devolvido vai no POST /analises."""
    try:
        return imagemService.salvar_upload(arquivo.file, arquivo.filename or "")
    except imagemService.ImagemInvalidaError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
