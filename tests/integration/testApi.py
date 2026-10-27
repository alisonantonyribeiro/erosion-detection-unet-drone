import io

import numpy as np
import pytest
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from erosion.api import deps
from erosion.api.main import app
from erosion.api.router import analises as analises_router
from erosion.repositories.db import Base
from erosion.repositories.models import Modelo
from erosion.services import imagemService


@pytest.fixture
def sessao_teste():
    # banco em memoria por teste: nao toca no erosion.db real
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def tasks_enviadas(monkeypatch):
    # evita depender do Redis: so registra o que seria enviado ao worker
    enviadas = []
    monkeypatch.setattr(
        analises_router.celery_app, "send_task", lambda nome, args: enviadas.append((nome, args))
    )
    return enviadas


@pytest.fixture
def client(sessao_teste, tasks_enviadas, tmp_path, monkeypatch):
    def get_db_teste():
        db = sessao_teste()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(imagemService, "caminho_upload", lambda nome: tmp_path / nome)
    app.dependency_overrides[deps.get_db_session] = get_db_teste
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def modelo_id(sessao_teste):
    db = sessao_teste()
    modelo = Modelo(versao="v9", caminho_arquivo="modelo.h5")
    db.add(modelo)
    db.commit()
    yield modelo.id
    db.close()


def _geotiff_em_bytes(bandas: int = 4, tamanho: int = 512) -> bytes:
    buffer = io.BytesIO()
    dados = np.random.randint(0, 255, (bandas, tamanho, tamanho), dtype=np.uint8)
    with rasterio.MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff", height=tamanho, width=tamanho, count=bandas, dtype="uint8",
            crs="EPSG:31982", transform=from_origin(300000, 7300000, 0.037, 0.037),
        ) as dst:
            dst.write(dados)
        buffer.write(memfile.read())
    return buffer.getvalue()


# --- microbacias ---

def test_criar_microbacia_com_todos_os_campos(client):
    payload = {
        "nome": "Arroio Fundo", "area_ha": 59.24, "pais": "Brasil", "estado": "PR",
        "cidade": "Marechal Candido Rondon", "latitude": -24.55, "longitude": -54.05,
        "descricao": "Nascentes",
    }
    resposta = client.post("/microbacias", json=payload)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] > 0
    assert {k: corpo[k] for k in payload} == payload
    assert corpo["criado_em"] is not None


def test_criar_microbacia_so_com_nome(client):
    resposta = client.post("/microbacias", json={"nome": "Area 1"})

    assert resposta.status_code == 201
    assert resposta.json()["area_ha"] is None


@pytest.mark.parametrize(
    "payload",
    [{}, {"nome": ""}, {"nome": "x", "latitude": 91}, {"nome": "x", "longitude": -181}, {"nome": "x", "area_ha": -1}],
)
def test_criar_microbacia_payload_invalido_retorna_422(client, payload):
    assert client.post("/microbacias", json=payload).status_code == 422


def test_listar_microbacias_ordenado_por_nome(client):
    assert client.get("/microbacias").json() == []

    client.post("/microbacias", json={"nome": "Rio Verde"})
    client.post("/microbacias", json={"nome": "Arroio Fundo"})

    nomes = [m["nome"] for m in client.get("/microbacias").json()]
    assert nomes == ["Arroio Fundo", "Rio Verde"]


