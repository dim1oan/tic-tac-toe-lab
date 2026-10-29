"""Модуль предметной логики (Model) для игры «Крестики-нолики».

Обеспечивает независимую от интерфейса валидацию игрового процесса:
- Хранение состояния игрового поля 3x3.
- Контроль очередности ходов.
- Проверка условий победы по всем 8 направлениям и ничейного исхода.
- Ведение турнирной статистики и истории ходов.
- Обработка исключительных ситуаций с использованием кастомных исключений.
"""

from dataclasses import dataclass
from typing import Final, List, Optional, Tuple, Dict
import copy


# Константы игроков и пустого поля
PLAYER_X: Final[str] = "X"
PLAYER_O: Final[str] = "O"
EMPTY_CELL: Final[str] = ""
BOARD_SIZE: Final[int] = 3


class TicTacToeException(Exception):
    """Базовое исключение для ошибок логики игры 'Крестики-нолики'."""
    pass


class InvalidCoordinateError(TicTacToeException):
    """Исключение при передаче координат клетки вне диапазона 0..2."""
    pass


class CellOccupiedError(TicTacToeException):
    """Исключение при попытке сделать ход в уже занятую клетку."""
    pass


class GameOverError(TicTacToeException):
    """Исключение при попытке сделать ход после завершения партии."""
    pass


@dataclass(frozen=True)
class MoveRecord:
    """Неизменяемая структура данных для записи хода в истории.

    Attributes:
        player: Идентификатор игрока ('X' или 'O').
        row: Номер строки (0-2).
        col: Номер столбца (0-2).
        step_number: Порядковый номер хода в партии (начиная с 1).
    """
    player: str
    row: int
    col: int
    step_number: int


