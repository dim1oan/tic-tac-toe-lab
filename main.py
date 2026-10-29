"""Главный графический модуль приложения «Крестики-нолики».

Реализует слой представления (View) и контроллера (Controller)
на базе библиотеки Tkinter с адаптивной темной темой.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Final, List, Optional
from model import (
    GameModel,
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    CellOccupiedError,
    GameOverError,
)

# Палитра темной темы оформления (Catppuccin / Modern Dark)
COLOR_BG_MAIN: Final[str] = "#181825"
COLOR_BG_CARD: Final[str] = "#1e1e2e"
COLOR_BG_CELL: Final[str] = "#313244"
COLOR_BG_CELL_HOVER: Final[str] = "#45475a"
COLOR_TEXT_PRIMARY: Final[str] = "#cdd6f4"
COLOR_TEXT_MUTED: Final[str] = "#a6adc8"
COLOR_PLAYER_X: Final[str] = "#89b4fa"      # Светло-синий
COLOR_PLAYER_O: Final[str] = "#f38ba8"      # Кораллово-розовый
COLOR_WIN_BG: Final[str] = "#a6e3a1"        # Мятно-зеленая подсветка победы
COLOR_WIN_FG: Final[str] = "#11111b"


class TicTacToeApp:
    """Главный класс графического интерфейса игры (View/Controller).

    Отвечает за отрисовку элементов управления, адаптивную компоновку
    с использованием менеджера сетки (grid), обработку событий ввода
    и отображение текущего состояния модели.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Инициализация главного окна и компонентов интерфейса."""
        self.root: tk.Tk = root
        self.root.title("Крестики-нолики — Лабораторная работа")
        self.root.geometry("600x700")
        self.root.minsize(360, 460)
        self.root.configure(bg=COLOR_BG_MAIN)

        # Экземпляр игровой модели
        self.model: GameModel = GameModel()

        # Матрица кнопок игрового поля 3x3
        self.buttons: List[List[tk.Button]] = []

        # Шрифты интерфейса
        self._init_fonts()

        # Построение интерфейса
        self._build_header_panel()
        self._build_board_grid()
        self._build_status_bar()

        # Обновление начального состояния
        self._update_ui_state()

    def _init_fonts(self) -> None:
        """Инициализация масштабируемых шрифтов приложения."""
        self.font_score_title = tkfont.Font(family="Segoe UI", size=10, weight="normal")
        self.font_score_val = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.font_turn = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.font_cell = tkfont.Font(family="Segoe UI", size=36, weight="bold")
        self.font_status = tkfont.Font(family="Segoe UI", size=10, weight="normal")

    def _build_header_panel(self) -> None:
        """Построение верхней информационной панели со счетом и индикатором хода."""
        self.header_frame = tk.Frame(self.root, bg=COLOR_BG_CARD, padx=16, pady=12)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(16, 8))

        # Настройка адаптивных столбцов карточки счета
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.columnconfigure(1, weight=1)
        self.header_frame.columnconfigure(2, weight=1)

        # Карточка счета игрока X
        self.lbl_score_x = tk.Label(
            self.header_frame,
            text="Игрок X\n0",
            font=self.font_score_val,
            fg=COLOR_PLAYER_X,
            bg=COLOR_BG_CARD,
            justify=tk.CENTER
        )
        self.lbl_score_x.grid(row=0, column=0, sticky="nsew")

        # Карточка ничьих
        self.lbl_score_draws = tk.Label(
            self.header_frame,
            text="Ничьи\n0",
            font=self.font_score_val,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_CARD,
            justify=tk.CENTER
        )
        self.lbl_score_draws.grid(row=0, column=1, sticky="nsew")

        # Карточка счета игрока O
        self.lbl_score_o = tk.Label(
            self.header_frame,
            text="Игрок O\n0",
            font=self.font_score_val,
            fg=COLOR_PLAYER_O,
            bg=COLOR_BG_CARD,
            justify=tk.CENTER
        )
        self.lbl_score_o.grid(row=0, column=2, sticky="nsew")

        # Индикатор текущего хода
        self.lbl_turn = tk.Label(
            self.header_frame,
            text="Ход игрока: X",
            font=self.font_turn,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_CARD,
            pady=6
        )
        self.lbl_turn.grid(row=1, column=0, columnspan=3, pady=(8, 0))

    def _build_board_grid(self) -> None:
        """Построение адаптивной сетки 3x3 для игрового поля."""
        self.board_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN, padx=16, pady=8)
        self.board_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Конфигурация равных весов (weight=1) для адаптивного ресайзинга
        for i in range(3):
            self.board_frame.rowconfigure(i, weight=1, uniform="board_row")
            self.board_frame.columnconfigure(i, weight=1, uniform="board_col")

        self.buttons = []
        for r in range(3):
            row_buttons: List[tk.Button] = []
            for c in range(3):
                btn = tk.Button(
                    self.board_frame,
                    text="",
                    font=self.font_cell,
                    bg=COLOR_BG_CELL,
                    activebackground=COLOR_BG_CELL_HOVER,
                    relief=tk.FLAT,
                    bd=0,
                    cursor="hand2",
                    command=lambda row=r, col=c: self._handle_cell_click(row, col)
                )
                btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

                # Добавление эффекта наведения (hover)
                btn.bind("<Enter>", lambda e, b=btn, row=r, col=c: self._on_cell_hover_enter(b, row, col))
                btn.bind("<Leave>", lambda e, b=btn, row=r, col=c: self._on_cell_hover_leave(b, row, col))

                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def _build_status_bar(self) -> None:
        """Построение нижней строки состояния."""
        self.status_bar = tk.Label(
            self.root,
            text="Готов к игре | Разрешение: 600x700",
            font=self.font_status,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_MAIN,
            anchor="w",
            padx=16,
            pady=8
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_cell_hover_enter(self, button: tk.Button, row: int, col: int) -> None:
        """Подсветка клетки при наведении курсора мыши (если она пуста)."""
        if not self.model.is_game_over and self.model.get_cell(row, col) == EMPTY_CELL:
            button.configure(bg=COLOR_BG_CELL_HOVER)

    def _on_cell_hover_leave(self, button: tk.Button, row: int, col: int) -> None:
        """Возврат цвета клетки при уходе курсора мыши."""
        if not self.model.is_game_over and self.model.get_cell(row, col) == EMPTY_CELL:
            button.configure(bg=COLOR_BG_CELL)

    def _handle_cell_click(self, row: int, col: int) -> None:
        """Обработка клика по клетке с перехватом исключений."""
        try:
            winner, win_line = self.model.make_move(row, col)
            self._render_move(row, col)

            if winner is not None:
                self._handle_game_finished(winner, win_line)
            else:
                self._update_turn_indicator()

        except CellOccupiedError:
            # Игнорируем клик по уже занятой клетке
            pass
        except GameOverError:
            # Игнорируем клик после окончания партии
            pass

    def _render_move(self, row: int, col: int) -> None:
        """Отображение установленного символа на кнопке поля."""
        cell_value = self.model.get_cell(row, col)
        btn = self.buttons[row][col]
        color = COLOR_PLAYER_X if cell_value == PLAYER_X else COLOR_PLAYER_O
        btn.configure(
            text=cell_value,
            fg=color,
            bg=COLOR_BG_CELL,
            activeforeground=color
        )

    def _handle_game_finished(self, winner: str, win_line: Optional[List[tuple]]) -> None:
        """Обработка завершения партии (победа или ничья)."""
        if winner == "draw":
            self.lbl_turn.configure(
                text="Ничья! Ни один игрок не уступил.",
                fg=COLOR_TEXT_MUTED
            )
            self.status_bar.configure(text="Партия завершена: Боевая ничья")
        else:
            self.lbl_turn.configure(
                text=f"Победил Игрок {winner}!",
                fg=COLOR_PLAYER_X if winner == PLAYER_X else COLOR_PLAYER_O
            )
            self.status_bar.configure(text=f"Партия завершена: Победа Игрока {winner}")

            # Подсветка выигрышной комбинации
            if win_line:
                for r, c in win_line:
                    self.buttons[r][c].configure(
                        bg=COLOR_WIN_BG,
                        fg=COLOR_WIN_FG,
                        activebackground=COLOR_WIN_BG,
                        activeforeground=COLOR_WIN_FG
                    )

        self._update_score_labels()

    def _update_turn_indicator(self) -> None:
        """Обновление индикатора очередности хода."""
        curr = self.model.current_player
        color = COLOR_PLAYER_X if curr == PLAYER_X else COLOR_PLAYER_O
        self.lbl_turn.configure(
            text=f"Ход игрока: {curr}",
            fg=color
        )

    def _update_score_labels(self) -> None:
        """Обновление карточек счета."""
        scores = self.model.scores
        self.lbl_score_x.configure(text=f"Игрок X\n{scores[PLAYER_X]}")
        self.lbl_score_draws.configure(text=f"Ничьи\n{scores['draws']}")
        self.lbl_score_o.configure(text=f"Игрок O\n{scores[PLAYER_O]}")

    def _update_ui_state(self) -> None:
        """Полная синхронизация интерфейса с моделью."""
        self._update_score_labels()
        self._update_turn_indicator()


def main() -> None:
    """Точка входа в графическое приложение."""
    root = tk.Tk()
    app = TicTacToeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
