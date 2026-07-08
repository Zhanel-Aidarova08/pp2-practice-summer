# phonebook.py
# Главный файл приложения TSIS1 — PhoneBook с расширенными данными.
#
# Что здесь есть (новое в TSIS1, поверх Practice 7-8):
#   1. Добавление контакта с email, датой рождения, группой
#   2. Добавление доп. телефона существующему контакту (add_phone)
#   3. Перемещение контакта в группу (move_to_group)
#   4. Расширенный поиск (search_contacts) - по имени/email/телефонам
#   5. Фильтр по группе
#   6. Поиск по email (частичное совпадение)
#   7. Сортировка списка (по имени / дню рождения / дате добавления)
#   8. Постраничный вывод (next/prev/quit)
#   9. Экспорт всех контактов в JSON
#  10. Импорт контактов из JSON (с проверкой дублей)
#  11. Импорт из CSV (с новыми полями)
#
# Все подсказки и сообщения на экране — на английском (проще для
# консоли Windows, там не всегда нормально показывается кириллица).

import csv
import json
from datetime import date

from connect import get_connection


# ============================================================
#  Вспомогательная функция: превращаем DATE/дату в строку,
#  чтобы можно было сохранить её в JSON
# ============================================================
def to_json_safe(value):
    if isinstance(value, date):
        return value.isoformat()  # например "1998-05-12"
    return value


# ============================================================
# 1. Добавление нового контакта (консоль)
# ============================================================
def add_contact(conn):
    print("\n--- New contact ---")
    name = input("Name: ").strip()
    phone = input("Main phone: ").strip()
    email = input("Email (leave empty to skip): ").strip() or None
    birthday = input("Birthday YYYY-MM-DD (leave empty to skip): ").strip() or None
    group_name = input("Group (Family/Work/Friend/Other, leave empty to skip): ").strip() or None

    cur = conn.cursor()

    group_id = None
    if group_name:
        # ищем группу, если нет - создаём
        cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
        row = cur.fetchone()
        if row:
            group_id = row[0]
        else:
            cur.execute(
                "INSERT INTO groups (name) VALUES (%s) RETURNING id",
                (group_name,),
            )
            group_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO contacts (name, phone, email, birthday, group_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (name, phone, email, birthday, group_id),
    )
    conn.commit()
    cur.close()
    print("Contact added!")


# ============================================================
# 2. Добавить доп. телефон существующему контакту
#    (вызывает процедуру add_phone из procedures.sql)
# ============================================================
def add_phone(conn):
    print("\n--- Add phone to contact ---")
    name = input("Contact name: ").strip()
    phone = input("New phone: ").strip()
    phone_type = input("Type (home/work/mobile): ").strip()

    cur = conn.cursor()
    try:
        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
        conn.commit()
        print("Phone added!")
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cur.close()


# ============================================================
# 3. Переместить контакт в другую группу
#    (вызывает процедуру move_to_group)
# ============================================================
def move_to_group(conn):
    print("\n--- Move contact to a group ---")
    name = input("Contact name: ").strip()
    group_name = input("New group: ").strip()

    cur = conn.cursor()
    try:
        cur.execute("CALL move_to_group(%s, %s)", (name, group_name))
        conn.commit()
        print("Done! Contact moved to group:", group_name)
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cur.close()


# ============================================================
# 4. Расширенный поиск (по имени / email / всем телефонам)
#    (вызывает функцию search_contacts)
# ============================================================
def search_contacts(conn):
    query = input("\nSearch text: ").strip()
    cur = conn.cursor()
    cur.execute("SELECT * FROM search_contacts(%s)", (query,))
    rows = cur.fetchall()
    cur.close()

    if not rows:
        print("Nothing found.")
        return

    print(f"\nFound contacts: {len(rows)}")
    for row in rows:
        print(f"  id={row[0]} | {row[1]} | email={row[2]} | birthday={row[3]}")


