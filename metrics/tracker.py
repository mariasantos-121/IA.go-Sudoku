# ==================================================
# metrics/tracker.py
# Responsabilidade: registrar métricas de execução
# de qualquer agente (CSP ou Hill Climbing).
# Os agentes importam e usam esse módulo.
# ==================================================

import time


class Tracker:
    def __init__(self):
        self.nodes       = 0          # nós expandidos (chamadas ao backtrack / iterações HC)
        self.backtracks  = 0          # quantas vezes o backtracking recuou (só CSP)
        self.start_time  = None       # momento em que solve() começou
        self.end_time    = None       # momento em que solve() terminou
        self.steps       = []         # lista de snapshots do tabuleiro (para animação)
        self.solved      = False      # se o agente encontrou solução

    # --------------------------------------------------
    # Controle de tempo
    # --------------------------------------------------

    def start(self):
        """Chame no início do solve()."""
        self.nodes      = 0
        self.backtracks = 0
        self.steps      = []
        self.solved     = False
        self.start_time = time.time()

    def stop(self, solved: bool):
        """Chame no final do solve(), passando se achou solução."""
        self.end_time = time.time()
        self.solved   = solved

    # --------------------------------------------------
    # Registro durante a busca
    # --------------------------------------------------

    def increment_nodes(self):
        """Incrementa contagem de nós. Chamar a cada iteração/recursão."""
        self.nodes += 1

    def increment_backtracks(self):
        """Incrementa contagem de backtracks. Chamar só no CSP."""
        self.backtracks += 1

    def record_step(self, grid: list[list[int]]):
        """
        Salva um snapshot do tabuleiro para animação.
        Recebe o grid 9x9 como lista de listas.
        Faz cópia para não salvar referência mutável.
        """
        self.steps.append([row[:] for row in grid])

    # --------------------------------------------------
    # Resultados
    # --------------------------------------------------

    def elapsed(self) -> float:
        """Tempo total de execução em segundos."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return round(end - self.start_time, 4)

    def summary(self) -> dict:
        """
        Retorna dicionário com todas as métricas.
        Usado pela interface para exibir resultados.
        """
        return {
            "solved"     : self.solved,
            "nodes"      : self.nodes,
            "backtracks" : self.backtracks,
            "time_sec"   : self.elapsed(),
            "steps"      : len(self.steps),
        }

    def print_summary(self, agent_name: str = "Agente"):
        """Imprime resumo no terminal. Útil para testes sem interface."""
        s = self.summary()
        print(f"\n{'='*35}")
        print(f"  Resultado — {agent_name}")
        print(f"{'='*35}")
        print(f"  Solução encontrada : {'Sim' if s['solved'] else 'Não'}")
        print(f"  Nós expandidos     : {s['nodes']}")
        print(f"  Backtracks         : {s['backtracks']}")
        print(f"  Passos gravados    : {s['steps']}")
        print(f"  Tempo de execução  : {s['time_sec']}s")
        print(f"{'='*35}\n")