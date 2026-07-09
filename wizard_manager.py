import wizard_menus
import wizard_edits
import db_viewer
import builder
import config
import wizard_git
import os


def build_code_snapshot_txt(output_path: str):
    exclude_dirs = {
        ".git",
        "__pycache__",
        ".blackbox",
        "node_modules",
        ".mypy_cache",
        "dist",
        "build",
    }

    exclude_exts = {
        ".xlsx",
        ".xls",
        ".zip",
        ".pdf",
        ".odt",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".mp3",
        ".mp4",
        ".mov",
        ".wav",
        ".avi",
        ".7z",
        ".rar",
        ".tar",
        ".gz",
        ".obj",
        ".o",
        ".a",
        ".bin",
        ".exe",
        ".dylib",
        ".so",
        ".dll",
    }

    code_exts = {
        ".py",
        ".json",
        ".txt",
        ".md",
        ".yml",
        ".yaml",
        ".js",
        ".ts",
        ".css",
        ".html",
        ".htm",
        ".xml",
    }

    def should_skip_dir(dir_name: str) -> bool:
        return dir_name in exclude_dirs

    def should_include_file(file_path: str) -> bool:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext in exclude_exts:
            return False
        if ext == "":
            return False
        return ext in code_exts

    files_collected = []
    root_dir = os.path.abspath(os.getcwd())
    output_path_abs = os.path.abspath(output_path)

    for cur_root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        for fn in files:
            fp = os.path.join(cur_root, fn)
            if os.path.abspath(fp) == output_path_abs:
                continue
            try:
                if should_include_file(fp):
                    files_collected.append(fp)
            except Exception:
                continue

    files_collected.sort(key=lambda p: os.path.relpath(p, root_dir).lower())

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("=== PROJECT CODE SNAPSHOT ===\n")
        out.write(f"Root: {root_dir}\n")
        out.write(f"Generated: {__import__('datetime').datetime.now().isoformat()}\n")
        out.write(f"Files: {len(files_collected)}\n")
        out.write("================================\n\n")

        for fp in files_collected:
            rel = os.path.relpath(fp, root_dir)
            out.write(f"=== FILE: ./{rel} ===\n")
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
            except UnicodeDecodeError:
                out.write("[SKIPPED: not UTF-8]\n")
            except Exception as e:
                out.write(f"[SKIPPED: {e}]\n")
            out.write("\n\n")


def main_menu():
    while True:
        print("\n>>> ГЛАВНЫЙ ПУЛЬТ УПРАВЛЕНИЯ СТРОИТЕЛЬНЫМ ТРЕКЕРОМ <<<")
        print(" 1. Показать текущую структуру базы (Дерево)")
        print(" 2. Добавить новую ветку структуры (Направление / Подобъект / Месяц)")
        print(" 3. Внести изменения в таблицу (Сумма / Переименование / СтрК)")
        print(" 4. Сгенерировать финальный отчет Excel (с отправкой на GitHub)")
        print(" 5. СЕРВИСНЫЕ НАСТРОЙКИ")
        print(" 0. Выход из программы")

        choice = input("\nВыберите действие (0-4): ").strip()

        if choice not in ("1", "2", "3", "4", "5", "0"):
            print(" [ОШИБКА] Неверный выбор.")
            continue

        if choice == "1":
            db_viewer.print_data()
        elif choice == "2":
            wizard_menus.menu_add_record()
            wizard_git.register_action("branch_added")
        elif choice == "3":
            wizard_edits.menu_edit_data(wizard_menus.select_hierarchy_target)
        elif choice == "4":
            print("\n⚙ Запущена генерация Excel...")
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Реестр Актов"

            ws.sheet_view.showGridLines = True
            builder.build_structure(ws)

            file_path = config.FULL_PATH if config.FULL_PATH else "Трекер_Акт_Выполнения.xlsx"
            try:
                wb.save(file_path)
                print(f"🚀 [УСПЕХ] Отчет успешно сохранен локально: {file_path}")
                wizard_git.run_git_sync()

            except PermissionError:
                print("❌ [ОШИБКА ДОСТУПА] Файл Excel открыт! Закройте его для генерации.")
            except Exception as e:
                print(f"❌ [ОШИБКА] Ошибка при сохранении отчета: {e}")

        elif choice == "5":
            print("\n[СЕРВИСНЫЕ НАСТРОЙКИ]")
            print("1 - Отключить подробные логи DEBUG в терминале")
            print("2 - Включить подробные логи DEBUG обратно")
            print("3 - Проверить текущую конфигурацию ширины столбцов в builder.py")
            print("4 - Собрать все файлы кода в один txt (ai_project_snapshot.txt)")
            print("5 - Конвертировать ai_project_snapshot.txt в PDF")

            srv_choice = input("Выберите действие: ").strip()

            if srv_choice == "4":
                output_name = "ai_project_snapshot.txt"
                output_path = os.path.join(os.getcwd(), output_name)
                build_code_snapshot_txt(output_path)
                print(f"\n✅ [УСПЕХ] Снимок кода сформирован: {output_path}")
                input("Нажмите Enter...")

            elif srv_choice == "5":
                txt_name = "ai_project_snapshot.txt"
                txt_path = os.path.join(os.getcwd(), txt_name)
                pdf_name = "ai_project_snapshot.pdf"
                pdf_path = os.path.join(os.getcwd(), pdf_name)

                if not os.path.exists(txt_path):
                    print(
                        f"❌ [ОШИБКА] TXT не найден: {txt_path}. Сначала выполните пункт 5->4 (генерация txt)."
                    )
                    input("Нажмите Enter...")
                else:
                    try:
                        import pdf_from_text

                        pdf_from_text.ensure_pdf(txt_path, pdf_path)
                        print(f"\n✅ [УСПЕХ] PDF сформирован: {pdf_path}")
                    except Exception as e:
                        print(f"❌ [ОШИБКА] Не удалось сформировать PDF: {e}")
                    input("Нажмите Enter...")

            elif srv_choice == "3":
                print("\n[ДИАГНОСТИКА ШИРИНЫ СТАТУСНЫХ КОЛОНОК]")
                print("Целевой размер: 1.35 см -> Значение в builder.py/openpyxl: 14.0")
                print("Проверяем диапазон колонок со статусами (D, E, F, G, H)...")

                if hasattr(builder, "test_columns_width_logic"):
                    builder.test_columns_width_logic()
                else:
                    print(" [ОШИБКА] В builder.py не найдена функция test_columns_width_logic().")

            else:
                import logging

                if srv_choice == "1":
                    logging.getLogger().setLevel(logging.WARNING)
                    print(" [ОК] Подробные логи DEBUG отключены.")
                elif srv_choice == "2":
                    logging.getLogger().setLevel(logging.DEBUG)
                    print(" [ОК] Подробные логи DEBUG включены.")
                else:
                    print(" [ОШИБКА] Неверный выбор.")

        elif choice == "0":
            print("\nПрограмма успешно завершена. Всего доброго!")
            break
        else:
            print(" [ОШИБКА] Неверный выбор.")


if __name__ == "__main__":
    main_menu()

