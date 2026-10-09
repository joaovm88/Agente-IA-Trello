# Agente de tarefas com Trello (Google ADK + Gemini)

Agente de IA em Python que organiza as tarefas do seu dia num quadro do Trello **a partir de uma conversa**. Cada função Python vira uma ferramenta que o modelo Gemini decide quando chamar.

> Projeto do desafio da DIO "Criando um agente para automatizar um fluxo de trabalho", baseado no agente `agent04` do repositório [agent-carbon-footprint](https://github.com/digitalinnovationone/agent-carbon-footprint/tree/main/agents/agent04), com melhorias próprias (veja [Melhorias](#melhorias-em-relação-ao-agente-base)).

## Como funciona

```
Você ──conversa──▶ Gemini (ADK) ──escolhe a ferramenta──▶ função Python ──py-trello──▶ Quadro do Trello
```

1. O agente abre a conversa informando a data de hoje e perguntando as tarefas do dia.
2. Para cada tarefa, cria um card em **A fazer** com nome, descrição e data.
3. Quando você conta o que já fez, ele move o card para **Em andamento** ou **Concluído**.

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `get_temporal_context` | Devolve a data e a hora atuais |
| `adicionar_tarefa` | Cria um card em *A fazer* com nome, descrição e data (`AAAA-MM-DD`) |
| `listar_tarefas` | Lista todas as tarefas ou só as de um status |
| `mudar_status_tarefa` | Move o card entre *A fazer*, *Em andamento* e *Concluído* |
| `remover_tarefa` | Exclui um card (o agente pede confirmação antes) |
| `listar_quadros` | Lista seus quadros, para trabalhar com mais de um |

As ferramentas que mexem em cards aceitam o parâmetro opcional `nome_do_quadro`; sem ele, usam o quadro padrão (`TRELLO_BOARD`).

## Estrutura do projeto

```
.
├── agenttaskmanager/
│   ├── __init__.py
│   ├── agent.py          # ferramentas e definição do agente
│   └── .env.exemplo      # modelo das credenciais (copie para .env)
├── tests/
│   └── test_agent.py     # testes offline com um quadro falso
├── requirements.txt
└── README.md
```

## Como rodar

**Requisitos:** Python 3.10 ou superior, conta no Trello e conta Google.

### 1. Preparar o Trello
1. Crie um quadro chamado `DIO` (ou outro nome, veja o passo 3) com as listas **A fazer**, **Em andamento** e **Concluído**.
2. Em <https://trello.com/power-ups/admin>, crie um Power-Up e gere a **chave de API** e o **segredo**.
3. Na mesma página, gere o **token** pelo link "Token".

### 2. Obter a chave do Gemini
Gere uma chave gratuita em <https://aistudio.google.com/apikey>. Ela tem limite diário de uso.

### 3. Instalar e configurar
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp agenttaskmanager/.env.exemplo agenttaskmanager/.env   # Windows: copy
```
Edite **`agenttaskmanager/.env`** (o nome do arquivo é exatamente `.env`, não `.env.exemplo`):

```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=...
TRELLO_API_KEY=...
TRELLO_API_SECRET=...
TRELLO_TOKEN=...
TRELLO_BOARD=DIO        # nome do quadro padrão
```

### 4. Iniciar
Na pasta raiz do projeto:
```bash
adk web
```
Abra o endereço mostrado (normalmente <http://localhost:8000>), escolha **agenttaskmanager** e converse.

### Segurança
O `.env` está no `.gitignore`. Nunca coloque chaves em arquivos versionados, como o `.env.exemplo`, nem em prints. Se alguma chave vazar, gere outra.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `No API key was provided` | O arquivo `.env` não existe em `agenttaskmanager/`, tem outro nome ou a `GOOGLE_API_KEY` está vazia. Reinicie o `adk web` depois de editar |
| `❌ Quadro '...' não encontrado` | O nome do quadro não bate com `TRELLO_BOARD` (a comparação ignora acentos e maiúsculas) |
| `❌ O quadro '...' não tem a lista ...` | As listas do quadro estão com nomes diferentes de *A fazer*, *Em andamento* e *Concluído* |
| `401 Unauthorized` | Chave, segredo ou token do Trello incorretos |
| `429` / `RESOURCE_EXHAUSTED` | Acabou o limite diário gratuito do Gemini |
| `adk: command not found` | O ambiente virtual não está ativo ou o `pip install` falhou |

## Melhorias em relação ao agente base

- **Data com um dia a menos:** a data `AAAA-MM-DD` agora é enviada às 12:00 UTC, e não à meia-noite. No fuso do Brasil (UTC-3), o card continua no mesmo dia.
- **Status com acento e variações:** `_normalizar` remove acentos e `SINONIMOS` aceita "Concluído", "concluida", "feito", "doing" e similares, que antes davam status inválido.
- **`remover_tarefa`:** criada, pois a instrução do agente base prometia remover tarefas e o código não tinha a função.
- **Tratamento de erros:** todas as ferramentas usam `try/except` e devolvem uma mensagem `❌` clara, em vez de quebrar a conversa.
- **Conexão única:** `_conectar()` e `_obter_quadro()` substituem o código de conexão repetido em cada ferramenta.
- **Vários quadros:** parâmetro `nome_do_quadro` e ferramenta `listar_quadros`; o agente pergunta em qual quadro a tarefa entra.
- **Instrução alinhada às ferramentas:** o texto de instrução do agente descreve só o que ele realmente consegue fazer.

## Como testei

### 1. Testes automáticos (sem Trello real)
```bash
pip install pytest
python -m pytest tests
```
Usam um quadro falso e cobrem: status com acento ("Concluído"), data sem perder um dia, mover, listar com filtro, remover e status inválido. Resultado: **4 testes passando**.

### 2. Teste manual no `adk web` com o meu quadro
Roteiro seguido com o quadro do Trello aberto ao lado. **Resultado: os 7 passos funcionaram como esperado.**

| # | Mensagem enviada | Resultado esperado |
|---|---|---|
| 1 | `Oi` | O agente informa a data de hoje e pergunta as tarefas do dia |
| 2 | `Estudar Python, descrição: revisar funções, para hoje` | Card criado em **A fazer** com a data de hoje (não a do dia anterior) |
| 3 | `Quais são minhas tarefas?` | Lista o card com nome, descrição e vencimento |
| 4 | `Comecei a estudar Python` | Card movido para **Em andamento** |
| 5 | `Terminei de estudar Python` | Card movido para **Concluído** |
| 6 | `Mostre só as concluídas` | Lista só esse card (testa o acento) |
| 7 | `Remova a tarefa Estudar Python` | Pede confirmação e, ao confirmar, o card some do quadro |

**Evidência:** *(coloque aqui os prints da conversa no `adk web` ao lado do quadro do Trello)*

## Limitações

- Os cards são encontrados pelo **nome**; se houver dois cards com o mesmo nome, a ferramenta usa o primeiro que achar.
- O quadro precisa ter as três listas com os nomes acima (ou equivalentes em inglês: *To Do*, *Doing*, *Done*).
- A chave gratuita do Gemini tem limite diário de requisições.
