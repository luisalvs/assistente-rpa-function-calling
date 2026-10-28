# Assistente RPA Inteligente — Function Calling com Python e FastAPI

API de monitoramento de automações RPA que utiliza **OpenAI Function Calling** para interpretar perguntas em linguagem natural, selecionar ferramentas Python e consultar informações de execução por meio de uma API REST.

Projeto desenvolvido para estudo de **Engenharia de IA aplicada à automação**, integrando **Python, OpenAI, FastAPI, HTTPX, Pydantic e Pytest**.

> **Projeto demonstrativo:** todos os processos RPA e seus logs são simulados. Não há integração com sistemas corporativos reais, e nenhum processo é reiniciado de verdade.

## Funcionalidades

- Consulta do **status** de uma automação a partir do seu código (ex.: `RPA-101`).
- Consulta de **logs e motivos de falhas** (ex.: `RPA-103`).
- Seleção automática de uma ou mais ferramentas pelo modelo de IA.
- Comunicação entre dois serviços REST usando HTTPX.
- Validação de parâmetros com **Pydantic**.
- Tratamento de códigos inexistentes, falhas HTTP, indisponibilidade e timeout.
- Lista explícita de funções autorizadas (allowlist).
- **Reinício simulado** com confirmação humana, disponível apenas no terminal.
- API de perguntas com **somente ferramentas de leitura**.
- Testes automatizados com Pytest e FastAPI TestClient.

## Tecnologias

| Tecnologia | Utilização |
| --- | --- |
| Python 3.13 | Linguagem principal (versão usada nos testes) |
| OpenAI Responses API | Interpretação de perguntas e Function Calling |
| FastAPI | APIs REST de monitoramento e assistente |
| HTTPX | Comunicação HTTP entre serviços |
| Pydantic | Validação de entradas e argumentos das ferramentas |
| python-dotenv | Leitura da chave de API em `.env` |
| Pytest | Testes automatizados |

## Arquitetura

```text
                      Usuário / Postman
                             |
                     POST /perguntar
                             |
                   API do Assistente
                    FastAPI :8003
                             |
                      OpenAI (LLM)
                             |
              Function Calling / validação
                   /                \
                  v                  v
        consultar_status_rpa   consultar_log_rpa
                  \                  /
                   \---- HTTPX -----/
                             |
                   API de Monitoramento
                    FastAPI :8002
                             |
                    Dados simulados
```

**Separação de permissões:** a API HTTP registra apenas `consultar_status_rpa` e `consultar_log_rpa`. A ferramenta `reiniciar_rpa` só existe na interface de terminal e solicita uma confirmação para **simulação**, sem reiniciar processos reais.

## Estrutura do projeto

```text
assistente-rpa-function-calling/
├── main.py                 # Assistente, ferramentas e interface de terminal
├── seguranca.py            # Validação e regras de autorização
├── api_monitoramento.py    # API REST dos processos simulados (:8002)
├── api_assistente.py       # API REST para perguntas à IA (:8003)
├── tests/
│   └── test_api_assistente.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Como executar localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/luisalvs/assistente-rpa-function-calling.git
cd assistente-rpa-function-calling
```

> O endereço acima ficará disponível depois que o repositório for criado e publicado no GitHub.

### 2. Criar ambiente virtual e instalar dependências

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Configurar a chave da OpenAI

```bash
cp .env.example .env
```

Edite `.env` e defina sua chave:

```dotenv
OPENAI_API_KEY=sua_chave_aqui
```

**Nunca publique `.env`, chaves, tokens ou credenciais.** A variável de ambiente é carregada pelo `python-dotenv`.

O modelo configurado em `main.py` é `gpt-4o-mini`; chamadas ao modelo podem gerar cobranças conforme sua conta e uso.

### 4. Iniciar a API de monitoramento

No **terminal 1**:

```bash
python -m uvicorn api_monitoramento:app --reload --host 127.0.0.1 --port 8002
```

### 5. Iniciar a API do assistente

No **terminal 2** (com o ambiente virtual ativado):

