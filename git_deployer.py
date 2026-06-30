import os
import json
import subprocess
import config

def get_current_git_version():
    try:
        res = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True, check=True)
        version = res.stdout.strip()
        if version.startswith('v'):
            parts = version[1:].split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            return f"v{'.'.join(parts)}"
        return "v2.1"
    except Exception:
        return "v2.1"

def generate_auto_changelog(session_added_rows=None):
    if session_added_rows:
        directions = set([r[0] for r in session_added_rows])
        months = set([r[2] for r in session_added_rows])
        return f"Добавлены новые записи для: {', '.join(directions)} ({', '.join(months)})"
    
    json_path = "changes.json"
    if os.path.exists(json_path) and os.path.getsize(json_path) > 2:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                changes = json.load(f)
            if changes:
                months_edited = []
                for k, v in changes.items():
                    if "||" in k:
                        months_edited.append(k.split("||")[-1])
                    elif isinstance(v, dict) and "label" in v:
                        months_edited.append(v["label"].strip())
                if months_edited:
                    return f"Внесены ручные изменения сумм для месяцев: {', '.join(set(months_edited))}"
        except Exception:
            pass
            
    return "Плановое обновление структуры и формул трекера"

def clear_changes_json():
    json_path = "changes.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            print(" [ОЧИСТКА] Буфер временных изменений changes.json успешно очищен.")
        except Exception as e:
            print(f" [ПРЕДУПРЕЖДЕНИЕ] Не удалось очистить changes.json: {e}")

def run_production_pipeline(session_added_rows=None):
    print("\n [ДВИЖОК] Шаг 1: Запуск локальной генерации таблицы...")
    result = subprocess.run(["python3", "main.py"])
    if result.returncode != 0:
        print(" [ОШИБКА] Сборка завершилась неудачно. Отправка в репозиторий заблокирована.")
        return False
        
    print("\n [ДВИЖОК] Шаг 2: Запрос синхронизации с облаком")
    push_choice = input("Выгрузить обновленный трекер в репозиторий GitHub? (да/нет): ").strip().lower()
    
    if push_choice in ("да", "y", "yes"):
        default_ver = get_current_git_version()
        default_logs = generate_auto_changelog(session_added_rows)
        
        print("\n Настройка метаданных коммита:")
        user_ver = input(f"Номер версии [По умолчанию: {default_ver}]: ").strip()
        final_ver = user_ver if user_ver else default_ver
        
        user_logs = input(f"Описание изменений [По умолчанию: {default_logs}]: ").strip()
        final_logs = user_logs if user_logs else default_logs
        
        commit_message = f"{final_ver} – {final_logs}"
        print(f"\n [GIT] Будет отправлено с описанием: \"{commit_message}\"")
        
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_message])
        subprocess.run(["git", "tag", "-a", final_ver, "-m", final_logs])
        push_res = subprocess.run(["git", "push", "origin", "main", "--tags"])
        
        if push_res.returncode == 0:
            print(" [УСПЕХ] Все файлы и тег версии успешно отправлены на GitHub!")
            clear_changes_json()
            return True
        else:
            print(" [ОШИБКА GIT] Не удалось отправить файлы в облако. Проверьте сеть или доступы.")
            return False
    else:
        print(" [ИНФО] Изменения сохранены только локально на Mac. Выгрузка отменена.")
        clear_changes_json()
        return True
