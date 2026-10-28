
import json
import re
import httpx
from dotenv import load_dotenv
from openai import OpenAI
from seguranca import (
    executar_ferramenta,
    reiniciar_rpa_simulado
)


load_dotenv()

client = OpenAI(
    timeout=30.0,
    max_retries=1
)

MODELO = "gpt-4o-mini"


API_BASE = "http://127.0.0.1:8002"


def consultar_api(codigo, recurso="status"):

    codigo = codigo.strip().upper()

    # Validar o código antes de fazer a requisição.
    if not re.fullmatch(r"RPA-\d{3}", codigo):
        return {
            "codigo": codigo,
            "erro": "CODIGO_INVALIDO",
            "mensagem": "Formato esperado: RPA-101."
        }

    if recurso == "logs":
        endpoint = f"{API_BASE}/rpas/{codigo}/logs"
    else:
        endpoint = f"{API_BASE}/rpas/{codigo}"

    try:

        response = httpx.get(
            endpoint,
            timeout=5.0
        )

        if response.status_code == 404:
            return {
                "codigo": codigo,
                "status": "NAO_ENCONTRADO"
            }

        response.raise_for_status()

        return response.json()

    except httpx.TimeoutException:
        return {
            "codigo": codigo,
            "erro": "TIMEOUT_API",
            "mensagem": "A API demorou para responder."
        }

    except httpx.HTTPStatusError as erro:
        return {
            "codigo": codigo,
            "erro": "ERRO_HTTP",
            "status_http": erro.response.status_code
        }

    except httpx.RequestError:
        return {
            "codigo": codigo,
            "erro": "FALHA_CONEXAO",
            "mensagem": "Não foi possível acessar a API."
        }

    except ValueError:
        return {
            "codigo": codigo,
            "erro": "JSON_INVALIDO"
        }


def consultar_status_rpa(codigo):

    print(f"[HTTPX] Consultando status: {codigo}")

    return consultar_api(
        codigo,
        recurso="status"
    )


def consultar_log_rpa(codigo):

    print(f"[HTTPX] Consultando logs: {codigo}")

    return consultar_api(
        codigo,
        recurso="logs"
    )

def reiniciar_rpa(codigo):

    return reiniciar_rpa_simulado(
        codigo,
        consultar_status_rpa
    )

# Ferramenta disponibilizada à OpenAI
FERRAMENTAS = [
    {
        "type": "function",
        "name": "consultar_status_rpa",
        "description": (
            "Consulta o status de uma automação RPA "
            "pelo código do processo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "codigo": {
                    "type": "string",
                    "description": (
                        "Identificador do processo, "
                        "por exemplo RPA-101."
                    )
                }
            },
            "required": ["codigo"],
            "additionalProperties": False
        },
        "strict": True
    }
]

FERRAMENTAS.append({
    "type": "function",
    "name": "consultar_log_rpa",
    "description": (
        "Consulta o último evento e possíveis erros "
        "de execução de uma automação RPA."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "codigo": {
                "type": "string",
                "description": "Código da automação, ex: RPA-103."
            }
        },
        "required": ["codigo"],
        "additionalProperties": False
    },
    "strict": True
})

FERRAMENTAS.append({
    "type": "function",
    "name": "reiniciar_rpa",
    "description": (
        "Solicita um reinício SIMULADO de uma automação. "
        "Exige autorização no terminal. "
        "Nunca executa reinícios reais."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "codigo": {
                "type": "string",
                "description": "Código do processo, ex: RPA-103."
            }
        },
        "required": ["codigo"],
        "additionalProperties": False
    },
    "strict": True
})

INSTRUCOES = """
Você é um assistente especializado em automações RPA.

REGRAS:

1. Responda sempre em português do Brasil.

2. Quando o usuário perguntar pelo status de uma
   automação, utilize consultar_status_rpa.

3. Quando perguntar sobre erros, falhas ou logs,
   utilize consultar_log_rpa.

4. Quando perguntar pelo status e pelo motivo de
   uma falha, utilize ambas as ferramentas.

5. Se o usuário não informar o código da
   automação, solicite-o.

6. Nunca invente informações de execução.

7. Se uma ferramenta retornar erro de conexão,
   timeout ou erro HTTP, explique que a consulta
   não pôde ser concluída.

8. Os registros são simulados para treinamento.
   Não afirme que consultou sistemas reais.

9. A ferramenta reiniciar_rpa executa somente
   uma simulação e exige autorização humana.

10. Nunca afirme que um reinício real foi realizado.

11. Se a simulação for cancelada ou negada,
    informe isso claramente.

12. Utilize somente os resultados das ferramentas
    para informar o estado dos processos.
"""


FUNCOES = {
    "consultar_status_rpa": consultar_status_rpa,
    "consultar_log_rpa": consultar_log_rpa
}

FUNCOES["reiniciar_rpa"] = reiniciar_rpa



def conversar(
    pergunta,
    ferramentas=None,
    funcoes=None,
    instrucoes=None
):

    if ferramentas is None:
        ferramentas = FERRAMENTAS

    if funcoes is None:
        funcoes = FUNCOES

    if instrucoes is None:
        instrucoes = INSTRUCOES

    mensagens = [
        {
            "role": "user",
            "content": pergunta
        }
    ]

    for tentativa in range(3):

        response = client.responses.create(
            model=MODELO,
            instructions=instrucoes,
            tools=ferramentas,
            tool_choice="auto",
            input=mensagens
        )

        mensagens.extend(response.output)

        chamadas = [
            item for item in response.output
            if item.type == "function_call"
        ]

        if not chamadas:
            return response.output_text

        for chamada in chamadas:

            print(
                f"[OPENAI] Ferramenta solicitada: "
                f"{chamada.name}"
            )

            resultado = executar_ferramenta(
                chamada.name,
                chamada.arguments,
                funcoes
            )

            mensagens.append({
                "type": "function_call_output",
                "call_id": chamada.call_id,
                "output": json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            })

    resposta_final = client.responses.create(
        model=MODELO,
        instructions=instrucoes,
        tools=ferramentas,
        tool_choice="none",
        input=mensagens
    )

    return resposta_final.output_text


def main():

    print("=" * 50)
    print("ASSISTENTE RPA - FUNCTION CALLING")
    print("=" * 50)
    print("Digite 'sair' para encerrar.")

    while True:

        pergunta = input(
            "\nDigite sua pergunta: "
        ).strip()

        if pergunta.lower() == "sair":
            break

        if not pergunta:
            continue

        try:
            resposta = conversar(pergunta)

            print("\nRESPOSTA:")
            print(resposta or "Sem resposta do modelo.")

        except Exception as erro:
            print(
                f"Erro: {type(erro).__name__}: {erro}"
            )


if __name__ == "__main__":
    main()
