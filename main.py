import os
import openpyxl
import config
import storage
import builder
import formatter

def run():
    print("⚙️ [Автоматический запуск] Сборка смарт-трекера...")
    file_path = config.FULL_PATH if config.FULL_PATH else "Трекер_Акт_Выполнения.xlsx"
    
    # 1. Загрузка истории
    saved_statuses, saved_sums = storage.load_historical_data(file_path)
    mock_data = storage.group_linear_data(config.DATA_ROWS)
    
    # 2. Инициализация книги
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Реестр Актов"
    ws.sheet_view.showGridLines = True
    ws.sheet_view.showOutlineSymbols = True
    ws.sheet_properties.outlinePr.summaryBelow = False
    
    # 3. Шапка
    ws.append(config.HEADERS)
    ws.row_dimensions.height = 28
    builder.apply_row_style(ws, 1, config.FONT_HDR, config.FILL_HDR, config.THIN_BORDER, config.ALIGN_C)
    
    # 4. Построение и стилизация
    last_row = builder.build_structure(ws, mock_data, saved_statuses, saved_sums)
    formatter.append_specifications(ws, last_row)
    formatter.apply_conditional_formatting(ws)
    formatter.set_column_widths(ws)
    
    # 5. Безопасное сохранение
    try:
        wb.save(file_path)
        
        # ФИЗИЧЕСКАЯ ПРОВЕРКА НАЛИЧИЯ ФАЙЛА НА ДИСКЕ
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
            print(f"📡 [ДАТЧИК КОНТРОЛЯ] Файл успешно обнаружен в системе!")
            print(f"📍 Путь: {os.path.abspath(file_path)}")
            print(f"⚖️ Вес документа: {file_size_kb} КБ")
            print(f"🚀 [УСПЕХ] Таблица полностью обновлена автоматически!")
        else:
            print("🚨 [ВНИМАНИЕ] Файл записан, но датчик системы указывает на пустой или отсутствующий документ!")
            
    except PermissionError:
        print("❌ [ОШИБКА ДОСТУПА] Файл Excel/LibreOffice открыт! Закройте его для генерации.")
    except Exception as e:
        print(f"❌ [КРИТИЧЕСКИЙ СБОЙ] Запись сорвалась: {e}")

if __name__ == "__main__":
    run()
