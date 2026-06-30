import config

def get_status_text(num, total):
    if num == 1: return "[ОДОБРЕНО] Документы согласованы"
    if num == 2: return "[В РАБОТЕ] На согласовании / проверке"
    if num == 3: return "[ОЖИДАНИЕ] Еще не началось согласование"
    return "[ОДОБРЕНО] Документы согласованы" if num == 1 else "[ОЖИДАНИЕ] Ждет старта" if total == 0 else ""

def apply_row_style(ws, row_idx, font, fill, border, alignment=None, is_center_cols=False):
    # Общая ширина строки теперь 10 колонок (A-J)
    for idx in range(1, 11):
        cell = ws.cell(row=row_idx, column=idx)
        cell.font, cell.border = font, border
        if fill: cell.fill = fill
        if alignment: cell.alignment = alignment
        elif is_center_cols and idx in (1, 4, 5, 6, 7, 8): cell.alignment = config.ALIGN_C

def build_structure(ws, mock_data, saved_statuses, saved_sums):
    item_id, current_row = 1, 2
    for direction in mock_data.keys():
        dir_row = current_row
        ws.append([f"{item_id}", direction, "", "", "", "", "", "", "", ""])
        ws.row_dimensions[current_row].height, ws.row_dimensions[current_row].outlineLevel = 26, 0
        apply_row_style(ws, current_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, is_center_cols=True)
        current_row += 1
        start_dir_body = current_row
        
        for sub_obj in mock_data[direction].keys():
            obj_row = current_row
            ws.append(["", f" Подобъект {sub_obj}", "", "", "", "", "", "", "", ""])
            ws.row_dimensions[current_row].height, ws.row_dimensions[current_row].outlineLevel = 24, 1
            apply_row_style(ws, current_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, is_center_cols=True)
            current_row += 1
            mth_rows = []
            
            for r_key in config.MONTHS_LIST:
                if r_key not in mock_data[direction][sub_obj]: continue
                mth_row = current_row
                mth_rows.append(mth_row)
                ws.append(["", f" {r_key}", "", "", "", "", "", "", "", ""])
                ws.row_dimensions[mth_row].height, ws.row_dimensions[mth_row].outlineLevel = 22, 2
                current_row += 1
                start_doc = current_row
                
                raw_data = mock_data[direction][sub_obj][r_key]
                val = saved_sums.get((direction, sub_obj, r_key))
                
                if val is None:
                    if isinstance(raw_data, (list, tuple)) and len(raw_data) > 0:
                        val = raw_data[0]
                    else:
                        val = raw_data
                
                for i, d_name in enumerate(config.DOCUMENTS_LIST):
                    # Записываем пустую строку в столбец I (Опл.) и J (Статус)
                    ws.append(["", f" • {d_name}", val if i == 0 else "", "", "", "", "", "", "", ""])
                    ws.row_dimensions[current_row].height, ws.row_dimensions[current_row].outlineLevel = 20, 3
                    
                    hist_key = (direction, sub_obj, r_key, d_name)
                    if hist_key in saved_statuses:
                        old_vals = saved_statuses[hist_key]
                        ws[f'D{current_row}'].value = old_vals[0] if isinstance(old_vals, (list, tuple)) else old_vals
                        ws[f'E{current_row}'].value = old_vals[1] if isinstance(old_vals, (list, tuple)) and len(old_vals) > 1 else old_vals
                        ws[f'F{current_row}'].value = old_vals[2] if isinstance(old_vals, (list, tuple)) and len(old_vals) > 2 else old_vals
                        ws[f'G{current_row}'].value = old_vals[3] if isinstance(old_vals, (list, tuple)) and len(old_vals) > 3 else old_vals
                        ws[f'H{current_row}'].value = old_vals[4] if isinstance(old_vals, (list, tuple)) and len(old_vals) > 4 else None
                    else:
                        if isinstance(raw_data, (list, tuple)):
                            def_status = raw_data[-1] if len(raw_data) > 1 else None
                        else:
                            def_status = raw_data
                        
                        if def_status is not None:
                            ws[f'D{current_row}'] = ws[f'E{current_row}'] = ws[f'F{current_row}'] = ws[f'G{current_row}'] = ws[f'H{current_row}'] = def_status
                            
                    cur_h = ws[f'H{current_row}'].value
                    ws[f'J{current_row}'] = get_status_text(cur_h, val) if cur_h in (1,2,3) else ("[ОЖИДАНИЕ] Ждет старта" if val == 0 else "")
                    
                    apply_row_style(ws, current_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    ws.cell(row=current_row, column=1).alignment = config.ALIGN_C
                    ws.cell(row=current_row, column=3).number_format = '#,##0'
                    ws.cell(row=current_row, column=3).alignment = config.ALIGN_R
                    for col_idx in (4, 5, 6, 7, 8): 
                        ws.cell(row=current_row, column=col_idx).alignment = config.ALIGN_C
                    current_row += 1
                    
                end_doc = current_row - 1
                ws[f'C{mth_row}'] = f"=SUM(C{start_doc}:C{end_doc})"
                
                # Скрытый проверочный статус уходит в 11-ю колонку K
                ws.cell(row=mth_row, column=11, value=f"=MAX(D{start_doc}:H{end_doc})")
                
                # Итоговая текстовая формула считывает данные из K и записывает результат в J
                ws[f'J{mth_row}'] = f'=IF(K{mth_row}=1; "[ОДОБРЕНО] Документы согласованы"; IF(K{mth_row}=2; "[В РАБОТЕ] На согласовании / проверке"; IF(K{mth_row}=3; "[ОЖИДАНИЕ] Еще не началось согласование"; "")))'
                
                apply_row_style(ws, mth_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, is_center_cols=True)
                ws.cell(row=mth_row, column=3).number_format = '#,##0'
                ws.cell(row=mth_row, column=3).alignment = config.ALIGN_R
                
            if mth_rows: ws[f'C{obj_row}'] = "=" + "+".join([f"C{m}" for m in mth_rows])
        end_dir_body = current_row - 1
        sub_obj_rows = [r for r in range(start_dir_body, end_dir_body) if ws.cell(row=r, column=2).value and str(ws.cell(row=r, column=2).value).startswith(" Подобъект")]
        if sub_obj_rows: ws[f'C{dir_row}'] = "=" + "+".join([f"C{s}" for s in sub_obj_rows])
        item_id += 1
    return current_row
