import os
import openpyxl
import config
import storage
import builder
import formatter

def run():
    print("Инициализация сборщика смарт-трекера...")
    saved_statuses, saved_sums = storage.load_historical_data(config.FULL_PATH)
    mock_data = storage.group_linear_data(config.DATA_ROWS)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Реестр Актов"
    ws.sheet_view.showGridLines = ws.sheet_view.showOutlineSymbols = True
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.append(config.HEADERS)
    ws.row_dimensions.height = 28
    builder.apply_row_style(ws, 1, config.FONT_HDR, config.FILL_HDR, config.THIN_BORDER, config.ALIGN_C)
    last_row = builder.build_structure(ws, mock_data, saved_statuses, saved_sums)
    formatter.append_specifications(ws, last_row)
    formatter.apply_conditional_formatting(ws)
    formatter.set_column_widths(ws)
    try:
        wb.save(config.FULL_PATH)
        print("🚀 Модульный смарт-трекер успешно создан на Рабочем столе!")
    except PermissionError:
        print("❌ Ошибка: Закройте файл Excel перед запуском скрипта!")

if __name__ == "__main__":
    run()
