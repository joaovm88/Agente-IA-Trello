"""Testes offline (sem Trello real): usam um quadro falso."""
import os
import sys
import types
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
for nome in ("google", "google.adk", "google.adk.agents", "google.adk.agents.llm_agent", "trello", "dotenv"):
    sys.modules.setdefault(nome, types.ModuleType(nome))
sys.modules["google.adk.agents.llm_agent"].Agent = lambda **kw: kw
sys.modules["trello"].TrelloClient = MagicMock
sys.modules["dotenv"].load_dotenv = lambda: None

from agenttaskmanager import agent  # noqa: E402


def quadro_falso():
    def lista(nome, cards=()):
        l = MagicMock(); l.name = nome; l.id = nome; l.list_cards.return_value = list(cards); return l
    card = MagicMock(); card.name = "Estudar"; card.desc = ""; card.due = None; card.id = "1"
    q = MagicMock(); q.name = "DIO"
    q.list_lists.return_value = [lista("A fazer", [card]), lista("Em andamento"), lista("Concluído")]
    agent._obter_quadro = lambda nome="": q
    return q, card


def test_normaliza_status_com_acento():
    assert agent._status_canonico("Concluído") == "concluido"
    assert agent._status_canonico(" EM  andamento") == "em andamento"
    assert agent._status_canonico("xyz") is None


def test_mover_para_concluido_com_acento():
    q, card = quadro_falso()
    assert agent.mudar_status_tarefa("estudar", "Concluído").startswith("✅")
    card.change_list.assert_called_once_with("Concluído")


def test_data_nao_perde_um_dia():
    q, _ = quadro_falso()
    agent.adicionar_tarefa("T", "d", "2026-10-09")
    assert q.list_lists()[0].add_card.call_args.kwargs["due"] == "2026-10-09T12:00:00.000Z"


def test_remover_e_listar():
    q, card = quadro_falso()
    assert len(agent.listar_tarefas("a fazer")) == 1
    assert agent.listar_tarefas("concluído") == []
    assert agent.remover_tarefa("Estudar").startswith("🗑️")
    card.delete.assert_called_once()
    assert agent.listar_tarefas("banana").startswith("❌")