class GameModel:
    """Класс чистой игровой логики (Model в паттерне MVC).

    Инкапсулирует состояние игрового поля, правила переходов между
    состояниями, определение победителя, фиксацию ничьих и ведение
    счета побед за всю игровую сессию.
    """

    def __init__(self) -> None:
        """Инициализация новой модели с начальными параметрами."""
        self._scores: Dict[str, int] = {
            PLAYER_X: 0,
            PLAYER_O: 0,
            "draws": 0
        }
        self._starting_player: str = PLAYER_X
        self._current_player: str = PLAYER_X
        self._board: List[List[str]] = [
            [EMPTY_CELL for _ in range(BOARD_SIZE)]
            for _ in range(BOARD_SIZE)
        ]
        self._is_game_over: bool = False
        self._winner: Optional[str] = None
        self._winning_line: Optional[List[Tuple[int, int]]] = None
        self._move_history: List[MoveRecord] = []

    @property
    def current_player(self) -> str:
        """Возвращает идентификатор текущего активного игрока."""
        return self._current_player

    @property
    def scores(self) -> Dict[str, int]:
        """Возвращает копию текущего счета матча."""
        return self._scores.copy()

    @property
    def is_game_over(self) -> bool:
        """Возвращает флаг завершения текущей партии."""
        return self._is_game_over

    @property
    def winner(self) -> Optional[str]:
        """Возвращает победителя текущей партии (или None при ничьей/в процессе)."""
        return self._winner

    @property
    def winning_line(self) -> Optional[List[Tuple[int, int]]]:
        """Возвращает список координат победной комбинации клеток (если есть)."""
        return list(self._winning_line) if self._winning_line else None

    @property
    def move_history(self) -> List[MoveRecord]:
        """Возвращает историю ходов текущей партии."""
        return list(self._move_history)

    def get_board_state(self) -> List[List[str]]:
        """Возвращает глубокую копию игрового поля 3x3.

        Защищает внутреннее состояние от непреднамеренной модификации извне.
        """
        return copy.deepcopy(self._board)

    def get_cell(self, row: int, col: int) -> str:
        """Получить значение конкретной клетки поля.

        Args:
            row: Индекс строки (0..2).
            col: Индекс столбца (0..2).

        Raises:
            InvalidCoordinateError: Если координаты выходят за границы матрицы 3x3.
        """
        self._validate_coordinates(row, col)
        return self._board[row][col]

    def make_move(self, row: int, col: int) -> Tuple[Optional[str], Optional[List[Tuple[int, int]]]]:
        """Выполнить ход текущим игроком в указанную клетку.

        Args:
            row: Индекс строки (0..2).
            col: Индекс столбца (0..2).

        Returns:
            Tuple[Optional[str], Optional[List[Tuple[int, int]]]]:
                (победитель, координаты победной линии).
                Если партия завершилась победой, возвращается ('X' или 'O', список клеток).
                Если партия завершилась вничью, возвращается ('draw', None).
                Если игра продолжается, возвращается (None, None).

        Raises:
            GameOverError: Если партия уже завершена.
            InvalidCoordinateError: Если координаты выходят за диапазон [0, 2].
            CellOccupiedError: Если целевая клетка уже занята.
        """
        if self._is_game_over:
            raise GameOverError("Невозможно сделать ход: текущая партия уже завершена.")

        self._validate_coordinates(row, col)

        if self._board[row][col] != EMPTY_CELL:
            raise CellOccupiedError(f"Клетка ({row}, {col}) уже занята символом '{self._board[row][col]}'.")

        # Фиксация хода
        active_player = self._current_player
        self._board[row][col] = active_player
        step_number = len(self._move_history) + 1
        self._move_history.append(
            MoveRecord(
                player=active_player,
                row=row,
                col=col,
                step_number=step_number
            )
        )

        # Проверка победы
        win_result = self._check_winning_combinations()
        if win_result is not None:
            winner_symbol, win_coords = win_result
            self._is_game_over = True
            self._winner = winner_symbol
            self._winning_line = win_coords
            self._scores[winner_symbol] += 1
            return winner_symbol, win_coords

        # Проверка ничьей (все клетки заполнены, победителя нет)
        if self.is_board_full():
            self._is_game_over = True
            self._winner = None
            self._winning_line = None
            self._scores["draws"] += 1
            return "draw", None

        # Передача хода следующему игроку
        self._current_player = PLAYER_O if active_player == PLAYER_X else PLAYER_X
        return None, None

    def is_board_full(self) -> bool:
        """Проверяет, заполнены ли все 9 клеток поля."""
        for row in self._board:
            for cell in row:
                if cell == EMPTY_CELL:
                    return False
        return True

    def new_game(self, alternate_starting_player: bool = True) -> None:
        """Начать новую партию со сбросом поля и сохранением общего счета.

        Args:
            alternate_starting_player: Если True, первый ход переходит к другому игроку.
        """
        self._board = [
            [EMPTY_CELL for _ in range(BOARD_SIZE)]
            for _ in range(BOARD_SIZE)
        ]
        self._is_game_over = False
        self._winner = None
        self._winning_line = None
        self._move_history.clear()

        if alternate_starting_player:
            self._starting_player = (
                PLAYER_O if self._starting_player == PLAYER_X else PLAYER_X
            )
        self._current_player = self._starting_player

    def reset_scores(self) -> None:
        """Полный сброс турнирного счета сессии."""
        self._scores = {
            PLAYER_X: 0,
            PLAYER_O: 0,
            "draws": 0
        }

    def _validate_coordinates(self, row: int, col: int) -> None:
        """Внутренняя валидация индексов строки и столбца."""
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise InvalidCoordinateError(
                f"Некорректные координаты ({row}, {col}). Ожидаются значения в диапазоне 0..{BOARD_SIZE - 1}."
            )

    def _check_winning_combinations(self) -> Optional[Tuple[str, List[Tuple[int, int]]]]:
        """Проверка всех возможных 8 выигрышных линий на поле.

        Returns:
            Tuple[str, List[Tuple[int, int]]] или None:
                Кортеж (победитель, координаты линии), если найден, иначе None.
        """
        # 1. Проверка горизонталей (строки)
        for r in range(BOARD_SIZE):
            if (self._board[r][0] != EMPTY_CELL and
                    self._board[r][0] == self._board[r][1] == self._board[r][2]):
                return self._board[r][0], [(r, 0), (r, 1), (r, 2)]

        # 2. Проверка вертикалей (столбцы)
        for c in range(BOARD_SIZE):
            if (self._board[0][c] != EMPTY_CELL and
                    self._board[0][c] == self._board[1][c] == self._board[2][c]):
                return self._board[0][c], [(0, c), (1, c), (2, c)]

        # 3. Главная диагональ (сверху-слева направо-вниз)
        if (self._board[0][0] != EMPTY_CELL and
                self._board[0][0] == self._board[1][1] == self._board[2][2]):
            return self._board[0][0], [(0, 0), (1, 1), (2, 2)]

        # 4. Побочная диагональ (сверху-справа налево-вниз)
        if (self._board[0][2] != EMPTY_CELL and
                self._board[0][2] == self._board[1][1] == self._board[2][0]):
            return self._board[0][2], [(0, 2), (1, 1), (2, 0)]

        return None
