# agente-ia---trello

Agente de IA em Python (Google ADK + Gemini) que organiza as tarefas do dia num quadro do Trello a partir de uma conversa. Cada função Python vira uma ferramenta do agente.

## O que o agente faz

Ao começar, informa a data de hoje e pergunta as tarefas do dia, criando um card para cada uma. Depois você conta o que já fez e ele move os cards.

| Ferramenta | Função |
|---|---|
| `get_temporal_context` | Data e hora atuais |
| `adicionar_tarefa` | Cria card em *A fazer* com nome, descrição e data |
| `listar_tarefas` | Lista todas ou só as de um status |
| `mudar_status_tarefa` | Move entre *A fazer*, *Em andamento* e *Concluído* |
| `remover_tarefa` | Exclui um card |
| `listar_quadros` | Lista os quadros (para trabalhar com mais de um) |

## Como configurar

1. **Trello**: crie um quadro (padrão `DIO`) com as listas `A fazer`, `Em andamento` e `Concluído`. Em <https://trello.com/power-ups/admin> registre um Power-Up e gere a **chave**, o **segredo** e o **token**.
2. **Gemini**: gere uma chave gratuita no [Google AI Studio](https://aistudio.google.com/) (tem limite diário).
3. **Ambiente** (Python 3.10+):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp agenttaskmanager/.env.exemplo agenttaskmanager/.env   # preencha as chaves
   adk web
   ```
4. Abra o endereço mostrado, escolha `agenttaskmanager` e converse. Para outro quadro padrão, mude `TRELLO_BOARD` no `.env`.

O `.env` está no `.gitignore`; nunca versione chaves.

## Melhorias feitas (em relação ao agente base)

- **Data com um dia a menos**: a data `AAAA-MM-DD` agora é enviada às 12:00 UTC, e não à meia-noite, então no fuso do Brasil (UTC-3) continua no mesmo dia.
- **Status com acento/variações**: `_normalizar` remove acentos e `SINONIMOS` aceita "Concluído", "concluida", "feito", "doing" etc.
- **`remover_tarefa`**: criada, pois a instrução prometia e o código não tinha.
- **`try/except` em todas as ferramentas**, devolvendo mensagem `❌` clara ao agente.
- **Conexão única**: `_conectar()` e `_obter_quadro()` substituem o código repetido.
- **Vários quadros**: parâmetro `nome_do_quadro` e ferramenta `listar_quadros`; o agente pergunta em qual quadro a tarefa entra.
- **Instrução alinhada** às ferramentas que existem.

## Como testei

### 1. Testes automáticos (sem Trello real)
```bash
python -m pytest tests
```
Usam um quadro falso e cobrem: status com acento ("Concluído"), data de vencimento sem perder um dia, mover, listar com filtro, remover e status inválido. Resultado: **4 passando**.

### 2. Teste manual no `adk web` com o meu quadro
Roteiro seguido, com o quadro do Trello aberto ao lado. **Resultado: os 7 passos funcionaram como esperado**, com o agente criando, listando, movendo e removendo cards no meu quadro.

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
