import openpyxl
import config

def apply_row_style(ws, row_idx, font, fill, border, alignment=None):
    """Применяет стили оформления к указанной строке таблицы."""
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=row_idx, column=col)
        if font: cell.font = font
        if fill: cell.fill = fill
        if border: cell.border = border
        if alignment: cell.alignment = alignment

def build_structure(ws, mock_data, saved_statuses, saved_sums):
    """
    Генерирует структуру табличной части.
    Исправлено извлечение сумм [450000, 3] -> 450000.
    """
    # Очищаем дефолтный лист перед заполнением, если он пустой
    if ws.max_row == 1 and ws.cell(row=1, column=1).value is None:
        ws.append(config.HEADERS)
        apply_row_style(ws, 1, config.FONT_HDR, config.FILL_HDR, config.THIN_BORDER, config.ALIGN_C)
    
    for direction in mock_data.keys():
        # Смещаем Направление во вторую ячейку (столбец B)
        ws.append(["", str(direction), "", "", "", "", "", "", "", ""])
        apply_row_style(ws, ws.max_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, config.ALIGN_L)
        
        for sub_obj in mock_data[direction].keys():
            ws.append(["", str(sub_obj), "", "", "", "", "", "", "", ""])
            apply_row_style(ws, ws.max_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, config.ALIGN_L)
            
            for r_key in config.MONTHS_LIST:
                if r_key not in mock_data[direction][sub_obj]: continue
                raw_data = mock_data[direction][sub_obj][r_key]
                
                # ИСПРАВЛЕНО: Строго извлекаем только число суммы из массива/кортежа
                if isinstance(raw_data, (list, tuple)) and len(raw_data) > 0:
                    clean_sum = raw_data[0]
                else:
                    clean_sum = raw_data
                
                val = saved_sums.get((direction, sub_obj, r_key))
                if val is None:
                    val = clean_sum
                
                # Добавляем строку месяца с чистым числом суммы
                ws.append(["", r_key, val, "", "", "", "", "", "", ""])
                apply_row_style(ws, ws.max_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, config.ALIGN_L)
                
                # Добавляем строки документов
                for d_name in config.DOCUMENTS_LIST:
                    hist_key = (direction, sub_obj, r_key, d_name)
                    st = saved_statuses.get(hist_key, ("", "", "", "", "", ""))
                    
                    s0 = st[0] if len(st) > 0 else ""
                    s1 = st[1] if len(st) > 1 else ""
                    s2 = st[2] if len(st) > 2 else ""
                    s3 = st[3] if len(st) > 3 else ""
                    s4 = st[4] if len(st) > 4 else ""
                    s5 = st[5] if len(st) > 5 else ""
                    
                    doc_row = ["", f"• {d_name}", clean_sum, s0, s1, s2, s3, s4, s5, ""]
                    ws.append(doc_row)
                    apply_row_style(ws, ws.max_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    
    # Блок восстановления формул и статусов по индексам D-J
    for row in range(2, ws.max_row + 1):
        cell_b = ws.cell(row=row, column=2).value
        if cell_b in config.MONTHS_LIST:
            start_dir_body = row + 1
            end_dir_body = row
            for r in range(row + 1, ws.max_row + 1):
                val_b = ws.cell(row=r, column=2).value
                if val_b in config.MONTHS_LIST or (val_b and not str(val_b).startswith("•")):
                    end_dir_body = r - 1
                    break
                if r == ws.max_row:
                    end_dir_body = ws.max_row
            
            ws.cell(row=row, column=10).value = f"=IF(SUBTOTAL(9, C{start_dir_body}:C{end_dir_body})>0, \"В работе\", \"\")"
            
    return ws.max_row
