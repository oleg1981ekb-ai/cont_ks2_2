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
    """Записывает в ячейку чистое число статуса для корректной работы условного цвета."""
    status_val = ""
    
    if isinstance(status_raw, dict):
        status_val = status_raw.get("value", "")
    else:
        status_val = status_raw

    if status_val == "" or status_val is None:
        return ""

    try:
        # ВОЗВРАЩАЕМ ИСПРАВЛЕНИЕ: Преобразуем статус в число int, чтобы сработал цвет Excel
        cell.value = int(status_val)
    except ValueError:
        cell.value = str(status_val)

    cell.font = config.FONT_DATA
    cell.alignment = config.ALIGN_C
    return cell.value
