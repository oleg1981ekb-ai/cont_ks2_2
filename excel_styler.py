import openpyxl
import config

# Настраиваем деликатный серый курсив для 5-го уровня истории дат
FONT_LOG_DATE = openpyxl.styles.Font(name="Calibri", size=9, italic=True, color="7A7A7A")

def apply_row_style(ws, row_idx, font, fill, border, alignment=None):
    """Применяет стили оформления к указанной строке таблицы."""
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=row_idx, column=col)
        if font: cell.font = font
        if fill: cell.fill = fill
        if border: cell.border = border
        if alignment: cell.alignment = alignment

def format_status_cell(cell, status_raw):
    """Записывает статус, красит ячейку и делает цифры жирными чёрными."""
    import config
    from openpyxl.styles import Font

    if isinstance(status_raw, dict):
        status_val = status_raw.get("value", "")
    else:
        status_val = status_raw

    if status_val == "" or status_val is None:
        return

    status_str = str(status_val).strip()
    
    try:
        cell.value = int(status_str)
    except ValueError:
        cell.value = status_str

    cell.alignment = config.ALIGN_C
    
    # ИСПРАВЛЕНО: Принудительный жирный черный шрифт для идеального контраста
    cell.font = Font(name="Calibri", size=11, bold=True, color="000000")
    
    if status_str == "1":
        cell.fill = config.FILL_GREEN
    elif status_str == "2":
        cell.fill = config.FILL_YELLOW
    elif status_str == "3":
        cell.fill = config.FILL_RED

