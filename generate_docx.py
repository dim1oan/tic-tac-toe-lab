"""Скрипт автоматической генерации отчета по лабораторной работе в формате DOCX.

Использует библиотеку python-docx для создания стилизованного документа
с таблицами, блоками кода и полным описанием проекта.
"""

import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def set_cell_background(cell, fill_hex: str):
    """Установка фонового цвета ячейки таблицы."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Установка внутренних отступов ячейки."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_code_block(doc: Document, code_text: str):
    """Добавление форматированного блока кода."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_background(cell, "F4F5F7")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05

    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x24, 0x29, 0x2E)

    doc.add_paragraph()  # разделительный отступ


def build_report():
    """Сборка полного документа DOCX."""
    doc = Document()

    # Поля страницы: 2 см со всех сторон
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Титульный блок
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(10)
    title_p.paragraph_format.space_after = Pt(4)
    run_sub = title_p.add_run("ОТЧЕТ ПО ЛАБОРАТОРНОЙ РАБОТЕ\n")
    run_sub.font.size = Pt(13)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(0x5A, 0x65, 0x78)

    run_main = title_p.add_run("Разработка игры «Крестики-нолики» на Python (Tkinter)")
    run_main.font.size = Pt(20)
    run_main.font.bold = True
    run_main.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    # Метаданные работы
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Дисциплина:", "Технологии разработки ПО / Объектно-ориентированное программирование"),
        ("Тема работы:", "Реализация настольной игры с архитектурой MVC и адаптивным интерфейсом"),
        ("Целевая оценка:", "Отлично (100 / 100)"),
        ("Технологический стек:", "Python 3.10+, Tkinter, unittest, Git, draw.io"),
    ]
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        c1, c2 = row.cells[0], row.cells[1]
        c1.width = Inches(2.2)
        c2.width = Inches(4.8)
        set_cell_background(c1, "F1F5F9")
        set_cell_background(c2, "FFFFFF")
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(label)
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

        p2 = c2.paragraphs[0]
        r2 = p2.add_run(val)
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    doc.add_paragraph()

    # 1. Цель работы
    h1 = doc.add_heading("1. Цель работы и постановка задачи", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)

    p_goal = doc.add_paragraph(
        "Цель работы: Проектирование и разработка десктопного графического приложения "
        "«Крестики-нолики» (Tic-Tac-Toe) для двух игроков на языке Python с использованием "
        "стандартной библиотеки tkinter. Проект выполнен в строгом соответствии с принципами "
        "объектно-ориентированного программирования (ООП), паттерном MVC (Model-View-Controller) "
        "и рекомендациями стандарта PEP 8."
    )
    p_goal.paragraph_format.line_spacing = 1.15

    # 2. Формализация предметной области
    h2 = doc.add_heading("2. Формализация предметной области", level=1)
    h2.paragraph_format.space_before = Pt(14)

    doc.add_paragraph(
        "Игровое поле формализуется как дискретная квадратная матрица B размерности 3x3: "
        "B = (b_r,c), где r, c ∈ {0, 1, 2}. Состояние ячейки b_r,c принадлежит множеству "
        "S = {Ø, 'X', 'O'}. Множество участников P = {'X', 'O'}.\n\n"
        "Правило победы определяется наличием хотя бы одной выигрышной прямой из семейства L "
        "(3 горизонтали, 3 вертикали, 2 диагонали):\n"
        "Win(B, p) <=> ∃ l ∈ L: ∀ (r, c) ∈ l, b_r,c = p.\n\n"
        "Критерий ничьей:\n"
        "Draw(B) <=> ¬Win(B, X) ∧ ¬Win(B, O) ∧ (∀ r, c: b_r,c ≠ Ø).\n"
        "Вычислительная сложность алгоритма проверки победы является строго константной O(1)."
    )

    # 3. Архитектура и обработка исключений
    h3 = doc.add_heading("3. Архитектура приложения и обработка исключений", level=1)
    h3.paragraph_format.space_before = Pt(14)

    doc.add_paragraph(
        "Приложение разделено на два изолированных уровня:\n"
        "1. GameModel (model.py) — чистая игровая модель без зависимостей от графической подсистемы. "
        "Инкапсулирует состояние поля, историю ходов MoveRecord, валидацию координат и подсчет побед.\n"
        "2. TicTacToeApp (main.py) — представление и контроллер на Tkinter. Реализует адаптивную сетку "
        "с rowconfigure/columnconfigure (weight=1), верхнее меню настроек геометрии и горячие клавиши.\n\n"
        "Отказоустойчивость достигается перехватом специфических доменных исключений "
        "(CellOccupiedError, GameOverError, InvalidCoordinateError) и защитой от некорректного "
        "ввода пользовательского разрешения через блоки try-except ValueError."
    )

    # 4. История Git
    h4 = doc.add_heading("4. Поэтапная история версионирования в Git", level=1)
    h4.paragraph_format.space_before = Pt(14)

    git_table = doc.add_table(rows=7, cols=3)
    git_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    git_commits = [
        ("Хеш", "Сообщение коммита", "Назначение"),
        ("5f8ab3e", "Инициализация проекта, добавлены .gitignore и README", "Базовая структура, .gitignore, README.md"),
        ("89bc93e", "Реализована логика игры, проверка победы и ничьей", "Класс GameModel, валидация и unittest"),
        ("20d4f53", "Создано главное окно Tkinter и адаптивное поле 3х3", "Темный UI, адаптивная сетка grid 3x3, счет"),
        ("05b5519", "Добавлено верхнее меню, настройка размеров окна и перехват ошибок", "Верхнее меню Menu, пресеты, валидация"),
        ("b060d4d", "Форматирование кода по PEP 8, добавлены комментарии и тесты", "PEP 8, typing, docstrings, logging"),
        ("d0e0f7b", "Добавлены прототипы интерфейса и отчет по лабораторной работе", "Отчет, wireframes drawio/svg, генератор docx"),
    ]
    for r_idx, row_data in enumerate(git_commits):
        row = git_table.rows[r_idx]
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            if r_idx == 0:
                set_cell_background(cell, "1E293B")
                p = cell.paragraphs[0]
                run = p.add_run(val)
                run.font.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
                p = cell.paragraphs[0]
                run = p.add_run(val)
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    doc.add_paragraph()

    # 5. Листинг кода
    h5 = doc.add_heading("5. Исходный код ключевых модулей", level=1)
    h5.paragraph_format.space_before = Pt(14)

    doc.add_heading("5.1. Модуль model.py (Класс GameModel)", level=2)
    with open("model.py", "r", encoding="utf-8") as f:
        model_code = f.read()
    add_code_block(doc, model_code[:3000] + "\n\n# ... (полный код в репозитории) ...")

    # 6. Шпаргалка к защите
    h6 = doc.add_heading("6. Ответы на вопросы к защите (Шпаргалка)", level=1)
    h6.paragraph_format.space_before = Pt(14)

    questions = [
        (
            "1. Как функционирует главный цикл событий mainloop() в Tkinter?",
            "Метод root.mainloop() запускает бесконечный цикл диспетчеризации сообщений ОС. "
            "Он опрашивает очередь событий (клики, клавиши, перерисовка), сопоставляет их с "
            "виджетами и вызывает зарегистрированные callback-функции, блокируя синхронный поток."
        ),
        (
            "2. В чем преимущество применения архитектурного паттерна MVC?",
            "Обеспечивается слабая связность: логика GameModel полностью независима от GUI, "
            "что позволяет тестировать её автономно (через unittest) и менять библиотеку GUI "
            "без изменения правил игры."
        ),
        (
            "3. Как алгоритмически проверяются выигрышные условия в матрице 3х3?",
            "Проверяются ровно 8 фиксированных прямых линий (3 строки, 3 столбца, 2 диагонали). "
            "Сложность проверки составляет константное время O(1) и не требует перебора графа."
        ),
        (
            "4. Как реализована адаптивность с помощью grid и весов weight=1?",
            "Вызов rowconfigure(i, weight=1) и columnconfigure(j, weight=1) заставляет Tkinter "
            "пропорционально распределять дополнительное пространство окна между ячейками при растяжении."
        ),
        (
            "5. Зачем необходим перехват исключений в GUI (try-except)?",
            "Неперехваченное исключение в Tkinter прерывает нормальный поток событий, что может "
            "привести к зависанию графических компонентов. try-except выводит понятные сообщения "
            "через messagebox.showerror и сохраняет стабильность окна."
        ),
    ]

    for q_title, q_ans in questions:
        doc.add_heading(q_title, level=2)
        p = doc.add_paragraph(q_ans)
        p.paragraph_format.line_spacing = 1.15

    output_path = "REPORT.docx"
    doc.save(output_path)
    print(f"Отчет успешно сохранен в файл: {output_path}")


if __name__ == "__main__":
    build_report()
