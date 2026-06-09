# ==================================================
# environment/board.py
# Responsabilidade: representar o tabuleiro,
# validar regras e fornecer informações ao agente.
# O board NAO resolve nada — só sabe o que é válido.
# ==================================================


class SudokuBoard:
    def __init__(self, puzzle: list[list[int]]):
        """
        Recebe o puzzle como lista 9x9.
        0 representa célula vazia.
        """
        self.initial = [row[:] for row in puzzle]       # puzzle original (imutável)
        self.grid    = [row[:] for row in puzzle]        # cópia que pode ser modificada

    # --------------------------------------------------
    # Informações sobre o tabuleiro
    # --------------------------------------------------

    def get_empty_cells(self) -> list[tuple[int, int]]:
        """Retorna lista de (linha, coluna) de todas as células vazias."""
        return [
            (i, j)
            for i in range(9)
            for j in range(9)
            if self.initial[i][j] == 0
        ]

    def get_initial_cells(self) -> list[tuple[int, int]]:
        """Retorna lista de (linha, coluna) das células já preenchidas no puzzle."""
        return [
            (i, j)
            for i in range(9)
            for j in range(9)
            if self.initial[i][j] != 0
        ]

    def get_neighbors(self, var: tuple[int, int]) -> set[tuple[int, int]]:
        """
        Retorna todas as células que compartilham restrição com var:
        mesma linha, mesma coluna ou mesmo bloco 3x3.
        """
        i, j = var
        neighbors = set()

        # Linha e coluna
        for k in range(9):
            if k != j:
                neighbors.add((i, k))
            if k != i:
                neighbors.add((k, j))

        # Bloco 3x3
        box_i = (i // 3) * 3
        box_j = (j // 3) * 3
        for r in range(box_i, box_i + 3):
            for c in range(box_j, box_j + 3):
                if (r, c) != var:
                    neighbors.add((r, c))

        return neighbors

    # --------------------------------------------------
    # Validação
    # --------------------------------------------------

    def is_valid_value(self, row: int, col: int, num: int) -> bool:
        """
        Verifica se num pode ser colocado em (row, col)
        sem violar as regras do Sudoku no grid atual.
        """
        # Linha
        if num in self.grid[row]:
            return False

        # Coluna
        if num in [self.grid[r][col] for r in range(9)]:
            return False

        # Bloco 3x3
        box_r = (row // 3) * 3
        box_c = (col // 3) * 3
        for r in range(box_r, box_r + 3):
            for c in range(box_c, box_c + 3):
                if self.grid[r][c] == num:
                    return False

        return True

    def is_solved(self) -> bool:
        """Retorna True se o grid está completamente e corretamente preenchido."""
        for i in range(9):
            row = [self.grid[i][j] for j in range(9)]
            col = [self.grid[j][i] for j in range(9)]
            if sorted(row) != list(range(1, 10)):
                return False
            if sorted(col) != list(range(1, 10)):
                return False

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):
                block = [
                    self.grid[box_r + r][box_c + c]
                    for r in range(3)
                    for c in range(3)
                ]
                if sorted(block) != list(range(1, 10)):
                    return False

        return True

    def count_conflicts(self) -> int:
        """
        Conta o total de conflitos no grid atual.
        Usado pelo Hill Climbing como função objetivo.
        Quanto menor, mais perto da solução.
        """
        conflicts = 0

        for i in range(9):
            row = [self.grid[i][j] for j in range(9)]
            col = [self.grid[j][i] for j in range(9)]
            conflicts += (9 - len(set(row)))
            conflicts += (9 - len(set(col)))

        return conflicts

    # --------------------------------------------------
    # Manipulação do grid
    # --------------------------------------------------

    def apply_solution(self, assignment: dict[tuple[int, int], int]):
        """
        Recebe o dicionário {(i,j): valor} do CSP
        e aplica no grid.
        """
        for (i, j), val in assignment.items():
            self.grid[i][j] = val

    def reset(self):
        """Volta o grid para o estado inicial."""
        self.grid = [row[:] for row in self.initial]

    # --------------------------------------------------
    # Visualização no terminal
    # --------------------------------------------------

    def print_board(self, grid: list[list[int]] | None = None):
        """
        Imprime o tabuleiro formatado no terminal.
        Se grid=None, usa o self.grid atual.
        """
        board = grid if grid is not None else self.grid

        for i in range(9):
            if i % 3 == 0 and i != 0:
                print("-" * 21)

            for j in range(9):
                if j % 3 == 0 and j != 0:
                    print("|", end=" ")
                print(board[i][j] if board[i][j] != 0 else ".", end=" ")
            print()