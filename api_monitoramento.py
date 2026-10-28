
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="API de Monitoramento RPA",
    version="1.0.0"
)


PROCESSOS_RPA = {
    "RPA-101": {
        "status": "CONCLUIDO",
        "descricao": "Consulta de veículos finalizada."
    },
    "RPA-102": {
        "status": "EM_EXECUCAO",
        "descricao": "Processando documentos."
    },
    "RPA-103": {
        "status": "ERRO",
        "descricao": "Falha de conexão com o serviço."
    }
}


LOGS_RPA = {
    "RPA-101": {
        "ultimo_evento": "Automação finalizada com sucesso.",
        "erro": None
    },
    "RPA-102": {
        "ultimo_evento": "Processando documentos.",
        "erro": None
    },
    "RPA-103": {
        "ultimo_evento": "Falha durante a execução.",
        "erro": "Timeout na conexão com o serviço externo."
    }
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rpas/{codigo}")
def consultar_status(codigo: str):

    codigo = codigo.strip().upper()

    processo = PROCESSOS_RPA.get(codigo)

    if processo is None:
        raise HTTPException(
            status_code=404,
            detail="Processo RPA não encontrado."
        )

    return {
        "codigo": codigo,
        **processo
    }


@app.get("/rpas/{codigo}/logs")
def consultar_logs(codigo: str):

    codigo = codigo.strip().upper()

    log = LOGS_RPA.get(codigo)

    if log is None:
        raise HTTPException(
            status_code=404,
            detail="Logs não encontrados."
        )

    return {
        "codigo": codigo,
        **log
    }