# ============================================================
# 5. Фильтр по группе
# ============================================================
def filter_by_group(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM groups ORDER BY name")
    groups = [r[0] for r in cur.fetchall()]
    print("\nAvailable groups:", ", ".join(groups))
    group_name = input("Enter group name: ").strip()

    cur.execute(
        """
        SELECT c.id, c.name, c.phone, c.email
        FROM contacts c
        JOIN groups g ON g.id = c.group_id
        WHERE g.name = %s
        ORDER BY c.name
        """,
        (group_name,),
    )
    rows = cur.fetchall()
    cur.close()

    if not rows:
        print("No contacts in this group.")
        return

    for row in rows:
        print(f"  id={row[0]} | {row[1]} | phone={row[2]} | email={row[3]}")


# ============================================================
# 6. Поиск по email (частичное совпадение, например "gmail")
# ============================================================
def search_by_email(conn):
    part = input("\nPart of email to search (e.g. gmail): ").strip()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email FROM contacts WHERE email ILIKE %s ORDER BY name",
        (f"%{part}%",),
    )
    rows = cur.fetchall()
    cur.close()

    if not rows:
        print("Nothing found.")
        return

    for row in rows:
        print(f"  id={row[0]} | {row[1]} | email={row[2]}")


# ============================================================
# 7. Сортированный список контактов
# ============================================================
def sorted_list(conn):
    print("\nSort by: 1) name  2) birthday  3) date added")
    choice = input("Choice (1-3): ").strip()

    column_map = {
        "1": "name",
        "2": "birthday",
        "3": "created_at",
    }
    column = column_map.get(choice, "name")

    cur = conn.cursor()
    # column берём из заранее известного словаря, поэтому это безопасно
    cur.execute(f"SELECT id, name, birthday, created_at FROM contacts ORDER BY {column}")
    rows = cur.fetchall()
    cur.close()

    for row in rows:
        print(f"  id={row[0]} | {row[1]} | birthday={row[2]} | added={row[3]}")


# ============================================================
# 8. Постраничная навигация (next / prev / quit)
#    Использует LIMIT/OFFSET так же, как функция пагинации
#    из Practice 8.
# ============================================================
def paginated_view(conn):
    page_size = 5
    offset = 0

    while True:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, phone FROM contacts ORDER BY id LIMIT %s OFFSET %s",
            (page_size, offset),
        )
        rows = cur.fetchall()
        cur.close()

        print(f"\n--- Page (offset={offset}) ---")
        if not rows:
            print("No more records.")
        for row in rows:
            print(f"  id={row[0]} | {row[1]} | {row[2]}")

        cmd = input("\nCommand (next / prev / quit): ").strip().lower()
        if cmd == "next":
            offset += page_size
        elif cmd == "prev":
            offset = max(0, offset - page_size)
        elif cmd == "quit":
            break
        else:
            print("Unknown command.")