def test_buscar_microbacia_por_id(client):
    criada = client.post("/microbacias", json={"nome": "Arroio Fundo"}).json()

    resposta = client.get(f"/microbacias/{criada['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Arroio Fundo"


def test_buscar_microbacia_inexistente_retorna_404(client):
    assert client.get("/microbacias/999").status_code == 404


# --- analises ---

def test_listar_analises_vazio(client):
    resposta = client.get("/analises")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_criar_e_listar_analises_com_filtros(client, modelo_id, tasks_enviadas):
    bacia_a = client.post("/microbacias", json={"nome": "A"}).json()["id"]
    bacia_b = client.post("/microbacias", json={"nome": "B"}).json()["id"]

    primeira = client.post(
        "/analises", json={"microbacia_id": bacia_a, "modelo_id": modelo_id, "caminho_imagem": "a.tif"}
    )
    client.post("/analises", json={"microbacia_id": bacia_b, "modelo_id": modelo_id, "caminho_imagem": "b.tif"})

    assert primeira.status_code == 200
    assert tasks_enviadas[0] == ("processar_analise", [primeira.json()["id"], "a.tif"])

    todas = client.get("/analises").json()
    assert [a["microbacia_id"] for a in todas] == [bacia_b, bacia_a]  # mais recente primeiro

    so_a = client.get("/analises", params={"microbacia_id": bacia_a}).json()
    assert [a["id"] for a in so_a] == [primeira.json()["id"]]

    assert len(client.get("/analises", params={"status": "pendente"}).json()) == 2
    assert client.get("/analises", params={"status": "concluida"}).json() == []


def test_listar_analises_status_invalido_retorna_422(client):
    assert client.get("/analises", params={"status": "qualquer"}).status_code == 422


def test_criar_analise_com_microbacia_inexistente_retorna_404(client, modelo_id, tasks_enviadas):
    resposta = client.post(
        "/analises", json={"microbacia_id": 999, "modelo_id": modelo_id, "caminho_imagem": "a.tif"}
    )

    assert resposta.status_code == 404
    assert "Microbacia" in resposta.json()["detail"]
    assert tasks_enviadas == []
    assert client.get("/analises").json() == []


def test_criar_analise_com_modelo_inexistente_retorna_404(client, tasks_enviadas):
    bacia = client.post("/microbacias", json={"nome": "A"}).json()["id"]

    resposta = client.post("/analises", json={"microbacia_id": bacia, "modelo_id": 999, "caminho_imagem": "a.tif"})

    assert resposta.status_code == 404
    assert "Modelo" in resposta.json()["detail"]
    assert tasks_enviadas == []


# --- imagens ---

def test_upload_geotiff_valido(client, tmp_path):
    resposta = client.post(
        "/imagens", files={"arquivo": ("orto.tif", _geotiff_em_bytes(), "image/tiff")}
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome_original"] == "orto.tif"
    assert (corpo["bandas"], corpo["largura"], corpo["altura"]) == (4, 512, 512)
    assert corpo["crs"] == "EPSG:31982"
    assert corpo["caminho_imagem"].endswith(".tif")
    assert "\\" not in corpo["caminho_imagem"]
    with rasterio.open(corpo["caminho_imagem"]) as src:
        assert src.count == 4


def test_caminho_do_upload_pode_ser_colado_no_post_analises(client, modelo_id, tasks_enviadas):
    # fluxo real do Postman: o caminho entra cru dentro de um JSON escrito a mao
    caminho = client.post(
        "/imagens", files={"arquivo": ("orto.tif", _geotiff_em_bytes(), "image/tiff")}
    ).json()["caminho_imagem"]
    bacia = client.post("/microbacias", json={"nome": "A"}).json()["id"]

    corpo_json = f'{{"microbacia_id": {bacia}, "modelo_id": {modelo_id}, "caminho_imagem": "{caminho}"}}'
    resposta = client.post("/analises", content=corpo_json, headers={"Content-Type": "application/json"})

    assert resposta.status_code == 200
    assert tasks_enviadas[-1][1][1] == caminho


def test_upload_imagem_rgb_sem_nir_retorna_422_e_nao_guarda(client, tmp_path):
    resposta = client.post(
        "/imagens", files={"arquivo": ("rgb.tif", _geotiff_em_bytes(bandas=3), "image/tiff")}
    )

    assert resposta.status_code == 422
    assert "3 banda" in resposta.json()["detail"]
    assert list(tmp_path.glob("*.tif")) == []


def test_upload_imagem_menor_que_tile_retorna_422(client):
    resposta = client.post(
        "/imagens", files={"arquivo": ("pequena.tif", _geotiff_em_bytes(tamanho=256), "image/tiff")}
    )

    assert resposta.status_code == 422
    assert "menor que o tile" in resposta.json()["detail"]


def test_upload_extensao_errada_retorna_422(client):
    resposta = client.post("/imagens", files={"arquivo": ("foto.jpg", b"jpeg", "image/jpeg")})

    assert resposta.status_code == 422
    assert ".jpg" in resposta.json()["detail"]


def test_upload_tif_corrompido_retorna_422_e_nao_guarda(client, tmp_path):
    resposta = client.post("/imagens", files={"arquivo": ("ruim.tif", b"nao sou tiff", "image/tiff")})

    assert resposta.status_code == 422
    assert list(tmp_path.glob("*.tif")) == []


def test_upload_sem_arquivo_retorna_422(client):
    assert client.post("/imagens").status_code == 422
