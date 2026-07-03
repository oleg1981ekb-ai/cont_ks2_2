import wizard_menus
import wizard_edits
import db_viewer
import builder
import config
import os

def main_menu():
    while True:
        print("\n>>> ГЛАВНЫЙ ПУЛЬТ УПРАВЛЕНИЯ СТРОИТЕЛЬНЫМ ТРЕКЕРОМ <<<")
        print(" 1. Показать текущую структуру базы (Дерево)")
        print(" 2. Добавить новую ветку структуры (Направление / Подобъект / Месяц)")
        print(" 3. Внести изменения в таблицу (Сумма / Переименование / СтрК)")
        print(" 4. Сгенерировать финальный отчет Excel (с отправкой на GitHub)")
        print(" 0. Выход из программы")
        
        choice = input("\nВыберите действие (0-4): ").strip()
        
        if choice == "1":
            db_viewer.print_data()
        elif choice == "2":
            wizard_menus.menu_add_record()
        elif choice == "3":
            # Передаем функцию выбора целей внутрь изолированного модуля редактирования
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
                
                default_ver = getattr(config, "VERSION", "v1.0.0")
                version_input = input(f"Введите версию [По умолчанию: {default_ver}]: ").strip()
                version = version_input if version_input else default_ver
                
                comment = input("Введите комментарий к коммиту: ").strip()
                commit_msg = f"{version} {comment}".strip()
                
                print("\n📡 Синхронизация с GitHub...")
                os.system("git add .")
                os.system(f'git commit -m "{commit_msg}"')
                os.system("git push")
                print("✅ [GITHUB] Изменения отправлены!")
                
            except PermissionError:
                print("❌ [ОШИБКА ДОСТУПА] Файл Excel открыт! Закройте его для генерации.")
            except Exception as e:
                print(f"❌ [ОШИБКА] Не удалось сохранить файл или отправить в Git: {e}")
        elif choice == "0":
            print("\nПрограмма успешно завершена. Всего доброго!")
            break
        else:
            print(" [ОШИБКА] Неверный выбор.")

if __name__ == "__main__":
    main_menu()