# ============================================================
# 9. Экспорт всех контактов в JSON
# ============================================================
def export_json(conn):
    filename = input("\nExport file name (e.g. export.json): ").strip()
    if not filename:
        filename = "export.json"

    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.id, c.name, c.phone, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY c.id
        """
    )
    contacts_rows = cur.fetchall()

    result = []
    for row in contacts_rows:
        contact_id, name, phone, email, birthday, group_name = row

        # достаём все доп. телефоны этого контакта
        cur.execute(
            "SELECT phone, type FROM phones WHERE contact_id = %s", (contact_id,)
        )
        phones = [{"phone": p, "type": t} for (p, t) in cur.fetchall()]

        result.append(
            {
                "name": name,
                "phone": phone,
                "email": email,
                "birthday": to_json_safe(birthday),
                "group": group_name,
                "phones": phones,
            }
        )

    cur.close()

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(result)} contacts to {filename}")


# ============================================================
# 10. Импорт контактов из JSON (с проверкой дублей по имени)
# ============================================================
def import_json(conn):
    filename = input("\nJSON file name to import: ").strip()

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("File not found.")
        return
    except json.JSONDecodeError as e:
        print("File is broken or not valid JSON:", e)
        return

    cur = conn.cursor()

    for item in data:
        name = item.get("name")
        phone = item.get("phone")
        email = item.get("email")
        birthday = item.get("birthday")
        group_name = item.get("group")

        # проверяем, есть ли уже контакт с таким именем
        cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
        existing = cur.fetchone()

        if existing:
            answer = input(
                f'Contact "{name}" already exists. Skip (s) or overwrite (o)? '
            ).strip().lower()
            if answer != "o":
                continue  # пропускаем этот контакт

            contact_id = existing[0]
            cur.execute(
                """
                UPDATE contacts
                SET phone = %s, email = %s, birthday = %s
                WHERE id = %s
                """,
                (phone, email, birthday, contact_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO contacts (name, phone, email, birthday)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, phone, email, birthday),
            )
            contact_id = cur.fetchone()[0]

        # обрабатываем группу
        if group_name:
            cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
            g = cur.fetchone()
            if g:
                group_id = g[0]
            else:
                cur.execute(
                    "INSERT INTO groups (name) VALUES (%s) RETURNING id",
                    (group_name,),
                )
                group_id = cur.fetchone()[0]
            cur.execute(
                "UPDATE contacts SET group_id = %s WHERE id = %s",
                (group_id, contact_id),
            )

        # добавляем доп. телефоны, если есть
        for phone_item in item.get("phones", []):
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                (contact_id, phone_item.get("phone"), phone_item.get("type")),
            )

    conn.commit()
    cur.close()
    print("JSON import finished.")


# ============================================================
# 11. Импорт из CSV (расширенный, с новыми полями)
#     Ожидаемые колонки: name,phone,type,email,birthday,group
# ============================================================
def import_csv(conn):
    filename = input("\nCSV file name to import: ").strip()
    if not filename:
        filename = "contacts.csv"

    cur = conn.cursor()

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                name = row.get("name")
                phone = row.get("phone")
                phone_type = row.get("type") or "mobile"
                email = row.get("email") or None
                birthday = row.get("birthday") or None
                group_name = row.get("group") or None

                group_id = None
                if group_name:
                    cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
                    g = cur.fetchone()
                    if g:
                        group_id = g[0]
                    else:
                        cur.execute(
                            "INSERT INTO groups (name) VALUES (%s) RETURNING id",
                            (group_name,),
                        )
                        group_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO contacts (name, phone, email, birthday, group_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, phone, email, birthday, group_id),
                )
                contact_id = cur.fetchone()[0]

                # тот же телефон дублируем и в таблицу phones с типом
                if phone:
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                        (contact_id, phone, phone_type),
                    )

                count += 1

        conn.commit()
        print(f"Imported {count} contacts from {filename}")
    except FileNotFoundError:
        print("File not found.")
    finally:
        cur.close()


# ============================================================
#  Главное меню
# ============================================================
def main_menu():
    conn = get_connection()

    menu_text = """
========== PhoneBook (TSIS 1) ==========
1  - Add contact
2  - Add phone to existing contact
3  - Move contact to a group
4  - Search (by name/email/phones)
5  - Filter by group
6  - Search by email
7  - Sorted list
8  - Paginated view (next/prev/quit)
9  - Export to JSON
10 - Import from JSON
11 - Import from CSV
0  - Exit
=========================================
"""

    actions = {
        "1": add_contact,
        "2": add_phone,
        "3": move_to_group,
        "4": search_contacts,
        "5": filter_by_group,
        "6": search_by_email,
        "7": sorted_list,
        "8": paginated_view,
        "9": export_json,
        "10": import_json,
        "11": import_csv,
    }

    while True:
        print(menu_text)
        choice = input("Choose an action: ").strip()

        if choice == "0":
            print("Bye!")
            break

        action = actions.get(choice)
        if action is None:
            print("No such menu option, try again.")
            continue

        try:
            action(conn)
        except Exception as e:
            # если что-то пошло не так, откатываем незавершённую транзакцию
            conn.rollback()
            print("An error occurred:", e)

    conn.close()


if __name__ == "__main__":
    main_menu()
