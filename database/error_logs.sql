CREATE TABLE IF NOT EXISTS error_logs (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    error_code TEXT NOT NULL,
    error_message TEXT,
    module TEXT,
    timestamp TIMESTAMPTZ DEFAULT now(),
    stack_trace TEXT,
    resolved BOOLEAN DEFAULT false
);

CREATE INDEX idx_error_logs_device_id ON error_logs(device_id);
CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX idx_error_logs_resolved ON error_logs(resolved);

COMMENT ON TABLE error_logs IS 'Stores application errors for debugging and monitoring';