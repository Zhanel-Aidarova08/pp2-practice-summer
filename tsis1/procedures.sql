-- ============================================================
--  procedures.sql
--  TSIS 1 — новые процедуры и функции.
--  Процедуры из Practice 8 (upsert_contact, delete-процедура,
--  пагинация и т.д.) здесь НЕ дублируются — они должны уже
--  существовать в базе из прошлой практики.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Процедура: добавить телефон существующему контакту
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- находим id контакта по имени
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE name = p_contact_name
    LIMIT 1;

    -- если контакт не найден — сообщаем об ошибке
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Контакт "%": не найден', p_contact_name;
    END IF;

    -- проверяем, что тип телефона правильный
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Неверный тип телефона: %', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);
END;
$$;


-- ------------------------------------------------------------
-- 2. Процедура: переместить контакт в другую группу
--    (если группы не существует — создаём её)
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INTEGER;
BEGIN
    -- ищем группу
    SELECT id INTO v_group_id
    FROM groups
    WHERE name = p_group_name;

    -- если группы нет — создаём новую
    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name)
        RETURNING id INTO v_group_id;
    END IF;

    -- обновляем контакт
    UPDATE contacts
    SET group_id = v_group_id
    WHERE name = p_contact_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Контакт "%": не найден', p_contact_name;
    END IF;
END;
$$;


-- ------------------------------------------------------------
-- 3. Функция: расширенный поиск — по имени, email и ВСЕМ телефонам
--    (учитывает, что теперь телефоны хранятся в отдельной таблице)
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id       INTEGER,
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT c.id, c.name, c.email, c.birthday
    FROM contacts c
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE c.name  ILIKE '%' || p_query || '%'
       OR c.email ILIKE '%' || p_query || '%'
       OR c.phone ILIKE '%' || p_query || '%'   -- основной телефон
       OR p.phone ILIKE '%' || p_query || '%';  -- телефоны из таблицы phones
END;
$$ LANGUAGE plpgsql;
