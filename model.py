"""Модуль предметной логики (Model) для игры «Крестики-нолики».

Данный модуль реализует архитектурный слой модели (Model) в рамках паттерна
MVC (Model-View-Controller) и функционирует независимо от графического
интерфейса пользователя (UI).

Основные компоненты:
    - Константы символов игроков и игрового поля.
    - Иерархия пользовательских исключений `TicTacToeException`.
    - Неизменяемая структура данных `MoveRecord` для логирования ходов.
    - Класс `GameModel` — центральный автомат состояний игры.

Соответствие стандартам:
    - PEP 8 (Code Style).
    - PEP 484 (Type Hints).
    - PEP 257 (Docstring Conventions).
"""

from dataclasses import dataclass
import copy
import logging
from typing import Dict, Final, List, Optional, Tuple

# Настройка модуля логирования для трассировки событий модели
logger: logging.Logger = logging.getLogger(__name__)

# Символьные константы игроков и пустого пространства
PLAYER_X: Final[str] = "X"
PLAYER_O: Final[str] = "O"
EMPTY_CELL: Final[str] = ""
DRAW_RESULT: Final[str] = "draw"
BOARD_SIZE: Final[int] = 3


class TicTacToeException(Exception):
    """Базовое исключение для ошибок доменной логики игры 'Крестики-нолики'."""

    pass


class InvalidCoordinateError(TicTacToeException):
    """Возбуждается при передаче координат клетки вне допустимого диапазона 0..2."""

    pass


class CellOccupiedError(TicTacToeException):
    """Возбуждается при попытке совершить ход в уже занятую клетку игрового поля."""

    pass


class GameOverError(TicTacToeException):
    """Возбуждается при попытке выполнения игрового действия после завершения партии."""

    pass


@dataclass(frozen=True)
class MoveRecord:
    """Неизменяемый снимок совершенного игрового хода (Value Object).

    Attributes:
        player: Строковый маркер игрока ('X' или 'O').
        row: Индекс строки поля (диапазон 0..2).
        col: Индекс столбца поля (диапазон 0..2).
        step_number: Порядковый номер хода в текущей партии.
    """

    player: str
    row: int
    col: int
    step_number: int


