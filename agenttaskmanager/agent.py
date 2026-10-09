"""Agente de organização de tarefas: conversa com o usuário e usa um quadro do Trello."""
import os
import unicodedata
from datetime import datetime

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from trello import TrelloClient

load_dotenv()

QUADRO_PADRAO = os.getenv("TRELLO_BOARD", "DIO")

# Status canônico -> nomes de lista aceitos no Trello (já normalizados)
STATUS_LISTAS = {
    "a fazer": ["a fazer", "to do", "todo"],
    "em andamento": ["em andamento", "doing", "in progress"],
    "concluido": ["concluido", "done"],
}
# Variações que o usuário (ou o modelo) pode escrever -> status canônico
SINONIMOS = {
    "a fazer": "a fazer", "afazer": "a fazer", "pendente": "a fazer", "todo": "a fazer", "to do": "a fazer",
    "em andamento": "em andamento", "andamento": "em andamento", "fazendo": "em andamento",
    "doing": "em andamento", "in progress": "em andamento",
    "concluido": "concluido", "concluida": "concluido", "concluir": "concluido", "feito": "concluido",
    "feita": "concluido", "pronto": "concluido", "done": "concluido",
}


def _normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem espaços nas pontas ('Concluído ' -> 'concluido')."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def _status_canonico(status: str):
    return SINONIMOS.get(_normalizar(status))


def _conectar() -> TrelloClient:
    """Única função que cria a conexão com o Trello."""
    return TrelloClient(
        api_key=os.getenv("TRELLO_API_KEY"),
        api_secret=os.getenv("TRELLO_API_SECRET"),
        token=os.getenv("TRELLO_TOKEN"),
    )


def _obter_quadro(nome_do_quadro: str = ""):
    nome = nome_do_quadro or QUADRO_PADRAO
    quadros = _conectar().list_boards()
    for q in quadros:
        if _normalizar(q.name) == _normalizar(nome):
            return q
    disponiveis = ", ".join(q.name for q in quadros) or "nenhum"
    raise ValueError(f"Quadro '{nome}' não encontrado. Quadros disponíveis: {disponiveis}")


def _lista_do_status(quadro, status_canonico: str):
    aceitos = STATUS_LISTAS[status_canonico]
    for lista in quadro.list_lists():
        if _normalizar(lista.name) in aceitos:
            return lista
    raise ValueError(f"O quadro '{quadro.name}' não tem a lista '{status_canonico}'")


def _achar_card(quadro, nome_da_task: str):
    alvo = _normalizar(nome_da_task)
    for lista in quadro.list_lists():
        for card in lista.list_cards():
            if _normalizar(card.name) == alvo:
                return card, lista
    return None, None


def get_temporal_context() -> str:
    """Retorna a data e hora atuais (AAAA/MM/DD HH:MM:SS) para organizar as tarefas do dia."""
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def listar_quadros() -> str:
    """Lista os nomes dos quadros do Trello disponíveis para o usuário escolher."""
    try:
        nomes = [q.name for q in _conectar().list_boards()]
        return "Quadros: " + ", ".join(nomes) + f" (padrão: {QUADRO_PADRAO})"
    except Exception as e:
        return f"❌ Erro: {e}"


def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, due_date: str, nome_do_quadro: str = "") -> str:
    """Cria um card na lista 'A fazer'.

    Args:
        nome_da_task: título da tarefa.
        descricao_da_task: descrição da tarefa.
        due_date: data de vencimento no formato AAAA-MM-DD.
        nome_do_quadro: quadro de destino; vazio usa o quadro padrão.
    """
    try:
        # Meio-dia UTC evita que o Trello mostre o dia anterior em fusos como o do Brasil (UTC-3).
        data = datetime.strptime(due_date.strip()[:10].replace("/", "-"), "%Y-%m-%d")
        vencimento = data.strftime("%Y-%m-%dT12:00:00.000Z")
        quadro = _obter_quadro(nome_do_quadro)
        lista = _lista_do_status(quadro, "a fazer")
        lista.add_card(name=nome_da_task, desc=descricao_da_task, due=vencimento)
        return f"✅ Tarefa '{nome_da_task}' criada em '{quadro.name}' para {data.strftime('%d/%m/%Y')}"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Erro: {e}"


