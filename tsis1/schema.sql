-- ============================================================
--  schema.sql
--  TSIS 1 — расширенная схема PhoneBook
--  Здесь создаются ВСЕ таблицы, нужные для этого задания.
--  Если у тебя уже есть таблица contacts из Practice 7 — просто
--  выполни блок ALTER TABLE (он добавит новые поля), а таблицу
--  contacts из части CREATE TABLE можно пропустить.
-- ============================================================

-- 1. Базовая таблица contacts (как в Practice 7),
--    сюда же сразу добавлены новые поля из TSIS1.
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(20),               -- основной телефон (остался с Practice 7)
    email      VARCHAR(100),              -- новое поле
    birthday   DATE,                      -- новое поле
    group_id   INTEGER,                   -- новое поле, ссылка на группу
    created_at TIMESTAMP DEFAULT NOW()    -- нужно для сортировки "по дате добавления"
);

-- 2. Таблица групп (категорий) контакта
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- заранее добавим базовые группы, чтобы было с чем работать
INSERT INTO groups (name) VALUES
    ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

-- 3. Если таблица contacts уже существовала без новых полей —
--    эти строки просто добавят недостающие колонки.
ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS email      VARCHAR(100),
    ADD COLUMN IF NOT EXISTS birthday   DATE,
    ADD COLUMN IF NOT EXISTS group_id   INTEGER,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- связываем group_id с таблицей groups (внешний ключ)
ALTER TABLE contacts
    DROP CONSTRAINT IF EXISTS contacts_group_id_fkey;
ALTER TABLE contacts
    ADD CONSTRAINT contacts_group_id_fkey
    FOREIGN KEY (group_id) REFERENCES groups(id);

-- 4. Таблица телефонов (один контакт — много телефонов)
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) CHECK (type IN ('home', 'work', 'mobile'))
);
