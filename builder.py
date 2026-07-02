import openpyxl
import json
import os
import datetime
import config
import excel_styler

def apply_row_style(ws, row_idx, font, fill, border, alignment=None):
    excel_styler.apply_row_style(ws, row_idx, font, fill, border, alignment)

def build_structure(ws, mock_data=None, saved_statuses=None, saved_sums=None):
    ws.freeze_panes = "A2"
    ws.sheet_properties.outlinePr.summaryBelow = False
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    ws.oddHeader.right.text = f"Выгружено: {now_str}"
    ws.oddHeader.right.size = 9
    ws.oddHeader.right.color = "7A7A7A"
    if ws.max_row == 1 and ws.cell(row=1, column=1).value is None:
        ws.append(config.HEADERS)
        excel_styler.apply_row_style(ws, 1, config.FONT_HDR, config.FILL_HDR, config.THIN_BORDER, config.ALIGN_C)
    
    json_path = "database.json"
    if not os.path.exists(json_path): return ws.max_row
    with open(json_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    row_counter = 1
    for direction in db.keys():
        ws.append(["", str(direction), "", "", "", "", "", "", "", ""])
        excel_styler.apply_row_style(ws, ws.max_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, config.ALIGN_L)
        ws.row_dimensions[ws.max_row].outline_level = 0
        
        for sub_obj in db[direction].keys():
            ws.append(["", str(sub_obj), "", "", "", "", "", "", "", ""])
            excel_styler.apply_row_style(ws, ws.max_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, config.ALIGN_L)
            ws.row_dimensions[ws.max_row].outline_level = 1
            
            for mth in config.MONTHS_LIST:
                if mth not in db[direction][sub_obj]: continue
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
                
                # Документы: Уровень 3
                for d_name in config.DOCUMENTS_LIST:
                    ws.append(["", f"• {d_name}", "", "", "", "", "", "", "", ""])
                    doc_row = ws.max_row
                    excel_styler.apply_row_style(ws, doc_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    ws.cell(row=doc_row, column=3).number_format = '#,##0.00'
                    ws.row_dimensions[doc_row].outline_level = 3
                    
                    mask = config.DOCUMENT_ROLES.get(d_name, {"СтрК": 1, "СДО": 1, "ГенДир": 1, "1 экз. З.": 1, "1 экз. П": 1, "Опл.": 1})
                    column_mapping = {"СтрК": 4, "СДО": 5, "ГенДир": 6, "1 экз. З.": 7, "1 экз. П": 8, "Опл.": 9}
                    
                    # Извлечение персонального или общего статуса
                    if isinstance(status_raw, dict) and d_name in status_raw:
                        doc_status_raw = status_raw[d_name]
                    else:
                        doc_status_raw = status_raw

                    status_date = doc_status_raw.get("date", "") if isinstance(doc_status_raw, dict) else ""
                    
                    for col_name, col_idx in column_mapping.items():
                        cell = ws.cell(row=doc_row, column=col_idx)
                        if mask.get(col_name, 1) == 0:
                            cell.fill = config.FILL_BLOCKED
                            cell.value = ""
                        else:
                            if col_name == "СтрК":
                                excel_styler.format_status_cell(cell, doc_status_raw)
                    
                    # НОВЫЙ 5-Й УРОВЕНЬ: Логгер даты
                    if mask.get("СтрК", 1) == 1 and status_date:
                        ws.append(["", f"    └─ Дата изменения СтрК: {status_date}", "", "", "", "", "", "", "", ""])
                        log_row = ws.max_row
                        excel_styler.apply_row_style(ws, log_row, excel_styler.FONT_LOG_DATE, None, config.THIN_BORDER, config.ALIGN_L)
                        ws.row_dimensions[log_row].outline_level = 4
                        
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=2).value in config.MONTHS_LIST:
            ws.cell(row=row, column=10).value = f"=IF(C{row}>0, \"В работе\", \"\")"
            
    return ws.max_row
