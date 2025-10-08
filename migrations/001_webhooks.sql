-- Webhooks Migration
-- Creates webhooks table for real-time event notifications

-- Create webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add RLS policies
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own webhooks
CREATE POLICY "Users can view own webhooks"
ON webhooks FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can insert their own webhooks
CREATE POLICY "Users can insert own webhooks"
ON webhooks FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own webhooks
CREATE POLICY "Users can update own webhooks"
ON webhooks FOR UPDATE
USING (auth.uid() = user_id);

-- Policy: Users can delete their own webhooks
CREATE POLICY "Users can delete own webhooks"
ON webhooks FOR DELETE
USING (auth.uid() = user_id);

-- Add indexes
CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_is_active ON webhooks(is_active) WHERE is_active = true;
CREATE INDEX idx_webhooks_events ON webhooks USING GIN(events);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_webhooks_updated_at
BEFORE UPDATE ON webhooks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE webhooks IS 'Stores webhook configurations for real-time event notifications';
COMMENT ON COLUMN webhooks.url IS 'Webhook delivery URL (must be HTTPS in production)';
COMMENT ON COLUMN webhooks.events IS 'Array of subscribed event types (e.g., source.created)';
COMMENT ON COLUMN webhooks.secret IS 'Optional secret for HMAC signature verification';
COMMENT ON COLUMN webhooks.is_active IS 'Whether webhook is active (can be disabled without deletion)';
