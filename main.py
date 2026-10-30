"""Главный графический модуль приложения «Крестики-нолики».

Реализует слой представления (View) и слой контроллера (Controller)
в рамках архитектурного паттерна MVC на базе стандартной библиотеки Tkinter.

Особенности графического интерфейса:
    - Адаптивная компоновка сетки с динамическим масштабированием (weight=1).
    - Современная темная цветовая схема оформления (Modern Dark Slate).
    - Развитое главное меню (tkinter.Menu): пресеты окна, произвольный ввод,
      полноэкранный режим и справочный раздел.
    - Отказоустойчивая обработка исключений (try-except) с информированием
      пользователя через модальные диалоги и трассировкой в системный лог.

Стандарты:
    - PEP 8 (Стиль оформления кода).
    - PEP 484 (Аннотации типов).
    - PEP 257 (Конвенции документирования docstrings).
"""

import logging
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog
from typing import Final, List, Optional, Tuple

from model import (
    BOARD_SIZE,
    COLOR_BG_CARD,
    COLOR_BG_CELL,
    COLOR_BG_CELL_HOVER,
    COLOR_BG_MAIN,
    COLOR_PLAYER_O,
    COLOR_PLAYER_X,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WIN_BG,
    COLOR_WIN_FG,
    DRAW_RESULT,
    EMPTY_CELL,
    PLAYER_O,
    PLAYER_X,
    CellOccupiedError,
    GameOverError,
    GameModel,
    InvalidCoordinateError,
)

# -----------------------------------------------------------------------------
# Настройка подсистемы логирования приложения
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger: logging.Logger = logging.getLogger("TicTacToeApp")

# -----------------------------------------------------------------------------
# Константы геометрии и цветовой палитры интерфейса
# -----------------------------------------------------------------------------
DEFAULT_WINDOW_WIDTH: Final[int] = 600
DEFAULT_WINDOW_HEIGHT: Final[int] = 700

MIN_WINDOW_WIDTH: Final[int] = 360
MIN_WINDOW_HEIGHT: Final[int] = 460

MAX_WINDOW_WIDTH: Final[int] = 2560
MAX_WINDOW_HEIGHT: Final[int] = 1600

# Дополнительные цвета палитры
COLOR_BORDER: Final[str] = "#45475a"
COLOR_STATUS_BG: Final[str] = "#11111b"


