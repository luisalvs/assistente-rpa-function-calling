
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator
)


class ParametrosRPA(BaseModel):

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(
        pattern=r"^RPA-\d{3}$"
    )

    @field_validator("codigo", mode="before")
    @classmethod
    def normalizar_codigo(cls, valor):

        if isinstance(valor, str):
            return valor.strip().upper()

        return valor


def executar_ferramenta(nome, argumentos_json, funcoes):

    # Somente funções previamente autorizadas.
    funcao = funcoes.get(nome)

    if funcao is None:
        return {
            "erro": "FERRAMENTA_NAO_AUTORIZADA"
        }

    try:

        parametros = ParametrosRPA.model_validate_json(
            argumentos_json
        )

    except (ValidationError, TypeError):

        return {
            "erro": "ARGUMENTOS_INVALIDOS",
            "mensagem": "Código RPA inválido."
        }

    return funcao(parametros.codigo)


def reiniciar_rpa_simulado(codigo, consultar_status):

    # Permissão fixa apenas para esta demonstração.
    if codigo != "RPA-103":
        return {
            "codigo": codigo,
            "status": "NEGADO",
            "reinicio_realizado": False,
            "mensagem": "Operação não autorizada."
        }

    # Confirma que a API está acessível e o processo
    # realmente apresenta status ERRO.
    dados = consultar_status(codigo)

    if dados.get("status") != "ERRO":
        return {
            "codigo": codigo,
            "status": "NEGADO",
            "reinicio_realizado": False,
            "mensagem": (
                "Processo não está em erro ou "
                "a consulta à API falhou."
            )
        }

    print("\n[SEGURANÇA] Ação sensível solicitada.")
    print(f"Processo: {codigo}")
    print("Operação: REINÍCIO SIMULADO")

    confirmacao = input(
        "Autoriza a simulação? [sim/N]: "
    ).strip().lower()

    if confirmacao != "sim":
        return {
            "codigo": codigo,
            "status": "CANCELADO",
            "reinicio_realizado": False,
            "mensagem": "Operação cancelada."
        }

    print("[SIMULAÇÃO] Aprovação registrada.")

    return {
        "codigo": codigo,
        "status": "SIMULACAO_APROVADA",
        "reinicio_realizado": False,
        "mensagem": (
            "Simulação concluída. "
            "Nenhum processo real foi reiniciado."
        )
    }
