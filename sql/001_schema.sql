-- Схема БД бронирования Health Klinik (PostgreSQL / Railway)
-- Можно применить вручную: psql $DATABASE_URL -f sql/001_schema.sql
-- Предпочтительный путь: Alembic-миграции (backend/alembic)

BEGIN;

CREATE TYPE booking_status AS ENUM (
    'pending',
    'confirmed',
    'cancelled',
    'completed'
);

CREATE TABLE therapists (
    id              SERIAL PRIMARY KEY,
    telegram_id     BIGINT NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    specialization  VARCHAR(300) NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX ix_therapists_telegram_id ON therapists (telegram_id);

CREATE TABLE clients (
    id              SERIAL PRIMARY KEY,
    telegram_id     BIGINT UNIQUE,
    name            VARCHAR(200) NOT NULL,
    phone           VARCHAR(50) NOT NULL,
    email           VARCHAR(255) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_clients_telegram_id ON clients (telegram_id);

CREATE TABLE services (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(200) NOT NULL UNIQUE,
    duration_minutes    INTEGER NOT NULL,
    price               NUMERIC(10, 2) NOT NULL
);

CREATE TABLE bookings (
    id                      SERIAL PRIMARY KEY,
    client_id               INTEGER NOT NULL REFERENCES clients (id),
    therapist_id            INTEGER NOT NULL REFERENCES therapists (id),
    service_name            VARCHAR(200) NOT NULL,
    "date"                  DATE NOT NULL,
    "time"                  TIME NOT NULL,
    status                  booking_status NOT NULL DEFAULT 'pending',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    telegram_confirm_token  UUID NOT NULL UNIQUE DEFAULT gen_random_uuid()
);

CREATE INDEX ix_bookings_client_id ON bookings (client_id);
CREATE INDEX ix_bookings_therapist_id ON bookings (therapist_id);
CREATE INDEX ix_bookings_date ON bookings ("date");
CREATE INDEX ix_bookings_status ON bookings (status);
CREATE INDEX ix_bookings_telegram_confirm_token ON bookings (telegram_confirm_token);

COMMIT;

-- Пример сидов (раскомментируй и подставь свой telegram_id терапевта):
-- INSERT INTO therapists (telegram_id, name, email, specialization, active)
-- VALUES (123456789, 'Anna Svensson', 'anna@example.com', 'Monicor & Alfa', TRUE);
--
-- INSERT INTO services (name, duration_minutes, price) VALUES
-- ('Monicor-session', 90, 1500.00),
-- ('Monicor + Alfa', 120, 2000.00);