def listar_tarefas(status: str = "todas", nome_do_quadro: str = ""):
    """Lista as tarefas do quadro, todas ou só de um status ('a fazer', 'em andamento', 'concluído')."""
    try:
        quadro = _obter_quadro(nome_do_quadro)
        listas = quadro.list_lists()
        if _normalizar(status) not in ("todas", "todos", "todo mundo", ""):
            canonico = _status_canonico(status)
            if not canonico:
                return "❌ Status inválido. Use: 'todas', 'a fazer', 'em andamento' ou 'concluído'"
            listas = [l for l in listas if _normalizar(l.name) in STATUS_LISTAS[canonico]]
        return [
            {"nome": c.name, "descricao": c.desc, "vencimento": c.due, "status": l.name, "id": c.id}
            for l in listas
            for c in l.list_cards()
        ]
    except Exception as e:
        return f"❌ Erro: {e}"


def mudar_status_tarefa(nome_da_task: str, novo_status: str, nome_do_quadro: str = "") -> str:
    """Move um card entre 'A fazer', 'Em andamento' e 'Concluído'."""
    try:
        canonico = _status_canonico(novo_status)
        if not canonico:
            return "❌ Status inválido. Use: 'a fazer', 'em andamento' ou 'concluído'"
        quadro = _obter_quadro(nome_do_quadro)
        destino = _lista_do_status(quadro, canonico)
        card, origem = _achar_card(quadro, nome_da_task)
        if not card:
            return f"❌ Card '{nome_da_task}' não encontrado"
        card.change_list(destino.id)
        return f"✅ '{card.name}': {origem.name} → {destino.name}"
    except Exception as e:
        return f"❌ Erro: {e}"


def remover_tarefa(nome_da_task: str, nome_do_quadro: str = "") -> str:
    """Remove (exclui) o card com o nome informado. Confirme com o usuário antes de chamar."""
    try:
        quadro = _obter_quadro(nome_do_quadro)
        card, _ = _achar_card(quadro, nome_da_task)
        if not card:
            return f"❌ Card '{nome_da_task}' não encontrado"
        card.delete()
        return f"🗑️ Tarefa '{card.name}' removida"
    except Exception as e:
        return f"❌ Erro: {e}"


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Agente de Organização de Tarefas",
    instruction="""
Você é um agente de organização de tarefas que trabalha num quadro do Trello.
Assim que a conversa começar, chame get_temporal_context e pergunte quais são as tarefas
do dia, informando a data de hoje. Depois pergunte se há mais alguma, até o usuário dizer que não.
Para cada tarefa, peça (ou deduza) nome, descrição e data (AAAA-MM-DD; "hoje" = data de get_temporal_context).

Ferramentas:
1. adicionar_tarefa: cria um card em "A fazer" com nome, descrição e data.
2. listar_tarefas: lista todas ou filtra por status ("a fazer", "em andamento", "concluído").
3. mudar_status_tarefa: move o card entre "A fazer", "Em andamento" e "Concluído"
   quando o usuário contar o que já fez ou começou.
4. remover_tarefa: exclui um card; peça confirmação antes.
5. listar_quadros: mostra os quadros; se o usuário tiver mais de um, pergunte em qual a tarefa entra
   e passe nome_do_quadro. Sem escolha, o quadro padrão é usado.
6. get_temporal_context: data e hora atuais.
Se uma ferramenta devolver um erro (❌), explique ao usuário em linguagem simples.
""",
    tools=[get_temporal_context, listar_quadros, adicionar_tarefa, listar_tarefas, mudar_status_tarefa, remover_tarefa],
)
