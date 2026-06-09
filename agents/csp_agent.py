# ==================================================
# agents/csp_agent.py
# Responsabilidade: resolver o Sudoku usando
# Backtracking + AC-3 (propagação de restrições)
# + MRV (heurística de seleção de variável).
# ==================================================

from collections import deque
from environment.board import SudokuBoard
from metrics.tracker import Tracker


class CSPAgent:
    def __init__(self, board: SudokuBoard, tracker: Tracker):
        self.board   = board
        self.tracker = tracker

        # --------------------------------------------------
        # CORREÇÃO 1: apenas células vazias são variáveis.
        # Células já preenchidas não entram na busca.
        # --------------------------------------------------
        self.variables = self.board.get_empty_cells()

        # Domínios: conjunto de valores possíveis para cada célula vazia
        self.domains = {
            var: set(range(1, 10))
            for var in self.variables
        }

        # Restrições: vizinhos de cada variável (linha + coluna + bloco)
        self.constraints = {
            var: self.board.get_neighbors(var)
            for var in self.variables
        }

    # ==================================================
    # AC-3 — Propagação de Restrições
    # Equivalente à propagação unitária do DPLL
    # (Lab: Agentes Lógicos)
    # ==================================================

    def ac3(self) -> bool:
        """
        Reduz os domínios antes de iniciar o backtracking.
        Retorna False se algum domínio ficar vazio (puzzle sem solução).
        """
        # Fila com todos os arcos entre variáveis vizinhas
        queue = deque(
            (xi, xj)
            for xi in self.variables
            for xj in self.constraints[xi]
            if xj in self.variables       # só arcos entre variáveis (células vazias)
        )

        while queue:
            xi, xj = queue.popleft()
            if self._revise(xi, xj):
                if len(self.domains[xi]) == 0:
                    return False          # domínio vazio → sem solução
                for xk in self.constraints[xi]:
                    if xk != xj and xk in self.variables:
                        queue.append((xk, xi))

        return True

    def _revise(self, xi: tuple, xj: tuple) -> bool:
        """
        Remove de domains[xi] os valores que não têm
        suporte em domains[xj].
        """
        revised = False

        # Se xj é célula já preenchida, seu "domínio" é o valor fixo do puzzle
        if xj not in self.variables:
            xj_domain = {self.board.initial[xj[0]][xj[1]]}
        else:
            xj_domain = self.domains[xj]

        for x in set(self.domains[xi]):
            # x não tem suporte em xj se nenhum valor de xj é diferente de x
            if not any(x != y for y in xj_domain):
                self.domains[xi].discard(x)
                revised = True

        return revised

    # ==================================================
    # BACKTRACKING
    # Estrutura idêntica ao DPLL (Lab: Agentes Lógicos)
    # ==================================================

    def solve(self) -> list[list[int]] | None:
        """
        Ponto de entrada. Inicializa o tracker e
        dispara o backtracking.
        Retorna o grid 9x9 resolvido ou None se sem solução.
        """
        self.tracker.start()

        # Roda AC-3 antes da busca para reduzir domínios
        if not self.ac3():
            self.tracker.stop(solved=False)
            return None

        assignment = {}

        # Células já preenchidas entram como atribuição inicial
        for i in range(9):
            for j in range(9):
                if self.board.initial[i][j] != 0:
                    assignment[(i, j)] = self.board.initial[i][j]

        result = self._backtrack(assignment)

        if result:
            # Aplica solução no grid do board
            self.board.apply_solution(result)
            self.tracker.stop(solved=True)
            return self.board.grid
        else:
            self.tracker.stop(solved=False)
            return None

    def _backtrack(self, assignment: dict) -> dict | None:
        """
        Backtracking recursivo com MRV.
        Registra métricas a cada chamada.
        """
        # Conta este nó expandido
        self.tracker.increment_nodes()

        # Condição de parada: todas as variáveis atribuídas
        if len(assignment) == len(self.variables) + len(self.board.get_initial_cells()):
            return assignment

        # Seleciona próxima variável via MRV
        var = self._select_unassigned_variable(assignment)

        for value in self._ordered_domain(var, assignment):
            if self._is_consistent(var, value, assignment):
                assignment[var] = value

                # Grava snapshot do estado atual para animação
                self._record_snapshot(assignment)

                result = self._backtrack(assignment)
                if result:
                    return result

                # Backtrack: remove atribuição e registra
                del assignment[var]
                self.tracker.increment_backtracks()

        return None

    # ==================================================
    # MRV — Minimum Remaining Values
    # Heurística de seleção de variável
    # (Russell & Norvig, AIMA Cap. 6)
    # ==================================================

    def _select_unassigned_variable(self, assignment: dict) -> tuple:
        """
        CORREÇÃO 2: MRV dinâmico.
        Calcula quantos valores ainda são consistentes
        com o estado atual do assignment, não com o
        domínio estático calculado pelo AC-3.
        """
        unassigned = [v for v in self.variables if v not in assignment]

        return min(
            unassigned,
            key=lambda var: (
                # Critério primário: menor domínio disponível agora
                len([
                    v for v in self.domains[var]
                    if self._is_consistent(var, v, assignment)
                ]),
                # Critério de desempate: maior grau (mais vizinhos não atribuídos)
                -len([
                    n for n in self.constraints[var]
                    if n not in assignment
                ])
            )
        )

    def _ordered_domain(self, var: tuple, assignment: dict) -> list:
        """
        Retorna valores do domínio de var ordenados
        pelos que causam menos restrições nos vizinhos
        (Least Constraining Value — melhora performance).
        """
        def count_constraints(value):
            count = 0
            for neighbor in self.constraints[var]:
                if neighbor not in assignment and neighbor in self.variables:
                    if value in self.domains[neighbor]:
                        count += 1
            return count

        return sorted(self.domains[var], key=count_constraints)

    # ==================================================
    # Checagem de consistência
    # ==================================================

    def _is_consistent(self, var: tuple, value: int, assignment: dict) -> bool:
        """
        Verifica se atribuir value a var não viola
        nenhuma restrição com os vizinhos já atribuídos.
        """
        for neighbor in self.constraints[var]:
            if neighbor in assignment and assignment[neighbor] == value:
                return False
        return True

    # ==================================================
    # Snapshot para animação
    # ==================================================

    def _record_snapshot(self, assignment: dict):
        """
        Monta o grid 9x9 atual e manda para o tracker.
        Combina células iniciais + assignment atual.
        """
        grid = [row[:] for row in self.board.initial]
        for (i, j), val in assignment.items():
            grid[i][j] = val
        self.tracker.record_step(grid)