class GameModel:
    """Модель предметной области (Model) классической игры «Крестики-нолики».

    Инкапсулирует:
        - Матрицу состояния сетки 3x3.
        - Контроль очередности ходов.
        - Алгоритмическую проверку 8 выигрышных линий (3 горизонтали,
          3 вертикали и 2 диагонали) и критерия ничейного исхода.
        - Ведение турнирной статистики сессии (победы X, победы O, ничьи).
        - Полную историю сделанных ходов с защитой от внешних мутаций.
    """

    def __init__(self) -> None:
        """Конструктор модели: инициализирует пустое поле и счетчики сессии."""
        # Турнирный счет текущего игрового сеанса
        self._scores: Dict[str, int] = {
            PLAYER_X: 0,
            PLAYER_O: 0,
            "draws": 0,
        }

        # Очередность стартового игрока (для поочередной смены в новых партиях)
        self._starting_player: str = PLAYER_X
        self._current_player: str = PLAYER_X

        # Внутреннее представление поля в виде двумерного списка 3x3
        self._board: List[List[str]] = [
            [EMPTY_CELL for _ in range(BOARD_SIZE)]
            for _ in range(BOARD_SIZE)
        ]

        # Флаги терминального состояния партии
        self._is_game_over: bool = False
        self._winner: Optional[str] = None
        self._winning_line: Optional[List[Tuple[int, int]]] = None

        # Журнал ходов текущей партии
        self._move_history: List[MoveRecord] = []

        logger.info("Игровая модель GameModel успешно инициализирована.")

    # -------------------------------------------------------------------------
    # Публичные свойства для безопасного чтения внутреннего состояния (Read-only)
    # -------------------------------------------------------------------------

    @property
    def current_player(self) -> str:
        """Возвращает маркер игрока, чей ход ожидается в данный момент."""
        return self._current_player

    @property
    def scores(self) -> Dict[str, int]:
        """Возвращает копию словаря турнирного счета за текущую сессию."""
        return self._scores.copy()

    @property
    def is_game_over(self) -> bool:
        """Возвращает True, если текущая партия завершилась победой или ничьей."""
        return self._is_game_over

    @property
    def winner(self) -> Optional[str]:
        """Возвращает маркер победителя партии ('X' или 'O'), либо None."""
        return self._winner

    @property
    def winning_line(self) -> Optional[List[Tuple[int, int]]]:
        """Возвращает список из трех координат клеток выигрышной комбинации."""
        return list(self._winning_line) if self._winning_line else None

    @property
    def move_history(self) -> List[MoveRecord]:
        """Возвращает поверхностную копию истории ходов текущей партии."""
        return list(self._move_history)

    # -------------------------------------------------------------------------
    # Публичные методы взаимодействия
    # -------------------------------------------------------------------------

    def get_board_state(self) -> List[List[str]]:
        """Возвращает глубокую копию матрицы 3x3 состояния игрового поля.

        Принцип защитного копирования (Defensive Copy) предотвращает
        случайную мутацию внутренней матрицы из внешних модулей UI.

        Returns:
            List[List[str]]: Копия текущего состояния поля 3x3.
        """
        return copy.deepcopy(self._board)

    def get_cell(self, row: int, col: int) -> str:
        """Возвращает текущее состояние ячейки поля по заданным координатам.

        Args:
            row: Индекс строки (0..2).
            col: Индекс столбца (0..2).

        Returns:
            str: 'X', 'O' или пустая строка ''.

        Raises:
            InvalidCoordinateError: Если переданные индексы лежат вне границ [0, 2].
        """
        self._validate_coordinates(row, col)
        return self._board[row][col]

    def make_move(
        self, row: int, col: int
    ) -> Tuple[Optional[str], Optional[List[Tuple[int, int]]]]:
        """Фиксация игрового хода активного участника с валидацией состояния.

        Последовательность алгоритма:
            1. Проверка флага завершения партии (возбуждение GameOverError).
            2. Валидация диапазона координат (InvalidCoordinateError).
            3. Проверка пустоты выбранной клетки (CellOccupiedError).
            4. Запись символа активного игрока и сохранение шага в истории.
            5. Проверка выигрышных линий (8 направлений).
            6. Проверка условия ничьей (заполненность всех 9 ячеек).
            7. Переключение очередности хода при отсутствии победы/ничьей.

        Args:
            row: Индекс строки (0..2).
            col: Индекс столбца (0..2).

        Returns:
            Tuple[Optional[str], Optional[List[Tuple[int, int]]]]:
                - ('X' | 'O', координаты линии) — при наступлении победы;
                - ('draw', None) — при наступлении ничьей;
                - (None, None) — если партия продолжается.

        Raises:
            GameOverError: При попытке хода после финального свистка.
            InvalidCoordinateError: При координатах вне матрицы 3x3.
            CellOccupiedError: При клике по уже заполненной ячейке.
        """
        if self._is_game_over:
            logger.warning(
                "Попытка хода в завершенной партии: (%d, %d)", row, col
            )
            raise GameOverError("Невозможно сделать ход: текущая партия уже завершена.")

        self._validate_coordinates(row, col)

        if self._board[row][col] != EMPTY_CELL:
            logger.warning(
                "Попытка хода в занятую клетку (%d, %d): занята '%s'",
                row,
                col,
                self._board[row][col],
            )
            raise CellOccupiedError(
                f"Клетка ({row}, {col}) уже занята символом '{self._board[row][col]}'."
            )

        # 4. Фиксация хода
        active_player = self._current_player
        self._board[row][col] = active_player
        step_number = len(self._move_history) + 1

        record = MoveRecord(
            player=active_player,
            row=row,
            col=col,
            step_number=step_number,
        )
        self._move_history.append(record)

        logger.info(
            "Ход #%d: Игрок '%s' -> клетка (%d, %d)",
            step_number,
            active_player,
            row,
            col,
        )

        # 5. Проверка условий победы
        win_result = self._check_winning_combinations()
        if win_result is not None:
            winner_symbol, win_coords = win_result
            self._is_game_over = True
            self._winner = winner_symbol
            self._winning_line = win_coords
            self._scores[winner_symbol] += 1

            logger.info(
                "Партия окончена победой игрока '%s'. Линия: %s. Новый счет: %s",
                winner_symbol,
                win_coords,
                self._scores,
            )
            return winner_symbol, win_coords

        # 6. Проверка условия ничьей
        if self.is_board_full():
            self._is_game_over = True
            self._winner = None
            self._winning_line = None
            self._scores["draws"] += 1

            logger.info("Партия завершилась вничью. Новый счет: %s", self._scores)
            return DRAW_RESULT, None

        # 7. Чередование хода следующего игрока
        self._current_player = PLAYER_O if active_player == PLAYER_X else PLAYER_X
        return None, None

    def is_board_full(self) -> bool:
        """Определяет, заполнены ли все 9 ячеек игрового поля.

        Returns:
            bool: True, если на поле нет свободных ячеек, иначе False.
        """
        for row in self._board:
            for cell in row:
                if cell == EMPTY_CELL:
                    return False
        return True

    def new_game(self, alternate_starting_player: bool = True) -> None:
        """Сброс состояния доски и подготовка к новой партии.

        Общий накопленный счет побед и поражений сохраняется без изменений.

        Args:
            alternate_starting_player: Если True, право первого хода переходит
                ко второму игроку для обеспечения соревновательного паритета.
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

        logger.info(
            "Старт новой партии. Первый ход принадлежит игроку '%s'.",
            self._current_player,
        )

    def reset_scores(self) -> None:
        """Полный сброс турнирной таблицы сеанса к начальным нулям."""
        self._scores = {
            PLAYER_X: 0,
            PLAYER_O: 0,
            "draws": 0,
        }
        logger.info("Турнирный счет успешно обнулен.")

    # -------------------------------------------------------------------------
    # Внутренние служебные методы валидации и проверки условий
    # -------------------------------------------------------------------------

    def _validate_coordinates(self, row: int, col: int) -> None:
        """Проверяет корректность диапазона переданных координат ячейки.

        Args:
            row: Индекс строки.
            col: Индекс столбца.

        Raises:
            InvalidCoordinateError: Если индексы выходят за границы матрицы 3x3.
        """
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise InvalidCoordinateError(
                f"Некорректные координаты клетки ({row}, {col}). "
                f"Ожидаются значения в диапазоне 0..{BOARD_SIZE - 1}."
            )

    def _check_winning_combinations(
        self,
    ) -> Optional[Tuple[str, List[Tuple[int, int]]]]:
        """Проверяет матрицу на наличие победных линий (горизонтали, вертикали, диагонали).

        Анализируются ровно 8 геометрических прямых линий:
            - 3 строки (r = 0, 1, 2)
            - 3 столбца (c = 0, 1, 2)
            - Главная диагональ [(0,0), (1,1), (2,2)]
            - Побочная диагональ [(0,2), (1,1), (2,0)]

        Returns:
            Optional[Tuple[str, List[Tuple[int, int]]]]:
                Символ победителя и список координат выигрышных ячеек
                или None, если победная конфигурация не обнаружена.
        """
        # 1. Проверка горизонтальных строк
        for r in range(BOARD_SIZE):
            if (
                self._board[r][0] != EMPTY_CELL
                and self._board[r][0] == self._board[r][1] == self._board[r][2]
            ):
                return self._board[r][0], [(r, 0), (r, 1), (r, 2)]

        # 2. Проверка вертикальных столбцов
        for c in range(BOARD_SIZE):
            if (
                self._board[0][c] != EMPTY_CELL
                and self._board[0][c] == self._board[1][c] == self._board[2][c]
            ):
                return self._board[0][c], [(0, c), (1, c), (2, c)]

        # 3. Главная диагональ (сверху-слева вниз-направо)
        if (
            self._board[0][0] != EMPTY_CELL
            and self._board[0][0] == self._board[1][1] == self._board[2][2]
        ):
            return self._board[0][0], [(0, 0), (1, 1), (2, 2)]

        # 4. Побочная диагональ (сверху-справа вниз-налево)
        if (
            self._board[0][2] != EMPTY_CELL
            and self._board[0][2] == self._board[1][1] == self._board[2][0]
        ):
            return self._board[0][2], [(0, 2), (1, 1), (2, 0)]

        return None
