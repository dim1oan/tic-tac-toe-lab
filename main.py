"""Главный графический модуль приложения «Крестики-нолики».

Реализует слой представления (View) и контроллера (Controller)
на базе библиотеки Tkinter с адаптивной темной темой, верхним меню,
настройками разрешения окна и отказоустойчивой обработкой исключений.
"""

import re
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog
from typing import Final, List, Optional, Tuple
from model import (
    GameModel,
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    CellOccupiedError,
    GameOverError,
)

# Палитра темной темы оформления (Modern Dark / Catppuccin)
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

# Ограничения геометрии окна
MIN_WINDOW_WIDTH: Final[int] = 360
MIN_WINDOW_HEIGHT: Final[int] = 460
MAX_WINDOW_WIDTH: Final[int] = 2560
MAX_WINDOW_HEIGHT: Final[int] = 1600


class TicTacToeApp:
    """Главный класс графического интерфейса игры (View/Controller).

    Отвечает за отрисовку элементов управления, адаптивную компоновку
    с использованием менеджера сетки (grid), меню программы, масштабирование
    окна и обработку исключений.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Инициализация главного окна и компонентов интерфейса."""
        self.root: tk.Tk = root
        self.root.title("Крестики-нолики — Лабораторная работа")
        self.root.geometry("600x700")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.configure(bg=COLOR_BG_MAIN)

        # Состояние полноэкранного режима
        self._is_fullscreen: bool = False
        self._prev_geometry: str = "600x700"

        # Экземпляр игровой модели
        self.model: GameModel = GameModel()

        # Матрица кнопок игрового поля 3x3
        self.buttons: List[List[tk.Button]] = []

        # Шрифты интерфейса
        self._init_fonts()

        # Построение меню и интерфейса
        self._build_menu()
        self._build_header_panel()
        self._build_board_grid()
        self._build_status_bar()

        # Привязка горячих клавиш
        self._bind_shortcuts()

        # Перехват закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Обновление начального состояния
        self._update_ui_state()

    def _init_fonts(self) -> None:
        """Инициализация масштабируемых шрифтов приложения."""
        self.font_score_title = tkfont.Font(family="Segoe UI", size=10, weight="normal")
        self.font_score_val = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.font_turn = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.font_cell = tkfont.Font(family="Segoe UI", size=36, weight="bold")
        self.font_status = tkfont.Font(family="Segoe UI", size=10, weight="normal")

    def _build_menu(self) -> None:
        """Построение верхнего меню приложения (tkinter.Menu)."""
        menubar = tk.Menu(self.root, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY)

        # Меню 1: «Игра»
        game_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY)
        game_menu.add_command(label="Новая партия (Ctrl+N)", command=self.action_new_game)
        game_menu.add_command(label="Сброс счета (Ctrl+R)", command=self.action_reset_scores)
        game_menu.add_separator()
        game_menu.add_command(label="Выход (Ctrl+Q)", command=self.on_exit)
        menubar.add_cascade(label="Игра", menu=game_menu)

        # Меню 2: «Настройки окна»
        settings_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY)
        settings_menu.add_command(
            label="Разрешение: 400 × 500 (Компактный)",
            command=lambda: self.apply_preset_geometry(400, 500)
        )
        settings_menu.add_command(
            label="Разрешение: 600 × 700 (Стандартный)",
            command=lambda: self.apply_preset_geometry(600, 700)
        )
        settings_menu.add_command(
            label="Разрешение: 800 × 900 (Просторный)",
            command=lambda: self.apply_preset_geometry(800, 900)
        )
        settings_menu.add_separator()
        settings_menu.add_command(
            label="Пользовательский размер...",
            command=self.prompt_custom_resolution
        )
        settings_menu.add_separator()
        settings_menu.add_command(
            label="Полноэкранный режим (F11)",
            command=self.toggle_fullscreen
        )
        menubar.add_cascade(label="Настройки окна", menu=settings_menu)

        # Меню 3: «Справка»
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY)
        help_menu.add_command(label="Правила игры", command=self.show_rules)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_header_panel(self) -> None:
        """Построение информационной панели со счетом и индикатором хода."""
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

        # Конфигурация равных весов (weight=1) для плавного ресайзинга
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

                # Эффект подсветки клетки при наведении
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

    def _bind_shortcuts(self) -> None:
        """Привязка горячих клавиш клавиатуры."""
        self.root.bind("<Control-n>", lambda event: self.action_new_game())
        self.root.bind("<Control-N>", lambda event: self.action_new_game())
        self.root.bind("<Control-r>", lambda event: self.action_reset_scores())
        self.root.bind("<Control-R>", lambda event: self.action_reset_scores())
        self.root.bind("<Control-q>", lambda event: self.on_exit())
        self.root.bind("<Control-Q>", lambda event: self.on_exit())
        self.root.bind("<F11>", lambda event: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda event: self._exit_fullscreen())

    def _on_cell_hover_enter(self, button: tk.Button, row: int, col: int) -> None:
        """Подсветка свободной клетки при наведении мыши."""
        if not self.model.is_game_over and self.model.get_cell(row, col) == EMPTY_CELL:
            button.configure(bg=COLOR_BG_CELL_HOVER)

    def _on_cell_hover_leave(self, button: tk.Button, row: int, col: int) -> None:
        """Возврат исходного цвета при уходе курсора мыши."""
        if not self.model.is_game_over and self.model.get_cell(row, col) == EMPTY_CELL:
            button.configure(bg=COLOR_BG_CELL)

    def _handle_cell_click(self, row: int, col: int) -> None:
        """Обработка нажатия на клетку с защитой от ошибок и падений GUI."""
        try:
            winner, win_line = self.model.make_move(row, col)
            self._render_move(row, col)

            if winner is not None:
                self._handle_game_finished(winner, win_line)
            else:
                self._update_turn_indicator()

        except CellOccupiedError:
            # Предотвращение изменения уже занятой клетки
            self.status_bar.configure(text=f"Предупреждение: Клетка [{row + 1}, {col + 1}] уже занята!")
        except GameOverError:
            # Предотвращение ходов после завершения игры
            self.status_bar.configure(text="Партия уже окончена. Нажмите 'Новая партия' (Ctrl+N).")
        except Exception as exc:
            # Безопасный перехват непредвиденных исключений
            messagebox.showerror(
                "Ошибка игрового процесса",
                f"Произошла непредвиденная ошибка при обработке хода:\n{exc}"
            )

    def _render_move(self, row: int, col: int) -> None:
        """Отрисовка хода в соответствующей кнопке сетки."""
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
        """Отображение результатов завершенной партии."""
        if winner == "draw":
            self.lbl_turn.configure(
                text="Ничья! Победила дружба.",
                fg=COLOR_TEXT_MUTED
            )
            self.status_bar.configure(text="Партия завершена: Ничейный исход")
        else:
            self.lbl_turn.configure(
                text=f"Победа игрока {winner}!",
                fg=COLOR_PLAYER_X if winner == PLAYER_X else COLOR_PLAYER_O
            )
            self.status_bar.configure(text=f"Партия завершена: Победил Игрок {winner}")

            # Подсветка победных 3 клеток
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
        self.status_bar.configure(text=f"Ожидание хода игрока {curr}")

    def _update_score_labels(self) -> None:
        """Обновление карточек счета."""
        scores = self.model.scores
        self.lbl_score_x.configure(text=f"Игрок X\n{scores[PLAYER_X]}")
        self.lbl_score_draws.configure(text=f"Ничьи\n{scores['draws']}")
        self.lbl_score_o.configure(text=f"Игрок O\n{scores[PLAYER_O]}")

    def _update_ui_state(self) -> None:
        """Полная синхронизация интерфейса с текущим состоянием модели."""
        self._update_score_labels()
        self._update_turn_indicator()

    def action_new_game(self) -> None:
        """Запуск новой партии с очисткой игрового поля."""
        self.model.new_game(alternate_starting_player=True)

        # Очистка всех кнопок
        for r in range(3):
            for c in range(3):
                btn = self.buttons[r][c]
                btn.configure(
                    text="",
                    bg=COLOR_BG_CELL,
                    fg=COLOR_TEXT_PRIMARY,
                    activebackground=COLOR_BG_CELL_HOVER
                )

        self._update_ui_state()
        self.status_bar.configure(text="Новая партия началась! Поле очищено.")

    def action_reset_scores(self) -> None:
        """Сброс турнирной таблицы и начало игры с нуля."""
        confirm = messagebox.askyesno(
            "Подтверждение сброса",
            "Вы уверены, что хотите сбросить счет всех партий?",
            parent=self.root
        )
        if confirm:
            self.model.reset_scores()
            self.action_new_game()
            self.status_bar.configure(text="Счет матча успешно сброшен.")

    def apply_preset_geometry(self, width: int, height: int) -> None:
        """Установка разрешения окна по заранее заданному шаблону."""
        if self._is_fullscreen:
            self.toggle_fullscreen()

        self.root.geometry(f"{width}x{height}")
        self._prev_geometry = f"{width}x{height}"
        self.status_bar.configure(text=f"Разрешение окна изменено на {width}x{height}")

    def prompt_custom_resolution(self) -> None:
        """Диалог ввода пользовательского разрешения окна с перехватом исключений."""
        raw_input = simpledialog.askstring(
            "Настройка разрешения",
            f"Введите желаемое разрешение в формате ШхВ (например, 700x800):\n"
            f"Минимум: {MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}, "
            f"Максимум: {MAX_WINDOW_WIDTH}x{MAX_WINDOW_HEIGHT}",
            parent=self.root
        )

        if not raw_input:
            return

        try:
            width, height = self._parse_and_validate_resolution(raw_input)
            self.apply_preset_geometry(width, height)
            messagebox.showinfo(
                "Успех",
                f"Разрешение окна успешно изменено на {width}x{height}.",
                parent=self.root
            )
        except ValueError as err:
            messagebox.showerror(
                "Ошибка ввода разрешения",
                f"Не удалось применить размер окна:\n{err}",
                parent=self.root
            )
        except Exception as exc:
            messagebox.showerror(
                "Системная ошибка",
                f"Произошла непредвиденная ошибка при изменении геометрии окна:\n{exc}",
                parent=self.root
            )

    def _parse_and_validate_resolution(self, input_str: str) -> Tuple[int, int]:
        """Парсинг и валидация строки с разрешением окна.

        Args:
            input_str: Строка, введенная пользователем.

        Returns:
            Tuple[int, int]: Кортеж (ширина, высота).

        Raises:
            ValueError: При несоответствии формату или выходе за допустимый диапазон.
        """
        cleaned = input_str.strip().lower().replace(" ", "").replace("х", "x").replace("*", "x")
        parts = cleaned.split("x")

        if len(parts) != 2:
            raise ValueError(
                f"Неверный формат '{input_str}'.\n"
                "Ожидается запись вида 600x700 (два целых числа через 'x' или '*')."
            )

        try:
            width = int(parts[0])
            height = int(parts[1])
        except ValueError:
            raise ValueError("Ширина и высота должны быть строго целыми положительными числами.")

        if width < MIN_WINDOW_WIDTH or height < MIN_WINDOW_HEIGHT:
            raise ValueError(
                f"Заданный размер {width}x{height} слишком мал.\n"
                f"Минимально допустимый размер: {MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}."
            )

        if width > MAX_WINDOW_WIDTH or height > MAX_WINDOW_HEIGHT:
            raise ValueError(
                f"Заданный размер {width}x{height} превышает максимальный лимит.\n"
                f"Максимально допустимый размер: {MAX_WINDOW_WIDTH}x{MAX_WINDOW_HEIGHT}."
            )

        return width, height

    def toggle_fullscreen(self) -> None:
        """Переключение полноэкранного режима."""
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)
        if self._is_fullscreen:
            self.status_bar.configure(text="Полноэкранный режим включен (F11 / Esc для выхода)")
        else:
            self.status_bar.configure(text=f"Оконный режим восстановлен ({self._prev_geometry})")

    def _exit_fullscreen(self) -> None:
        """Выход из полноэкранного режима по клавише Escape."""
        if self._is_fullscreen:
            self.toggle_fullscreen()

    def show_rules(self) -> None:
        """Отображение модального окна с правилами игры."""
        rules_text = (
            "Правила классической игры «Крестики-нолики»:\n\n"
            "1. Игра проходит на квадратном поле 3х3 клетки для двух участников.\n"
            "2. Игроки ходят по очереди, ставя свой знак (X или O) в свободную клетку.\n"
            "3. Первый ход в начальной партии принадлежит игроку X.\n"
            "4. Цель игры — первым выстроить непрерывный ряд из трех своих знаков "
            "по горизонтали, вертикали или любой из двух диагоналей.\n"
            "5. Если все 9 клеток заполнены, а линия из 3 знаков не собрана, "
            "партии присваивается исход «Ничья».\n"
            "6. В последующих партиях право первого хода поочередно переходит "
            "к сопернику для обеспечения спортивного баланса."
        )
        messagebox.showinfo("Правила игры", rules_text, parent=self.root)

    def show_about(self) -> None:
        """Отображение информации об авторе и архитектуре программы."""
        about_text = (
            "Лабораторная работа по разработке игры «Крестики-нолики»\n"
            "Версия: 1.0.0 (Release)\n\n"
            "Архитектура: Model-View-Controller (ООП)\n"
            "Стек: Python 3 standard library (Tkinter)\n"
            "Стиль: Modern Dark Palette, адаптивная сетка grid (weight=1)\n\n"
            "Особенности реализации:\n"
            "• Независимый класс предметной логики GameModel\n"
            "• Динамическое масштабирование и пресеты геометрии\n"
            "• Комплексная обработка исключений (try-except) без сбоев GUI\n"
            "• Полное соответствие рекомендациям PEP 8"
        )
        messagebox.showinfo("О программе", about_text, parent=self.root)

    def on_exit(self) -> None:
        """Безопасное завершение работы приложения."""
        try:
            self.root.destroy()
        except Exception:
            pass


def main() -> None:
    """Точка входа в графическое приложение."""
    root = tk.Tk()
    app = TicTacToeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
