import config

def get_status_text(num, total):
    if num == 1: return "[ОДОБРЕНО] Документы согласованы"
    if num == 2: return "[В РАБОТЕ] На согласовании / проверке"
    if num == 3: return "[ОЖИДАНИЕ] Еще не началось согласование"
    return "[ОДОБРЕНО] Документы согласованы" if num == 1 else "[ОЖИДАНИЕ] Ждет старта" if total == 0 else ""

def apply_row_style(ws, row_idx, font, fill, border, alignment=None, is_center_cols=False):
    for idx in range(1, 9):
        cell = ws.cell(row=row_idx, column=idx)
        cell.font, cell.border = font, border
        if fill: cell.fill = fill
        if alignment: cell.alignment = alignment
        elif is_center_cols and idx in (1, 4, 5, 6, 7): cell.alignment = config.ALIGN_C

def build_structure(ws, mock_data, saved_statuses, saved_sums):
    item_id, current_row = 1, 2
    for direction in mock_data.keys():
        dir_row = current_row
        ws.append([f"{item_id}", direction, "", "", "", "", "", ""])
        ws.row_dimensions[current_row].height, ws.row_dimensions[current_row].outlineLevel = 26, 0
        apply_row_style(ws, current_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, is_center_cols=True)
        current_row += 1
        start_dir_body = current_row
        
        for sub_obj in mock_data[direction].keys():
            obj_row = current_row
            ws.append(["", f" Подобъект {sub_obj}", "", "", "", "", "", ""])
            ws.row_dimensions[current_row].height, ws.row_dimensions[current_row].outlineLevel = 24, 1
            apply_row_style(ws, current_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, is_center_cols=True)
            current_row += 1
            mth_rows = []
            
            for r_key in config.MONTHS_LIST:
                if r_key not in mock_data[direction][sub_obj]: continue
                mth_row = current_row
                mth_rows.append(mth_row)
                ws.append(["", f" {r_key}", "", "", "", "", "", ""])
                ws.row_dimensions[mth_row].height, ws.row_dimensions[mth_row].outlineLevel = 22, 2
                current_row += 1
                start_doc = current_row
                sum_key = (direction, sub_obj, r_key)
                val = saved_sums[sum_key] if sum_key in saved_sums else mock_data[direction][sub_obj][r_key]
                
                for i, d_name in enumerate(config.DOCUMENTS_LIST):
                    ws.append(["", f" • {d_name}", val if i == 0 else "", "", "", "", "", ""])
                    ws.row_dimensions[current_row].height, ws.row_dimensions[current_row].outlineLevel = 20, 3
                    
                    hist_key = (direction, sub_obj, r_key, d_name)
                    if hist_key in saved_statuses:
                        old_vals = saved_statuses[hist_key]
                        ws[f'D{current_row}'].value = old_vals
                        ws[f'E{current_row}'].value = old_vals
                        ws[f'F{current_row}'].value = old_vals
                        ws[f'G{current_row}'].value = old_vals if len(old_vals) > 2 else None
                    else:
                        def_status = mock_data[direction][sub_obj][r_key]
                        if def_status is not None: 
                            ws[f'D{current_row}'] = ws[f'E{current_row}'] = ws[f'F{current_row}'] = ws[f'G{current_row}'] = def_status
                            
                    cur_g = ws[f'G{current_row}'].value
                    ws[f'H{current_row}'] = get_status_text(cur_g, val) if cur_g in (1,2,3) else ("[ОЖИДАНИЕ] Ждет старта" if val == 0 else "")
                    
                    apply_row_style(ws, current_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L)
                    ws.cell(row=current_row, column=1).alignment = config.ALIGN_C
                    ws.cell(row=current_row, column=3).number_format = '#,##0'
                    ws.cell(row=current_row, column=3).alignment = config.ALIGN_R
                    for col_idx in (4, 5, 6, 7): 
                        ws.cell(row=current_row, column=col_idx).alignment = config.ALIGN_C
                    current_row += 1
                    
                end_doc = current_row - 1
                ws[f'C{mth_row}'] = f"=SUM(C{start_doc}:C{end_doc})"
                
                for col in ['D', 'E', 'F', 'G']: 
                    ws[f'{col}{mth_row}'] = f"=MAX({col}{start_doc}:{col}{end_doc})"
                # Исправленная формула: проверяет столбец G (максимальный статус) и выводит текст в H
                ws[f'H{mth_row}'] = f'=IF(G{mth_row}=1; "[ОДОБРЕНО] Документы согласованы"; IF(G{mth_row}=2; "[В РАБОТЕ] На согласовании / проверке"; IF(G{mth_row}=3; "[ОЖИДАНИЕ] Еще не началось согласование"; "")))'
                
                apply_row_style(ws, mth_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, is_center_cols=True)
                ws.cell(row=mth_row, column=3).number_format = '#,##0'
                ws.cell(row=mth_row, column=3).alignment = config.ALIGN_R
                
            if mth_rows: ws[f'C{obj_row}'] = "=" + "+".join([f"C{m}" for m in mth_rows])
        end_dir_body = current_row - 1
        sub_obj_rows = [r for r in range(start_dir_body, end_dir_body) if ws.cell(row=r, column=2).value and str(ws.cell(row=r, column=2).value).startswith(" Подобъект")]
        if sub_obj_rows: ws[f'C{dir_row}'] = "=" + "+".join([f"C{s}" for s in sub_obj_rows])
        item_id += 1
    return current_row
