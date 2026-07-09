import wizard_menus
import wizard_edits
import db_viewer
import builder
import config
import wizard_git
import os


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

            srv_choice = input("Выберите действие: ").strip()

            if srv_choice == "3":
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

