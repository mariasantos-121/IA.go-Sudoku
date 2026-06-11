# ==================================================
# agents/hill_climbing_agent.py
#
# Hill Climbing com Reinício Aleatório para Sudoku.
# Fundamentado no Lab: Ambientes Complexos I.
#
# Estratégia:
#   1. Gera estado inicial preenchendo cada bloco 3x3
#      com os números faltantes (embaralhados)
#   2. Avalia o estado pela quantidade de conflitos
#      em linhas e colunas (blocos sempre OK)
#   3. A cada iteração, testa TODOS os blocos e
#      todas as trocas possíveis dentro deles
#   4. Aceita o melhor vizinho se melhorar
#   5. Permite movimentos laterais (mesmo custo)
#      para escapar de platôs, com limite
#   6. Ao travar, reinicia com novo estado aleatório
#   7. Guarda o melhor estado de TODA a execução,
#      retornando-o mesmo que não chegue a 0 conflitos
# ==================================================

import random
import copy
from environment.board import SudokuBoard
from metrics.tracker   import Tracker


class HillClimbingAgent:

    def __init__(
        self,
        board         : SudokuBoard,
        tracker       : Tracker,
        max_restarts  : int = 150,
        max_iterations: int = 3000,
        max_sideways  : int = 50,
    ):
        """
        Parâmetros
        ----------
        board          : tabuleiro com puzzle inicial
        tracker        : objeto de métricas compartilhado
        max_restarts   : quantas vezes reinicia do zero
        max_iterations : iterações máximas por restart
        max_sideways   : movimentos laterais (custo igual)
                         permitidos antes de reiniciar
        """
        self.board          = board
        self.tracker        = tracker
        self.max_restarts   = max_restarts
        self.max_iterations = max_iterations
        self.max_sideways   = max_sideways

    # ==================================================
    # Ponto de entrada público
    # ==================================================

    def solve(self) -> list[list[int]]:
        """
        Executa o Hill Climbing com Reinício Aleatório.

        Retorna sempre um grid 9x9:
          - Solução perfeita (0 conflitos) se encontrar
          - Melhor aproximação encontrada caso contrário
        O tracker registra se a solução é perfeita ou não.
        """
        self.tracker.start()

        # Guarda o melhor estado encontrado em TODOS os restarts
        best_overall_grid     = None
        best_overall_conflicts = float("inf")

        for restart in range(self.max_restarts):

            # Novo estado inicial aleatório para este restart
            grid = self._generate_initial_state()
            cost = self._count_conflicts(grid)

            # Grava snapshot do estado inicial do restart
            self.tracker.record_step(copy.deepcopy(grid))

            # Contador de movimentos laterais neste restart
            sideways_count = 0

            for _ in range(self.max_iterations):

                # Contabiliza este nó expandido
                self.tracker.increment_nodes()

                # Atualiza melhor global se este estado for melhor
                if cost < best_overall_conflicts:
                    best_overall_conflicts = cost
                    best_overall_grid      = copy.deepcopy(grid)

                # Solução perfeita encontrada
                if cost == 0:
                    self.board.apply_solution(
                        {(i, j): grid[i][j]
                         for i in range(9)
                         for j in range(9)}
                    )
                    self.tracker.stop(solved=True)
                    return self.board.grid

                # Busca melhor vizinho em TODOS os blocos
                neighbor, neighbor_cost = self._best_neighbor(grid, cost)

                if neighbor_cost < cost:
                    # Melhora real — sobe o morro
                    grid           = neighbor
                    cost           = neighbor_cost
                    sideways_count = 0
                    self.tracker.record_step(copy.deepcopy(grid))

                elif neighbor_cost == cost and sideways_count < self.max_sideways:
                    # Movimento lateral — tenta escapar do platô
                    grid           = neighbor
                    sideways_count += 1
                    self.tracker.record_step(copy.deepcopy(grid))

                else:
                    # Ótimo local real — encerra este restart
                    break

        # Esgotou todos os restarts sem solução perfeita.
        # Retorna o melhor estado encontrado em toda a execução.
        if best_overall_grid is not None:
            self.board.apply_solution(
                {(i, j): best_overall_grid[i][j]
                 for i in range(9)
                 for j in range(9)}
            )

        self.tracker.stop(solved=False)
        self.tracker.final_conflicts = best_overall_conflicts
        return self.board.grid

    # ==================================================
    # Geração do estado inicial completo
    # ==================================================

    def _generate_initial_state(self) -> list[list[int]]:
        """
        Preenche cada bloco 3x3 com os números que
        ainda não aparecem nele (embaralhados).

        Garante que nenhum bloco tenha conflitos internos
        desde o início — apenas linhas e colunas podem
        conter conflitos, o que reduz o espaço de busca.
        """
        grid = copy.deepcopy(self.board.initial)

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):

                # Números já presentes neste bloco
                present = {
                    grid[box_r + r][box_c + c]
                    for r in range(3)
                    for c in range(3)
                    if grid[box_r + r][box_c + c] != 0
                }

                # Números que faltam
                missing = list(set(range(1, 10)) - present)
                random.shuffle(missing)

                # Distribui nas células vazias do bloco
                idx = 0
                for r in range(3):
                    for c in range(3):
                        if grid[box_r + r][box_c + c] == 0:
                            grid[box_r + r][box_c + c] = missing[idx]
                            idx += 1

        return grid

    # ==================================================
    # Função heurística — contar conflitos
    # ==================================================

    def _count_conflicts(self, grid: list[list[int]]) -> int:
        """
        Conta o total de conflitos em linhas e colunas.

        Para cada linha/coluna, o número de conflitos é
        (9 - quantidade de valores únicos), pois valores
        repetidos indicam violações das regras do Sudoku.

        Blocos 3x3 não são contados: por construção do
        estado inicial e das trocas (sempre dentro do
        mesmo bloco), eles nunca têm conflitos internos.

        Retorno: inteiro >= 0. Zero = solução perfeita.
        """
        conflicts = 0

        for i in range(9):
            row = [grid[i][j] for j in range(9)]
            col = [grid[j][i] for j in range(9)]
            conflicts += 9 - len(set(row))
            conflicts += 9 - len(set(col))

        return conflicts

    # ==================================================
    # Geração de vizinhos — todos os blocos
    # ==================================================

    def _best_neighbor(
        self,
        grid        : list[list[int]],
        current_cost: int,
    ) -> tuple[list[list[int]], int]:
        """
        Percorre TODOS os blocos 3x3 e testa todas as
        trocas possíveis entre células não-fixas de cada
        bloco, retornando o vizinho de menor custo.

        Trocar apenas dentro do mesmo bloco preserva a
        propriedade de conflito zero nos blocos, então
        só linhas e colunas precisam ser reavaliadas.

        Retorna (melhor_grid, melhor_custo).
        Se nenhuma troca melhorar, retorna o melhor
        movimento lateral encontrado (mesmo custo).
        """
        best_grid      = grid
        best_cost      = current_cost
        lateral_grid   = None
        lateral_cost   = current_cost  # melhor empate encontrado

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):

                # Células não-fixas neste bloco
                free = [
                    (box_r + r, box_c + c)
                    for r in range(3)
                    for c in range(3)
                    if self.board.initial[box_r + r][box_c + c] == 0
                ]

                # Testa todos os pares de células livres
                for i in range(len(free)):
                    for j in range(i + 1, len(free)):
                        r1, c1 = free[i]
                        r2, c2 = free[j]

                        # Aplica troca diretamente no grid (in-place)
                        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
                        cost = self._count_conflicts(grid)

                        if cost < best_cost:
                            # Melhora encontrada — salva cópia
                            best_cost = cost
                            best_grid = copy.deepcopy(grid)

                        elif cost == lateral_cost and lateral_grid is None:
                            # Primeiro empate encontrado — candidato lateral
                            lateral_cost = cost
                            lateral_grid = copy.deepcopy(grid)

                        # Desfaz a troca
                        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]

        # Prioriza melhora; se não houver, usa movimento lateral
        if best_cost < current_cost:
            return best_grid, best_cost

        if lateral_grid is not None:
            return lateral_grid, lateral_cost

        # Sem vizinho melhor ou lateral — sinaliza ótimo local
        return grid, current_cost