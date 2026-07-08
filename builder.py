import openpyxl
import json
import os
import datetime
import config
import db_core
import db_viewer
import excel_styler

def apply_row_style(ws, row_idx, font, fill, border, alignment=None):
    excel_styler.apply_row_style(ws, row_idx, font, fill, border, alignment)

def build_structure(ws, mock_data=None, saved_statuses=None, saved_sums=None):
    ws.freeze_panes = "A3"
    ws.sheet_properties.outlinePr.summaryBelow = False
    
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    ws.oddHeader.right.text = f"Выгружено: {now_str}"
    ws.oddHeader.right.size = 9
    ws.oddHeader.right.color = "7A7A7A"
    
    if ws.max_row == 1 and ws.cell(row=1, column=1).value is None:
        ws.append(config.HEADERS)
        for col_idx in range(1, len(config.HEADERS) + 1):
            cell = ws.cell(row=2, column=col_idx)
            cell.fill = config.FILL_HDR
            cell.font = config.FONT_HDR
            cell.border = config.THIN_BORDER



    
    json_path = "database.json"
    if not os.path.exists(json_path): return ws.max_row
    with open(json_path, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    # ЭТАП 1: Чтение метаданных на старте
    meta = db.get("_meta", {}) if isinstance(db, dict) else {}
    target_dir = meta.get("last_changed_dir")
    target_sub = meta.get("last_changed_sub")
    is_new = meta.get("is_new_change", False)

    row_counter = 1
    for direction in db.keys():
        if direction == "_meta":
            continue
        ws.append(["", str(direction), "", "", "", "", "", "", "", ""])
        excel_styler.apply_row_style(ws, ws.max_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, config.ALIGN_L)
        ws.row_dimensions[ws.max_row].outline_level = 0
        
        for sub_obj in db[direction].keys():
            ws.append(["", str(sub_obj), "", "", "", "", "", "", "", ""])
            excel_styler.apply_row_style(ws, ws.max_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, config.ALIGN_L)
            ws.row_dimensions[ws.max_row].outline_level = 1
            
            raw_months = list(db[direction][sub_obj].keys())
            available_months = [m for m in db_core.ALL_YEAR_MONTHS if m in raw_months]
            
            for m in raw_months:
                if m not in available_months:
                    available_months.append(m)
            
            for mth in available_months:
                mth_data = db[direction][sub_obj][mth]
                status_raw = mth_data.get("status", "")
                
                # Месяц: Уровень 2
                ws.append([row_counter, mth, float(mth_data.get("sum", 0.0)), "", "", "", "", "", "", ""])
                current_row = ws.max_row
                excel_styler.apply_row_style(ws, current_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, config.ALIGN_L)
                ws.cell(row=current_row, column=1).alignment = config.ALIGN_C
                ws.cell(row=current_row, column=3).number_format = '#,##0.00'
                ws.row_dimensions[current_row].outline_level = 2
                row_counter += 1

                # Раскрытие последнего изменения (ЭТАП 2)
                hidden_default = True
                if is_new and direction == target_dir and sub_obj == target_sub:
                    hidden_default = False
                ws.row_dimensions[current_row].hidden = hidden_default

                # Документы: Уровень 3
                for d_name in config.DOCUMENTS_LIST:
                    ws.append(["", f"• {d_name}", "", "", "", "", "", "", "", ""])
                    doc_row = ws.max_row
                    excel_styler.apply_row_style(ws, doc_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    ws.cell(row=doc_row, column=3).number_format = '#,##0.00'
                    ws.row_dimensions[doc_row].outline_level = 3
                    
                    mask = config.DOCUMENT_ROLES.get(d_name, {"СтрК": 1, "СДО": 1, "ГенДир": 1, "1 экз. З.": 1, "1 экз. П": 1, "Опл.": 1})
                    column_mapping = {"СтрК": 4, "СДО": 5, "ГенДир": 6, "1 экз. З.": 7, "1 экз. П": 8, "Опл.": 9}
                    
                    # статус конкретного документа: СтрК/СДО
                    if isinstance(status_raw, dict) and d_name in status_raw:
                        doc_status_raw = status_raw[d_name]
                    else:
                        doc_status_raw = status_raw

                    status_date = doc_status_raw.get("date", "") if isinstance(doc_status_raw, dict) else ""

                    print(f"DEBUG | Область: {direction} -> {sub_obj} | Документ: {d_name} | Содержимое строки базы: {doc_status_raw}")

                    for col_name, col_letter_or_idx in config.COLUMN_MAPPING.items():
                        if isinstance(col_letter_or_idx, str):
                            col_letter = col_letter_or_idx
                            col_idx = openpyxl.utils.column_index_from_string(col_letter)
                        else:
                            col_idx = int(col_letter_or_idx)

                        cell = ws.cell(row=doc_row, column=col_idx)

                        # Считываем статус конкретно для СтрК или СДО
                        if isinstance(doc_status_raw, dict):
                            # Если в базе лежит новый разделенный формат для СтрК и СДО
                            clean_status_value = doc_status_raw.get(col_name, {}).get('value') if col_name in doc_status_raw else doc_status_raw.get('value')
                        else:
                            # Если в базе лежит старый плоский формат (только для СтрК)
                            clean_status_value = doc_status_raw if col_name == "СтрК" else None

                        if mask.get(col_name) == 0:
                            cell.fill = config.FILL_BLOCKED
                            cell.value = ""
                        else:
                            if clean_status_value is not None:
                                excel_styler.format_status_cell(cell, clean_status_value)
                            else:
                                cell.fill = openpyxl.styles.PatternFill(fill_type=None)

                    # Логгер даты: Уровень 4



                    if mask.get("СтрК", 1) == 1 and status_date:

                        ws.append(["", f"    └─ Дата изменения СтрК: {status_date}", "", "", "", "", "", "", "", ""])
                        log_row = ws.max_row
                        excel_styler.apply_row_style(ws, log_row, excel_styler.FONT_LOG_DATE, None, config.THIN_BORDER, config.ALIGN_L)
                        ws.row_dimensions[log_row].outline_level = 4
                        
    # Проставляем формулы статуса акта
    for row in range(2, ws.max_row + 1):
        cell_val = ws.cell(row=row, column=2).value
        if cell_val and not str(cell_val).startswith("•") and not str(cell_val).startswith(" "):
            ws.cell(row=row, column=10).value = f"=IF(C{row}>0, \"В работе\", \"\")"
            
    # УМНОЕ АВТОМАТИЧЕСКОЕ СВЕРТЫВАНИЕ СТРОК ДО УРОВНЯ МЕСЯЦЕВ
    ws.sheet_view.showOutlineSymbols = True
    for row_idx in range(2, ws.max_row + 1):
        if ws.row_dimensions[row_idx].outline_level in (3, 4):
            ws.row_dimensions[row_idx].hidden = True

    # Если флаг последнего изменения новый — раскрываем нужный Подобъект (ЭТАП 2)
    if is_new and target_dir is not None and target_sub is not None:
        for row_idx in range(2, ws.max_row + 1):
            # Месяц: Уровень 2
            if ws.row_dimensions[row_idx].outline_level == 2:
                # В колонке B лежит название "direction/sub" или месяца; тут месяц в колонке B (индекс 2)
                mth_name = ws.cell(row=row_idx, column=2).value
                if mth_name is not None:
                    # Для принадлежности к целевому направлению/подобъекту полагаемся на то, что нужный блок построен последовательно:
                    # верхние строки direction и sub_obj ранее имеют другие outline_level.
                    pass

        # Практичный вариант: раскрываем ВСЕ строки после заголовков target_dir/target_sub,
        # поскольку структура построения: direction(level0) -> sub_obj(level1) -> месяцы(level2) -> документы(level3).
        # Найдём parent_row_idx (строка sub_obj) и затем раскрываем все строки внутри блока.
        parent_row_idx = None
        current_direction = None
        current_sub = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.row_dimensions[row_idx].outline_level == 0:
                current_direction = ws.cell(row=row_idx, column=2).value
            elif ws.row_dimensions[row_idx].outline_level == 1:
                current_sub = ws.cell(row=row_idx, column=2).value

            if current_direction == target_dir and current_sub == target_sub and ws.row_dimensions[row_idx].outline_level == 1:
                parent_row_idx = row_idx
                break

        if parent_row_idx is not None:
            # Раскрываем родительскую строку
            ws.row_dimensions[parent_row_idx].hidden = False

            # Раскрываем строки внутри блока до следующей строки outline_level==1 (другой sub_obj)
            for row_idx in range(parent_row_idx + 1, ws.max_row + 1):
                if ws.row_dimensions[row_idx].outline_level == 1:
                    break
                if ws.row_dimensions[row_idx].outline_level in (2, 3, 4):
                    ws.row_dimensions[row_idx].hidden = False

                    # На родительской (sub_obj) — show_detail()
            # openpyxl: show_detail доступно только на уровнях Outline, поэтому дополнительно:
            try:
                ws.row_dimensions[parent_row_idx].show_detail()
            except Exception:
                pass

            
    # ИСПРАВЛЕНО: Безопасный автоподбор ширины через чтение первой ячейки кортежа col[0]
    for col in ws.columns:
        max_len = 0
        col_idx = col[0].column
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        for cell in col:
            if cell.value:
                    if isinstance(cell.value, (int, float)) and cell.column == 3:
                        max_len = max(max_len, 18)
                    else:
                        max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(min(max_len + 3, 45), 12)
            
            
    # ЭТАП 3: Сброс флага в финале (чтобы следующий запуск открывался свернутым)
    if isinstance(db, dict) and "_meta" in db:
        db["_meta"]["is_new_change"] = False
        db_core.save_db(db)

    return ws.max_row