```bash
python -m uvicorn api_assistente:app --reload --host 127.0.0.1 --port 8003
```

Documentação interativa do assistente: <http://127.0.0.1:8003/docs>.

### 6. Opcional: utilizar o assistente pelo terminal

```bash
python main.py
```

A interface de terminal inclui o fluxo de reinício **simulado** com autorização via `input()`; essa função **não** está disponível na API HTTP.

## Endpoints

### API de monitoramento — porta 8002

| Método | Endpoint | Descrição |
| --- | --- | --- |
| GET | `/health` | Verifica disponibilidade |
| GET | `/rpas/{codigo}` | Retorna o status do processo |
| GET | `/rpas/{codigo}/logs` | Retorna o último evento e possível erro |

Exemplo:

```bash
curl http://127.0.0.1:8002/rpas/RPA-103
```

Resposta simulada:

```json
{
  "codigo": "RPA-103",
  "status": "ERRO",
  "descricao": "Falha de conexão com o serviço."
}
```

### API do assistente — porta 8003

| Método | Endpoint | Descrição |
| --- | --- | --- |
| GET | `/health` | Verifica a API e o número de ferramentas expostas |
| POST | `/perguntar` | Recebe uma pergunta e retorna a resposta do assistente |

**GET /health**

```bash
curl http://127.0.0.1:8003/health
```

```json
{
  "status": "ok",
  "ferramentas_disponiveis": 2
}
```

**POST /perguntar**

```bash
curl -X POST http://127.0.0.1:8003/perguntar \
  -H 'Content-Type: application/json' \
  -d '{"pergunta":"Qual é o status da RPA-103 e o motivo da falha?"}'
```

Exemplo de resposta (o texto pode variar):

```json
{
  "resposta": "A RPA-103 está com status ERRO. O último log indica timeout na conexão com o serviço externo."
}
```

A entrada `pergunta` exige entre **10 e 1000 caracteres**. Dados inválidos retornam HTTP `422`.

## Segurança e limitações

- **Validação de argumentos:** códigos RPA seguem o padrão `RPA-000`; argumentos extras são rejeitados.
- **Controle no executor:** só funções presentes no dicionário de funções permitidas podem executar.
- **Separação de interfaces:** a API HTTP não disponibiliza operações de reinício.
- **Confirmação no terminal:** o reinício simulado exige aprovação humana, mas nunca altera processos reais.
- **Resiliência:** erros de conexão e timeout são tratados sem inventar resultados de consulta.
- **Dados fictícios:** processos e logs são mantidos em memória na API de monitoramento.
- **Uso local:** este projeto **não possui autenticação, rate limiting ou auditoria completa**. Não deve ser disponibilizado publicamente sem acrescentar esses controles.

## Testes automatizados

Na raiz do projeto, com as dependências instaladas e a variável `OPENAI_API_KEY` configurada:

```bash
python -m pytest -v tests/
```

Cobertura dos cenários implementados:

1. Health check do assistente.
2. Resposta bem-sucedida com modelo simulado (mock).
3. Rejeição de pergunta curta (HTTP `422`).
4. Rejeição de campo obrigatório ausente (HTTP `422`).
5. Bloqueio da ferramenta sensível na API.
6. Tratamento de timeout da OpenAI (HTTP `504`).

**Resultado observado durante o desenvolvimento:** `6 passed`.

Os testes automatizados usam mocks e não substituem os testes de integração manuais com as duas APIs e a OpenAI.

## Próximas melhorias

- Autenticação e autorização por usuário.
- Persistência de estados e logs em PostgreSQL.
- Logs estruturados, métricas e rastreabilidade de chamadas.
- Testes adicionais de integração e segurança.
- Containerização com Docker e configuração adequada para produção.
- Evolução para agentes com ferramentas e fluxos mais elaborados.

## Contexto de aprendizado

Projeto desenvolvido como parte de um roteiro prático de estudos em **Python, RPA e Engenharia de IA**, com foco em integração de modelos de linguagem a ferramentas e APIs.
