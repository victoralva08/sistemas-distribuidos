-- Tabela de pagamentos
CREATE TABLE IF NOT EXISTS payments (
    id          SERIAL PRIMARY KEY,
    event_id    UUID        NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    amount      NUMERIC(10,2) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'processed',
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabela de estoque
CREATE TABLE IF NOT EXISTS inventory (
    id          SERIAL PRIMARY KEY,
    event_id    UUID        NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    product_id  VARCHAR(20) NOT NULL,
    quantity    INT         NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'reserved',
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabela de auditoria (todas as mensagens)
CREATE TABLE IF NOT EXISTS audit_log (
    id          SERIAL PRIMARY KEY,
    event_id    UUID        NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    routing_key VARCHAR(50) NOT NULL,
    payload     JSONB       NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_payments_event_id   ON payments(event_id);
CREATE INDEX IF NOT EXISTS idx_inventory_event_id  ON inventory(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_id      ON audit_log(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_routing_key   ON audit_log(routing_key);
