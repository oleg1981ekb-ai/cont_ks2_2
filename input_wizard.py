import os
import subprocess
import config

def save_config(data_rows, months, docs):
    """Генерирует config.py с расширенным набором заголовков"""
    with open("config.py", "w", encoding="utf-8") as f:
        f.write('import os\nfrom openpyxl.styles import Font, Alignment, PatternFill, Border, Side\n\n')
        f.write('DATA_ROWS = [\n')
        for row in data_rows:
            status_val = row[4] if row[4] is not None else "None"
            f.write(f'    ("{row[0]}", "{row[1]}", "{row[2]}", {row[3]}, {status_val}),\n')
        f.write(']\n\n')
        f.write(f'MONTHS_LIST = {repr(months)}\n')
        f.write(f'DOCUMENTS_LIST = {repr(docs)}\n\n')
        f.write('FOLDER_NAME = ""\nFILE_NAME = "Трекер_Акт_Выполнения.xlsx"\nFULL_PATH = os.path.join(FOLDER_NAME, FILE_NAME)\n\n')
        f.write('FONT_HDR = Font(name="Calibri", size=11, bold=True, color="FFFFFF")\nFONT_DIR = Font(name="Calibri", size=12, bold=True, color="FFFFFF")\n')
        f.write('FONT_OBJ = Font(name="Calibri", size=11, bold=True, color="000000")\nFONT_MTH = Font(name="Calibri", size=11, bold=True, italic=True, color="000000")\n')
        f.write('FONT_DATA = Font(name="Calibri", size=11)\n\nFILL_HDR = FILL_DIR = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")\n')
        f.write('FILL_OBJ = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")\nFILL_MTH = PatternFill(start_color="EAEAEA", end_color="EAEAEA", fill_type="solid")\n\n')
        f.write('THIN_BORDER = Border(left=Side(style="thin", color="B0B0B0"), right=Side(style="thin", color="B0B0B0"), top=Side(style="thin", color="B0B0B0"), bottom=Side(style="thin", color="B0B0B0"))\n\n')
        f.write('ALIGN_C = Alignment(horizontal="center", vertical="center", wrap_text=True)\nALIGN_L = Alignment(horizontal="left", vertical="center", wrap_text=True)\nALIGN_R = Alignment(horizontal="right", vertical="center")\n\n')
        # Обновленный список заголовков с новым столбцом
        f.write('HEADERS = ["№ п/п", "Наименование объекта / Месяц / Документ", "Сумма (руб.)", "СтрК", "СДО", "ГенДир", "ГенДир Один экс.", "Текущий статус акта"]\n')

def print_data():
    print("\n=== ТЕКУЩИЕ ЗАПИСИ В СИСТЕМЕ ===")
    for i, r in enumerate(config.DATA_ROWS, 1):
        print(f"{i}. Направление: {r[0]} | Подобъект: {r[1]} | Месяц: {r[2]} | Сумма: {r[3]} руб. | Статус: {r[4]}")
    print("================================")

def get_input_with_nav(prompt_text, current_step, total_steps):
    full_prompt = f"{prompt_text} (или 'назад'/'выход'): "
    user_input = input(full_prompt).strip()
    if user_input.lower() == 'выход': return 'EXIT'
    if user_input.lower() == 'назад': return 'BACK'
    return user_input

def run_wizard():
    while True:
        import importlib
        importlib.reload(config)
        print("\n--- СМАРТ-ПОМОЩНИК УПРАВЛЕНИЯ ТРЕКЕРОМ ---")
        print("1. Посмотреть текущие записи данных")
        print("2. Добавить новую запись (Объект / Месяц)")
        print("3. Сгенерировать Excel и отправить на GitHub")
        print("4. Выйти из помощника")
        choice = input("Выберите действие (1-4): ").strip()
        
        if choice == "1":
            print_data()
        elif choice == "2":
            print("\n>> ДОБАВЛЕНИЕ НОВОЙ ЗАПИСИ")
            steps = [
                "1. Введите Направление (например, 01_АНАПА (Таманская))",
                "2. Введите Подобъект (например, 271)",
                "3. Введите Месяц (например, Апрель)",
                "4. Введите Сумму цифрами (без пробелов)",
                "5. Выберите стартовый статус (1-3, или 0 - Нет статуса)"
            ]
            answers = [""] * 5
            current_idx, cancelled = 0, False
            while current_idx < len(steps):
                res = get_input_with_nav(steps[current_idx], current_idx + 1, len(steps))
                if res == 'EXIT':
                    print("🛑 Ввод отменен."); cancelled = True; break
                elif res == 'BACK':
                    if current_idx == 0: print("⏮️ Возврат в меню."); cancelled = True; break
                    else: current_idx -= 1; continue
                if current_idx == 3:
                    try: answers[current_idx] = int(res)
                    except ValueError: print("❌ Ошибка: Сумма должна быть числом!"); continue
                elif current_idx == 4:
                    answers[current_idx] = int(res) if res in ("1", "2", "3") else None
                else:
                    if not res: print("❌ Поле не может быть пустым!"); continue
                    answers[current_idx] = res
                current_idx += 1
            if not cancelled:
                new_rows = list(config.DATA_ROWS)
                new_rows.append((answers[0], answers[1], answers[2], answers[3], answers[4]))
                new_months = list(config.MONTHS_LIST)
                if answers[2] not in new_months: new_months.append(answers[2])
                save_config(new_rows, new_months, config.DOCUMENTS_LIST)
                print("✅ Запись успешно сохранена!")
        elif choice == "3":
            print("\n⚙️ Запуск автоматических процессов...")
            save_config(list(config.DATA_ROWS), list(config.MONTHS_LIST), list(config.DOCUMENTS_LIST))
            subprocess.run(["python3", "main.py"])
            print("📦 Синхронизация с репозиторием GitHub...")
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", "Added GenDir One ex column layout"])
            subprocess.run(["git", "push", "origin", "main"])
            print("🚀 Всё готово! Excel обновлен, код отправлен на GitHub.")
        elif choice == "4":
            print("До свидания!"); break
        else:
            print("❌ Неверный ввод.")

if __name__ == "__main__":
    run_wizard()
