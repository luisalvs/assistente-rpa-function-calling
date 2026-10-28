
import httpx
from fastapi.testclient import TestClient
from openai import APITimeoutError
import api_assistente
from seguranca import executar_ferramenta


client = TestClient(api_assistente.app)


def test_health():

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ferramentas_disponiveis"] == 2


def test_pergunta_sucesso(monkeypatch):

    def mock_conversar(
        pergunta,
        ferramentas,
        funcoes,
        instrucoes
    ):

        assert "RPA-101" in pergunta

        assert len(ferramentas) == 2
        assert "reiniciar_rpa" not in funcoes

        return "A RPA-101 foi concluída."

    monkeypatch.setattr(
        api_assistente,
        "conversar",
        mock_conversar
    )

    response = client.post(
        "/perguntar",
        json={
            "pergunta": "Qual é o status da RPA-101?"
        }
    )

    assert response.status_code == 200
    assert "concluída" in response.json()["resposta"]


def test_pergunta_curta():

    response = client.post(
        "/perguntar",
        json={"pergunta": "Teste"}
    )

    assert response.status_code == 422


def test_campo_obrigatorio():

    response = client.post(
        "/perguntar",
        json={}
    )

    assert response.status_code == 422


def test_ferramenta_sensivel_bloqueada():

    resultado = executar_ferramenta(
        "reiniciar_rpa",
        '{"codigo":"RPA-103"}',
        api_assistente.FUNCOES_API
    )

    assert resultado["erro"] == (
        "FERRAMENTA_NAO_AUTORIZADA"
    )

    nomes = [
        item["name"]
        for item in api_assistente.FERRAMENTAS_API
    ]

    assert "reiniciar_rpa" not in nomes


def test_timeout_openai(monkeypatch):

    def mock_timeout(
        pergunta,
        ferramentas,
        funcoes,
        instrucoes
    ):

        raise APITimeoutError(
            request=httpx.Request(
                "POST",
                "https://api.openai.com/v1/responses"
            )
        )

    monkeypatch.setattr(
        api_assistente,
        "conversar",
        mock_timeout
    )

    response = client.post(
        "/perguntar",
        json={
            "pergunta": "Qual é o status da RPA-101?"
        }
    )

    assert response.status_code == 504
