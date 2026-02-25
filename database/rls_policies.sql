-- Enable Row Level Security
ALTER TABLE pos_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE stolen_cookies ENABLE ROW LEVEL SECURITY;
ALTER TABLE exfil ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- Policies for pos_clients
CREATE POLICY "Users can view their own clients" ON pos_clients
    FOR SELECT USING (auth.role() = 'authenticated' AND client_serial = auth.uid()::text);
CREATE POLICY "Service role full access" ON pos_clients
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for service_requests
CREATE POLICY "Users can view their own requests" ON service_requests
    FOR SELECT USING (auth.role() = 'authenticated' AND target_client = auth.uid()::text);
CREATE POLICY "Service role full access" ON service_requests
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for device_keys
CREATE POLICY "Service role only" ON device_keys
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for stolen_cookies
CREATE POLICY "Service role only" ON stolen_cookies
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for exfil
CREATE POLICY "Service role only" ON exfil
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for error_logs
CREATE POLICY "Service role only" ON error_logs
    FOR ALL USING (auth.role() = 'service_role');