"""Модульные тесты для проверки предметной логики модели GameModel.

Запуск тестов:
    python -m unittest test_model.py
"""

import unittest
from model import (
    GameModel,
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    CellOccupiedError,
    GameOverError,
    InvalidCoordinateError,
)


class TestGameModel(unittest.TestCase):
    """Набор тестов для проверки корректности игровой модели."""

    def setUp(self) -> None:
        """Создание нового экземпляра модели перед каждым тестом."""
        self.model = GameModel()

    def test_initial_state(self) -> None:
        """Проверка начального состояния игрового поля и параметров."""
        self.assertEqual(self.model.current_player, PLAYER_X)
        self.assertFalse(self.model.is_game_over)
        self.assertIsNone(self.model.winner)
        self.assertEqual(len(self.model.move_history), 0)

        board = self.model.get_board_state()
        for r in range(3):
            for c in range(3):
                self.assertEqual(board[r][c], EMPTY_CELL)

    def test_alternate_turns(self) -> None:
        """Проверка чередования ходов между X и O."""
        self.model.make_move(0, 0)
        self.assertEqual(self.model.current_player, PLAYER_O)
        self.model.make_move(1, 1)
        self.assertEqual(self.model.current_player, PLAYER_X)

    def test_occupied_cell_exception(self) -> None:
        """Проверка возбуждения исключения CellOccupiedError при повторном клике."""
        self.model.make_move(0, 0)
        with self.assertRaises(CellOccupiedError):
            self.model.make_move(0, 0)

    def test_invalid_coordinates_exception(self) -> None:
        """Проверка возбуждения исключения InvalidCoordinateError."""
        with self.assertRaises(InvalidCoordinateError):
            self.model.make_move(3, 0)
        with self.assertRaises(InvalidCoordinateError):
            self.model.make_move(-1, 2)

    def test_horizontal_win(self) -> None:
        """Проверка победы по горизонтальной строке."""
        # X: (0,0), O: (1,0), X: (0,1), O: (1,1), X: (0,2) -> Победа X
        self.model.make_move(0, 0)
        self.model.make_move(1, 0)
        self.model.make_move(0, 1)
        self.model.make_move(1, 1)
        winner, line = self.model.make_move(0, 2)

        self.assertEqual(winner, PLAYER_X)
        self.assertEqual(line, [(0, 0), (0, 1), (0, 2)])
        self.assertTrue(self.model.is_game_over)
        self.assertEqual(self.model.scores[PLAYER_X], 1)

    def test_vertical_win(self) -> None:
        """Проверка победы по вертикальному столбцу."""
        # X: (0,0), O: (0,1), X: (1,0), O: (1,1), X: (2,0) -> Победа X
        self.model.make_move(0, 0)
        self.model.make_move(0, 1)
        self.model.make_move(1, 0)
        self.model.make_move(1, 1)
        winner, line = self.model.make_move(2, 0)

        self.assertEqual(winner, PLAYER_X)
        self.assertEqual(line, [(0, 0), (1, 0), (2, 0)])
        self.assertTrue(self.model.is_game_over)

    def test_diagonal_win(self) -> None:
        """Проверка победы по диагонали."""
        # X: (0,0), O: (0,1), X: (1,1), O: (0,2), X: (2,2) -> Победа X
        self.model.make_move(0, 0)
        self.model.make_move(0, 1)
        self.model.make_move(1, 1)
        self.model.make_move(0, 2)
        winner, line = self.model.make_move(2, 2)

        self.assertEqual(winner, PLAYER_X)
        self.assertEqual(line, [(0, 0), (1, 1), (2, 2)])
        self.assertTrue(self.model.is_game_over)

    def test_draw_condition(self) -> None:
        """Проверка сценария ничьей при заполнении всех 9 клеток без победителя."""
        # Сетка:
        # X O X
        # X O O
        # O X X
        moves = [
            (0, 0),  # X
            (0, 1),  # O
            (0, 2),  # X
            (1, 1),  # O
            (1, 0),  # X
            (1, 2),  # O
            (2, 1),  # X
            (2, 0),  # O
            (2, 2),  # X
        ]
        winner = None
        for r, c in moves:
            winner, _ = self.model.make_move(r, c)

        self.assertEqual(winner, "draw")
        self.assertTrue(self.model.is_game_over)
        self.assertIsNone(self.model.winner)
        self.assertEqual(self.model.scores["draws"], 1)

    def test_move_after_game_over_raises_exception(self) -> None:
        """Проверка невозможности совершения хода после окончания партии."""
        self.model.make_move(0, 0)
        self.model.make_move(1, 0)
        self.model.make_move(0, 1)
        self.model.make_move(1, 1)
        self.model.make_move(0, 2)  # X побеждает

        with self.assertRaises(GameOverError):
            self.model.make_move(2, 2)

    def test_new_game_preserves_scores(self) -> None:
        """Проверка сохранения счета при старте новой партии."""
        self.model.make_move(0, 0)
        self.model.make_move(1, 0)
        self.model.make_move(0, 1)
        self.model.make_move(1, 1)
        self.model.make_move(0, 2)  # Победа X

        self.model.new_game(alternate_starting_player=True)
        self.assertFalse(self.model.is_game_over)
        self.assertEqual(self.model.scores[PLAYER_X], 1)
        self.assertEqual(self.model.current_player, PLAYER_O)  # Очередность перешла к O


if __name__ == "__main__":
    unittest.main()
