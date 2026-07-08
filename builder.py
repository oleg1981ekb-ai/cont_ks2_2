import logging
logging.getLogger().setLevel(logging.WARNING)

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
    if not os.path.exists(json_path):
        return ws.max_row
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
        excel_styler.apply_row_style(
            ws, ws.max_row, config.FONT_DIR, config.FILL_DIR, config.THIN_BORDER, config.ALIGN_L
        )
        ws.row_dimensions[ws.max_row].outline_level = 0

        for sub_obj in db[direction].keys():
            ws.append(["", str(sub_obj), "", "", "", "", "", "", "", ""])
            excel_styler.apply_row_style(
                ws, ws.max_row, config.FONT_OBJ, config.FILL_OBJ, config.THIN_BORDER, config.ALIGN_L
            )
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
                ws.append(
                    [row_counter, mth, float(mth_data.get("sum", 0.0)), "", "", "", "", "", "", ""]
                )
                current_row = ws.max_row
                excel_styler.apply_row_style(
                    ws, current_row, config.FONT_MTH, config.FILL_MTH, config.THIN_BORDER, config.ALIGN_L
                )
                ws.cell(row=current_row, column=1).alignment = config.ALIGN_C
                ws.cell(row=current_row, column=3).number_format = "#,##0.00"
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
                    excel_styler.apply_row_style(
                        ws, doc_row, config.FONT_DATA, None, config.THIN_BORDER, config.ALIGN_L
                    )
                    ws.cell(row=doc_row, column=3).number_format = "#,##0.00"
                    ws.row_dimensions[doc_row].outline_level = 3

                    mask = config.DOCUMENT_ROLES.get(
                        d_name,
                        {"СтрК": 1, "СДО": 1, "ГенДир": 1, "1 экз. З.": 1, "1 экз. П": 1, "Опл.": 1},
                    )

                    for col_name, col_letter_or_idx in config.COLUMN_MAPPING.items():
                        if isinstance(col_letter_or_idx, str):
                            col_idx = openpyxl.utils.column_index_from_string(col_letter_or_idx)
                        else:
                            col_idx = int(col_letter_or_idx)

                        cell = ws.cell(row=doc_row, column=col_idx)

                        # статус конкретного документа: СтрК/СДО
                        if isinstance(status_raw, dict) and d_name in status_raw:
                            doc_status_raw = status_raw[d_name]
                        else:
                            doc_status_raw = status_raw

                        status_date = doc_status_raw.get("date", "") if isinstance(doc_status_raw, dict) else ""

                        if isinstance(doc_status_raw, dict):
                            clean_status_value = (
                                doc_status_raw.get(col_name, {}).get("value")
                                if col_name in doc_status_raw
                                else doc_status_raw.get("value")
                            )
                        else:
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
                        ws.append([
                            "",
                            f"    └─ Дата изменения СтрК: {status_date}",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ])
                        log_row = ws.max_row
                        excel_styler.apply_row_style(
                            ws,
                            log_row,
                            excel_styler.FONT_LOG_DATE,
                            None,
                            config.THIN_BORDER,
                            config.ALIGN_L,
                        )
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

    # Надежный автоподбор ширины столбцов с запасом (ЭТАП 1-2)
    for col in ws.columns:
        max_len = 0
        col_letter = openpyxl.utils.get_column_letter(col[0].column)

        for cell in col:
            if cell.value is not None:
                cell_len = max(len(sub_line) for sub_line in str(cell.value).split("\n"))
                if cell_len > max_len:
                    max_len = cell_len

        # Добавляем запас в 4 символа, но с поправками по ключевым колонкам
        if col[0].column == 2:
            ws.column_dimensions[col_letter].width = max(max_len + 5, 45)
        elif col[0].column == 3:
            ws.column_dimensions[col_letter].width = max(max_len + 4, 18)
        else:
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    return ws.max_row