class TicTacToeApp:
    """Главный класс графического интерфейса и контроллера игры «Крестики-нолики».

    Класс управляет жизненным циклом Tkinter-виджетов, связывает события
    пользовательского ввода (клики мыши, горячие клавиши) с методами
    предметной модели `GameModel` и гарантирует устойчивость приложения
    к непредвиденным ошибкам.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Инициализация главного окна приложения и его визуальных компонентов.

        Args:
            root: Корневой экземпляр Tkinter (tk.Tk).
        """
        self.root: tk.Tk = root
        self.root.title("Крестики-нолики — Лабораторная работа (Senior Edition)")
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.configure(bg=COLOR_BG_MAIN)

        # Состояние геометрии окна
        self._is_fullscreen: bool = False
        self._saved_geometry: str = f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}"

        # Создание экземпляра доменной модели (Model в MVC)
        self.model: GameModel = GameModel()

        # Матрица кнопок интерактивного поля 3x3
        self.buttons: List[List[tk.Button]] = []

        # Инициализация шрифтовой подсистемы
        self._init_fonts()

        # Построение слоев интерфейса
        self._build_menu()
        self._build_header_panel()
        self._build_board_grid()
        self._build_status_bar()

        # Регистрация обработчиков горячих клавиш и закрытия окна
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Синхронизация визуального представления с начальным состоянием модели
        self._update_ui_state()

        logger.info("Графический интерфейс TicTacToeApp успешно построен.")

    # -------------------------------------------------------------------------
    # Инициализация стилей и шрифтов
    # -------------------------------------------------------------------------

    def _init_fonts(self) -> None:
        """Создает семейство шрифтов с поддержкой адаптивного отображения."""
        self.font_score_title = tkfont.Font(
            family="Segoe UI", size=10, weight="normal"
        )
        self.font_score_val = tkfont.Font(
            family="Segoe UI", size=18, weight="bold"
        )
        self.font_turn = tkfont.Font(
            family="Segoe UI", size=13, weight="bold"
        )
        self.font_cell = tkfont.Font(
            family="Segoe UI", size=36, weight="bold"
        )
        self.font_status = tkfont.Font(
            family="Segoe UI", size=10, weight="normal"
        )

    # -------------------------------------------------------------------------
    # Построение структуры интерфейса (Widgets Composition)
    # -------------------------------------------------------------------------

    def _build_menu(self) -> None:
        """Формирует главное верхнее меню приложения (tkinter.Menu).

        Структура меню:
            - «Игра»: Новая партия, Сброс турнирного счета, Выход.
            - «Настройки окна»: Пресеты разрешения, Произвольный ввод, F11.
            - «Справка»: Правила игры, Сведения об авторе и архитектуре.
        """
        menubar = tk.Menu(
            self.root,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_BG_CELL_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY,
            bd=0,
        )

        # Раздел «Игра»
        game_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_BG_CELL_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY,
        )
        game_menu.add_command(
            label="Новая партия (Ctrl+N)",
            command=self.action_new_game,
            accelerator="Ctrl+N",
        )
        game_menu.add_command(
            label="Сброс счета (Ctrl+R)",
            command=self.action_reset_scores,
            accelerator="Ctrl+R",
        )
        game_menu.add_separator()
        game_menu.add_command(
            label="Выход из игры (Ctrl+Q)",
            command=self.on_exit,
            accelerator="Ctrl+Q",
        )
        menubar.add_cascade(label="Игра", menu=game_menu)

        # Раздел «Настройки окна»
        settings_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_BG_CELL_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY,
        )
        settings_menu.add_command(
            label="Разрешение: 400 × 500 (Компактный)",
            command=lambda: self.apply_preset_geometry(400, 500),
        )
        settings_menu.add_command(
            label="Разрешение: 600 × 700 (Стандартный)",
            command=lambda: self.apply_preset_geometry(600, 700),
        )
        settings_menu.add_command(
            label="Разрешение: 800 × 900 (Просторный)",
            command=lambda: self.apply_preset_geometry(800, 900),
        )
        settings_menu.add_separator()
        settings_menu.add_command(
            label="Пользовательский размер...",
            command=self.prompt_custom_resolution,
        )
        settings_menu.add_separator()
        settings_menu.add_command(
            label="Полноэкранный режим (F11)",
            command=self.toggle_fullscreen,
            accelerator="F11",
        )
        menubar.add_cascade(label="Настройки окна", menu=settings_menu)

        # Раздел «Справка»
        help_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_BG_CELL_HOVER,
            activeforeground=COLOR_TEXT_PRIMARY,
        )
        help_menu.add_command(
            label="Правила игры",
            command=self.show_rules,
        )
        help_menu.add_command(
            label="О программе",
            command=self.show_about,
        )
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_header_panel(self) -> None:
        """Создает верхнюю карточку отображения текущего счета и статуса хода."""
        self.header_frame = tk.Frame(
            self.root,
            bg=COLOR_BG_CARD,
            padx=16,
            pady=12,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
        )
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(16, 8))

        # Настройка пропорционального распределения 3 информационных колонок
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
            justify=tk.CENTER,
        )
        self.lbl_score_x.grid(row=0, column=0, sticky="nsew")

        # Карточка счета ничьих
        self.lbl_score_draws = tk.Label(
            self.header_frame,
            text="Ничьи\n0",
            font=self.font_score_val,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_CARD,
            justify=tk.CENTER,
        )
        self.lbl_score_draws.grid(row=0, column=1, sticky="nsew")

        # Карточка счета игрока O
        self.lbl_score_o = tk.Label(
            self.header_frame,
            text="Игрок O\n0",
            font=self.font_score_val,
            fg=COLOR_PLAYER_O,
            bg=COLOR_BG_CARD,
            justify=tk.CENTER,
        )
        self.lbl_score_o.grid(row=0, column=2, sticky="nsew")

        # Индикатор активного хода
        self.lbl_turn = tk.Label(
            self.header_frame,
            text="Ход игрока: X",
            font=self.font_turn,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_CARD,
            pady=6,
        )
        self.lbl_turn.grid(row=1, column=0, columnspan=3, pady=(8, 0))

    def _build_board_grid(self) -> None:
        """Построение адаптивной сетки 3x3 с весами rowconfigure/columnconfigure.

        За счет указания weight=1 для каждой строки и каждого столбца,
        кнопки равномерно масштабируются при любом изменении размеров окна.
        """
        self.board_frame = tk.Frame(
            self.root, bg=COLOR_BG_MAIN, padx=16, pady=8
        )
        self.board_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        for i in range(BOARD_SIZE):
            self.board_frame.rowconfigure(i, weight=1, uniform="board_row")
            self.board_frame.columnconfigure(i, weight=1, uniform="board_col")

        self.buttons = []
        for r in range(BOARD_SIZE):
            row_buttons: List[tk.Button] = []
            for c in range(BOARD_SIZE):
                btn = tk.Button(
                    self.board_frame,
                    text="",
                    font=self.font_cell,
                    bg=COLOR_BG_CELL,
                    activebackground=COLOR_BG_CELL_HOVER,
                    relief=tk.FLAT,
                    bd=0,
                    cursor="hand2",
                    command=lambda row=r, col=c: self._handle_cell_click(row, col),
                )
                btn.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

                # Привязка интерактивного эффекта наведения (Hover Effect)
                btn.bind(
                    "<Enter>",
                    lambda e, b=btn, row=r, col=c: self._on_cell_hover_enter(
                        b, row, col
                    ),
                )
                btn.bind(
                    "<Leave>",
                    lambda e, b=btn, row=r, col=c: self._on_cell_hover_leave(
                        b, row, col
                    ),
                )

                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def _build_status_bar(self) -> None:
        """Создает нижнюю строку состояния с текущим статусом и разрешением."""
        self.status_bar = tk.Label(
            self.root,
            text=f"Готов к игре | Разрешение: {DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}",
            font=self.font_status,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_STATUS_BG,
            anchor="w",
            padx=16,
            pady=8,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _bind_shortcuts(self) -> None:
        """Регистрирует комбинации горячих клавиш клавиатуры."""
        self.root.bind("<Control-n>", lambda event: self.action_new_game())
        self.root.bind("<Control-N>", lambda event: self.action_new_game())
        self.root.bind("<Control-r>", lambda event: self.action_reset_scores())
        self.root.bind("<Control-R>", lambda event: self.action_reset_scores())
        self.root.bind("<Control-q>", lambda event: self.on_exit())
        self.root.bind("<Control-Q>", lambda event: self.on_exit())
        self.root.bind("<F11>", lambda event: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda event: self._exit_fullscreen())

    # -------------------------------------------------------------------------
    # Обработчики событий мыши и интерактивности
    # -------------------------------------------------------------------------

    def _on_cell_hover_enter(
        self, button: tk.Button, row: int, col: int
    ) -> None:
        """Подсвечивает свободную клетку при наведении мыши."""
        if not self.model.is_game_over and self.model.get_cell(row, col) == EMPTY_CELL:
            button.configure(bg=COLOR_BG_CELL_HOVER)

    def _on_cell_hover_leave(
        self, button: tk.Button, row: int, col: int
    ) -> None:
        """Возвращает клетке стандартный фон при уходе курсора."""
        if not self.model.is_game_over and self.model.get_cell(row, col) == EMPTY_CELL:
            button.configure(bg=COLOR_BG_CELL)

    def _handle_cell_click(self, row: int, col: int) -> None:
        """Главный обработчик клика по ячейке игрового поля.

        Отказоустойчивая обработка исключений:
            - `CellOccupiedError`: Клик по занятой ячейке не приводит к сбою,
              а выводит предупреждение в строку статуса.
            - `GameOverError`: Ход после победы корректно блокируется.
            - `InvalidCoordinateError`: Логируется как аномалия координат.
            - `Exception`: Глобальный перехват гарантирует целостность GUI.
        """
        try:
            winner, win_line = self.model.make_move(row, col)
            self._render_move(row, col)

            if winner is not None:
                self._handle_game_finished(winner, win_line)
            else:
                self._update_turn_indicator()

        except CellOccupiedError:
            logger.warning(
                "UI: Пользователь попытался повторно нажать занятую клетку (%d, %d)",
                row,
                col,
            )
            self.status_bar.configure(
                text=f"Предупреждение: Клетка [{row + 1}, {col + 1}] уже занята!"
            )
        except GameOverError:
            logger.info("UI: Клик заблокирован — текущая партия уже завершена.")
            self.status_bar.configure(
                text="Партия уже окончена. Нажмите 'Новая партия' (Ctrl+N)."
            )
        except InvalidCoordinateError as err:
            logger.error("UI: Недопустимые координаты ячейки: %s", err)
        except Exception as exc:
            logger.exception("UI: Непредвиденное исключение в цикле обработки хода:")
            messagebox.showerror(
                "Ошибка игрового процесса",
                f"Произошла непредвиденная системная ошибка:\n{exc}",
                parent=self.root,
            )

    def _render_move(self, row: int, col: int) -> None:
        """Отображает сделанный ход в соответствующей кнопке интерфейса."""
        cell_value = self.model.get_cell(row, col)
        btn = self.buttons[row][col]
        color = COLOR_PLAYER_X if cell_value == PLAYER_X else COLOR_PLAYER_O

        btn.configure(
            text=cell_value,
            fg=color,
            bg=COLOR_BG_CELL,
            activeforeground=color,
        )

    def _handle_game_finished(
        self, winner: str, win_line: Optional[List[Tuple[int, int]]]
    ) -> None:
        """Визуализация исхода завершенной партии (подсветка победы / ничья)."""
        if winner == DRAW_RESULT:
            self.lbl_turn.configure(
                text="Ничья! Ни один игрок не уступил победу.",
                fg=COLOR_TEXT_MUTED,
            )
            self.status_bar.configure(text="Партия завершена: Боевая ничья")
        else:
            self.lbl_turn.configure(
                text=f"Победа игрока {winner}!",
                fg=COLOR_PLAYER_X if winner == PLAYER_X else COLOR_PLAYER_O,
            )
            self.status_bar.configure(
                text=f"Партия завершена: Победил Игрок {winner}"
            )

            # Подсветка выигрышной тройки клеток контрастным цветом
            if win_line:
                for r, c in win_line:
                    self.buttons[r][c].configure(
                        bg=COLOR_WIN_BG,
                        fg=COLOR_WIN_FG,
                        activebackground=COLOR_WIN_BG,
                        activeforeground=COLOR_WIN_FG,
                    )

        self._update_score_labels()

    def _update_turn_indicator(self) -> None:
        """Обновляет индикатор очередности следующего хода."""
        curr = self.model.current_player
        color = COLOR_PLAYER_X if curr == PLAYER_X else COLOR_PLAYER_O
        self.lbl_turn.configure(
            text=f"Ход игрока: {curr}",
            fg=color,
        )
        self.status_bar.configure(text=f"Ожидание хода игрока {curr}")

    def _update_score_labels(self) -> None:
        """Обновляет значения турнирного счета на карточках."""
        scores = self.model.scores
        self.lbl_score_x.configure(text=f"Игрок X\n{scores[PLAYER_X]}")
        self.lbl_score_draws.configure(text=f"Ничьи\n{scores['draws']}")
        self.lbl_score_o.configure(text=f"Игрок O\n{scores[PLAYER_O]}")

    def _update_ui_state(self) -> None:
        """Выполняет полную синхронизацию интерфейса с текущим состоянием модели."""
        self._update_score_labels()
        self._update_turn_indicator()

    # -------------------------------------------------------------------------
    # Действия пользователя через меню (Commands)
    # -------------------------------------------------------------------------

    def action_new_game(self) -> None:
        """Инициализирует новую партию с очисткой игрового поля."""
        logger.info("Запуск новой партии через команду интерфейса.")
        self.model.new_game(alternate_starting_player=True)

        # Очистка состояния всех визуальных кнопок
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                btn = self.buttons[r][c]
                btn.configure(
                    text="",
                    bg=COLOR_BG_CELL,
                    fg=COLOR_TEXT_PRIMARY,
                    activebackground=COLOR_BG_CELL_HOVER,
                )

        self._update_ui_state()
        self.status_bar.configure(text="Новая партия началась! Игровое поле очищено.")

    def action_reset_scores(self) -> None:
        """Сбрасывает турнирный счет сессии после подтверждения пользователем."""
        confirm = messagebox.askyesno(
            "Подтверждение сброса",
            "Вы действительно хотите обнулить счет всех сыгранных партий?",
            parent=self.root,
        )
        if confirm:
            logger.info("Пользователь подтвердил сброс счета.")
            self.model.reset_scores()
            self.action_new_game()
            self.status_bar.configure(text="Турнирный счет успешно обнулен.")

    # -------------------------------------------------------------------------
    # Управление разрешением и геометрией окна (Window Settings)
    # -------------------------------------------------------------------------

    def apply_preset_geometry(self, width: int, height: int) -> None:
        """Применяет заданный шаблон разрешения окна.

        Args:
            width: Желаемая ширина окна в пикселях.
            height: Желаемая высота окна в пикселях.
        """
        if self._is_fullscreen:
            self.toggle_fullscreen()

        self.root.geometry(f"{width}x{height}")
        self._saved_geometry = f"{width}x{height}"
        self.status_bar.configure(
            text=f"Разрешение окна изменено на {width}x{height}"
        )
        logger.info("Применено разрешение окна: %dx%d", width, height)

    def prompt_custom_resolution(self) -> None:
        """Отображает диалоговое окно для ввода произвольного разрешения.

        Реализует строгую валидацию входных данных через блок `try-except`,
        предотвращая сбои геометрии при опечатках или недопустимых значениях.
        """
        raw_input = simpledialog.askstring(
            "Настройка разрешения окна",
            f"Введите желаемое разрешение в формате ШхВ (например, 700x800):\n"
            f"Минимум: {MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}, "
            f"Максимум: {MAX_WINDOW_WIDTH}x{MAX_WINDOW_HEIGHT}",
            parent=self.root,
        )

        if not raw_input:
            logger.info("Пользователь отменил ввод произвольного разрешения.")
            return

        try:
            width, height = self._parse_and_validate_resolution(raw_input)
            self.apply_preset_geometry(width, height)
            messagebox.showinfo(
                "Успех",
                f"Разрешение окна успешно обновлено: {width} × {height} пикселей.",
                parent=self.root,
            )
        except ValueError as val_err:
            logger.warning(
                "Некорректный ввод разрешения: '%s'. Ошибка: %s",
                raw_input,
                val_err,
            )
            messagebox.showerror(
                "Некорректное разрешение",
                f"Ошибка формата или диапазона:\n{val_err}",
                parent=self.root,
            )
        except Exception as exc:
            logger.exception("Ошибка при установке пользовательского разрешения:")
            messagebox.showerror(
                "Системная ошибка",
                f"Не удалось применить геометрию окна:\n{exc}",
                parent=self.root,
            )

    def _parse_and_validate_resolution(self, input_str: str) -> Tuple[int, int]:
        """Парсит и валидирует строку формата 'ШхВ'.

        Поддерживает разделители 'x', 'х' (русская), '*', пробелы.

        Args:
            input_str: Введенная пользователем строка.

        Returns:
            Tuple[int, int]: Кортеж валидированных целых чисел (ширина, высота).

        Raises:
            ValueError: При нарушении формата, отрицательных или запредельных значениях.
        """
        cleaned = (
            input_str.strip()
            .lower()
            .replace(" ", "")
            .replace("х", "x")
            .replace("*", "x")
        )
        parts = cleaned.split("x")

        if len(parts) != 2:
            raise ValueError(
                f"Строка '{input_str}' не соответствует формату.\n"
                "Пример правильного ввода: 650x750 или 700*800."
            )

        try:
            width = int(parts[0])
            height = int(parts[1])
        except ValueError:
            raise ValueError("Ширина и высота должны быть целыми положительными числами.")

        if width < MIN_WINDOW_WIDTH or height < MIN_WINDOW_HEIGHT:
            raise ValueError(
                f"Разрешение {width}x{height} меньше допустимого минимума.\n"
                f"Минимальные размеры: {MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT}."
            )

        if width > MAX_WINDOW_WIDTH or height > MAX_WINDOW_HEIGHT:
            raise ValueError(
                f"Разрешение {width}x{height} превышает максимальный лимит.\n"
                f"Максимальные размеры: {MAX_WINDOW_WIDTH}x{MAX_WINDOW_HEIGHT}."
            )

        return width, height

    def toggle_fullscreen(self) -> None:
        """Переключает состояние между полноэкранным и оконным режимами."""
        self._is_fullscreen = not self._is_fullscreen
        self.root.attributes("-fullscreen", self._is_fullscreen)

        if self._is_fullscreen:
            self.status_bar.configure(
                text="Полноэкранный режим активен (Нажмите F11 или Esc для выхода)"
            )
            logger.info("Включен полноэкранный режим.")
        else:
            self.status_bar.configure(
                text=f"Оконный режим восстановлен ({self._saved_geometry})"
            )
            logger.info("Восстановлен оконный режим (%s).", self._saved_geometry)

    def _exit_fullscreen(self) -> None:
        """Служебный метод выхода из полноэкранного режима по нажатию Escape."""
        if self._is_fullscreen:
            self.toggle_fullscreen()

    # -------------------------------------------------------------------------
    # Диалоговые окна справочного раздела (Help)
    # -------------------------------------------------------------------------

    def show_rules(self) -> None:
        """Отображает структурированные правила игры «Крестики-нолики»."""
        rules_text = (
            "Правила классической игры «Крестики-нолики»:\n\n"
            "1. Поле представляет собой сетку 3х3 клетки для двух участников.\n"
            "2. Участники ходят строго по очереди, размещая свой символ (X или O).\n"
            "3. Первый ход в стартовой партии сессии делает Игрок X.\n"
            "4. Цель — первым составить непрерывную линию из 3 одинаковых символов:\n"
            "   • По горизонтали (в любой из 3 строк);\n"
            "   • По вертикали (в любом из 3 столбцов);\n"
            "   • По главной или побочной диагонали.\n"
            "5. Если все 9 клеток заполнены, а линия из 3 знаков отсутствует, "
            "партии присваивается исход «Ничья».\n"
            "6. В последующих раундах право первого хода поочередно переходит "
            "к сопернику для обеспечения спортивного баланса."
        )
        messagebox.showinfo("Правила игры", rules_text, parent=self.root)

    def show_about(self) -> None:
        """Отображает сведения о проекте, авторе и архитектурных решениях."""
        about_text = (
            "Лабораторная работа по дисциплине программирования\n"
            "Тема: Разработка игры «Крестики-нолики» на Tkinter\n"
            "Версия: 1.0.0 (Release)\n\n"
            "Архитектурный шаблон: Model-View-Controller (MVC)\n"
            "Графическая подсистема: Tkinter (Grid Layout с весами weight=1)\n"
            "Стиль: Modern Dark Slate Palette\n\n"
            "Ключевые инженерные решения:\n"
            "• Чистая модель предметной области без привязки к GUI\n"
            "• Полное покрытие тестами базовых игровых сценариев\n"
            "• Валидация геометрии и защита от сбоев в обработчиках событий\n"
            "• Строгое соблюдение спецификаций PEP 8 и PEP 484"
        )
        messagebox.showinfo("О программе", about_text, parent=self.root)

    def on_exit(self) -> None:
        """Корректное завершение работы приложения с освобождением дескрипторов."""
        logger.info("Завершение работы приложения...")
        try:
            self.root.destroy()
        except Exception as exc:
            logger.warning("Ошибка при уничтожении корневого окна: %s", exc)


def main() -> None:
    """Точка входа в программу: инициализация и запуск главного цикла событий."""
    logger.info("Запуск приложения «Крестики-нолики»...")
    root = tk.Tk()
    app = TicTacToeApp(root)
    root.mainloop()
    logger.info("Главный цикл Tkinter mainloop() завершен.")


if __name__ == "__main__":
    main()
