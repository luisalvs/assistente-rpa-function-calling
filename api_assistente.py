
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import (
    APITimeoutError,
    RateLimitError,
    AuthenticationError,
    APIConnectionError,
    OpenAIError
)
from main import (
    conversar,
    FERRAMENTAS,
    consultar_status_rpa,
    consultar_log_rpa
)


app = FastAPI(
    title="Assistente Inteligente RPA",
    version="1.0.0"
)


# Somente ferramentas de consulta
FERRAMENTAS_PERMITIDAS = {
    "consultar_status_rpa",
    "consultar_log_rpa"
}

FERRAMENTAS_API = [
    ferramenta
    for ferramenta in FERRAMENTAS
    if ferramenta["name"] in FERRAMENTAS_PERMITIDAS
]

FUNCOES_API = {
    "consultar_status_rpa": consultar_status_rpa,
    "consultar_log_rpa": consultar_log_rpa
}


INSTRUCOES_API = """

Você é um assistente de monitoramento de automações RPA.

Responda sempre em português do Brasil.

Utilize consultar_status_rpa para consultar o status
de uma automação.

Utilize consultar_log_rpa para consultar falhas e logs.

Quando necessário, utilize as duas ferramentas.

Se o código da automação não for informado,
solicite-o ao usuário.

Nunca invente resultados de execução.

Os dados pertencem a uma API de treinamento
com informações simuladas.

Você não possui ferramentas para reiniciar, alterar,
excluir ou executar automações.

Se alguém solicitar essas ações, informe que
não estão disponíveis nesta interface.

Se uma consulta falhar por timeout ou conexão,
explique que não foi possível consultar os dados.

"""


class PerguntaEntrada(BaseModel):
    pergunta: str = Field(
        min_length=10,
        max_length=1000
    )


class RespostaAssistente(BaseModel):
    resposta: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ferramentas_disponiveis": len(FERRAMENTAS_API)
    }


@app.post(
    "/perguntar",
    response_model=RespostaAssistente
)
def perguntar(dados: PerguntaEntrada):

    try:
        resposta = conversar(
            pergunta=dados.pergunta,
            ferramentas=FERRAMENTAS_API,
            funcoes=FUNCOES_API,
            instrucoes=INSTRUCOES_API
        )

    except APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Tempo limite excedido na OpenAI."
        )

    except RateLimitError:
        raise HTTPException(
            status_code=503,
            detail="Limite de requisições atingido."
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=502,
            detail="Erro de autenticação com a OpenAI."
        )

    except APIConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Falha de conexão com a OpenAI."
        )

    except OpenAIError:
        raise HTTPException(
            status_code=502,
            detail="Erro ao processar a solicitação."
        )

    if not resposta or not resposta.strip():
        raise HTTPException(
            status_code=502,
            detail="O modelo não retornou uma resposta."
        )

    return RespostaAssistente(
        resposta=resposta
    )
