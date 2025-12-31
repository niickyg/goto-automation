-- PostgreSQL Schema for GoTo Call Automation System
-- Version: 1.0
-- Description: Complete database schema for call tracking, summaries, action items, and KPIs

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean recreation)
DROP TABLE IF EXISTS kpis CASCADE;
DROP TABLE IF EXISTS action_items CASCADE;
DROP TABLE IF EXISTS call_summaries CASCADE;
DROP TABLE IF EXISTS calls CASCADE;

-- Drop custom types if they exist
DROP TYPE IF EXISTS call_direction CASCADE;
DROP TYPE IF EXISTS sentiment_type CASCADE;
DROP TYPE IF EXISTS action_item_status CASCADE;

-- Create custom enum types
CREATE TYPE call_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE sentiment_type AS ENUM ('positive', 'neutral', 'negative');
CREATE TYPE action_item_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');

-- Calls table: Stores call records from GoTo Connect
CREATE TABLE calls (
    id SERIAL PRIMARY KEY,
    goto_call_id VARCHAR(255) UNIQUE NOT NULL,
    direction call_direction NOT NULL,
    caller_number VARCHAR(50),
    caller_name VARCHAR(255),
    called_number VARCHAR(50),
    called_name VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    recording_url TEXT,
    recording_downloaded BOOLEAN DEFAULT FALSE,
    recording_file_path TEXT,
    webhook_received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for calls table
CREATE INDEX idx_calls_goto_call_id ON calls(goto_call_id);
CREATE INDEX idx_calls_start_time ON calls(start_time);
CREATE INDEX idx_calls_direction ON calls(direction);
CREATE INDEX idx_calls_caller_number ON calls(caller_number);
CREATE INDEX idx_calls_created_at ON calls(created_at);

-- Call summaries table: Stores AI-generated summaries and analysis
CREATE TABLE call_summaries (
    id SERIAL PRIMARY KEY,
    call_id INTEGER UNIQUE NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    transcript TEXT,
    summary TEXT,
    sentiment sentiment_type,
    urgency_score INTEGER CHECK (urgency_score >= 1 AND urgency_score <= 5),
    key_topics TEXT,
    transcription_started_at TIMESTAMP,
    transcription_completed_at TIMESTAMP,
    analysis_started_at TIMESTAMP,
    analysis_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for call_summaries table
CREATE INDEX idx_call_summaries_call_id ON call_summaries(call_id);
CREATE INDEX idx_call_summaries_sentiment ON call_summaries(sentiment);
CREATE INDEX idx_call_summaries_urgency_score ON call_summaries(urgency_score);

-- Action items table: Stores action items extracted from calls
CREATE TABLE action_items (
    id SERIAL PRIMARY KEY,
    call_id INTEGER NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    assigned_to VARCHAR(255),
    due_date TIMESTAMP,
    status action_item_status DEFAULT 'pending' NOT NULL,
    priority INTEGER CHECK (priority >= 1 AND priority <= 5),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for action_items table
CREATE INDEX idx_action_items_call_id ON action_items(call_id);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_action_items_assigned_to ON action_items(assigned_to);
CREATE INDEX idx_action_items_due_date ON action_items(due_date);
CREATE INDEX idx_action_items_priority ON action_items(priority);

-- KPIs table: Stores aggregated metrics for different time periods
CREATE TABLE kpis (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_calls INTEGER DEFAULT 0,
    total_duration_seconds INTEGER DEFAULT 0,
    avg_duration_seconds FLOAT,
    inbound_calls INTEGER DEFAULT 0,
    outbound_calls INTEGER DEFAULT 0,
    calls_with_recordings INTEGER DEFAULT 0,
    calls_transcribed INTEGER DEFAULT 0,
    positive_sentiment_count INTEGER DEFAULT 0,
    neutral_sentiment_count INTEGER DEFAULT 0,
    negative_sentiment_count INTEGER DEFAULT 0,
    avg_urgency_score FLOAT,
    total_action_items INTEGER DEFAULT 0,
    completed_action_items INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for kpis table
CREATE INDEX idx_kpis_period ON kpis(period_type, period_start);
CREATE INDEX idx_kpis_period_start ON kpis(period_start);

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_summaries_updated_at
    BEFORE UPDATE ON call_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_action_items_updated_at
    BEFORE UPDATE ON action_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kpis_updated_at
    BEFORE UPDATE ON kpis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for call summaries with denormalized data
CREATE OR REPLACE VIEW v_call_summaries AS
SELECT
    c.id,
    c.goto_call_id,
    c.direction,
    c.caller_number,
    c.caller_name,
    c.called_number,
    c.called_name,
    c.start_time,
    c.end_time,
    c.duration_seconds,
    c.recording_url IS NOT NULL AS has_recording,
    cs.summary,
    cs.sentiment,
    cs.urgency_score,
    cs.key_topics,
    cs.transcript IS NOT NULL AS has_transcript,
    cs.transcription_completed_at,
    cs.analysis_completed_at,
    COUNT(ai.id) AS action_items_count,
    COUNT(ai.id) FILTER (WHERE ai.status = 'completed') AS completed_action_items_count,
    c.created_at
FROM calls c
LEFT JOIN call_summaries cs ON c.id = cs.call_id
LEFT JOIN action_items ai ON c.id = ai.call_id
GROUP BY c.id, cs.id;

-- Create a view for action items with call info
CREATE OR REPLACE VIEW v_action_items_with_calls AS
SELECT
    ai.id,
    ai.call_id,
    c.goto_call_id,
    c.caller_name,
    c.caller_number,
    c.start_time AS call_start_time,
    ai.description,
    ai.assigned_to,
    ai.due_date,
    ai.status,
    ai.priority,
    ai.completed_at,
    ai.created_at,
    ai.updated_at,
    CASE
        WHEN ai.due_date IS NOT NULL AND ai.due_date < CURRENT_TIMESTAMP
            AND ai.status IN ('pending', 'in_progress')
        THEN TRUE
        ELSE FALSE
    END AS is_overdue
FROM action_items ai
INNER JOIN calls c ON ai.call_id = c.id;

-- Grant permissions (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO goto_automation_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO goto_automation_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO goto_automation_readonly;

-- Insert sample data for testing (optional)
-- COMMENT OUT OR REMOVE IN PRODUCTION

/*
INSERT INTO calls (goto_call_id, direction, caller_number, caller_name, called_number, called_name, start_time, end_time, duration_seconds)
VALUES
    ('CALL-001', 'inbound', '+1-555-0100', 'John Doe', '+1-555-0200', 'Support Team', '2025-01-01 10:00:00', '2025-01-01 10:05:00', 300),
    ('CALL-002', 'outbound', '+1-555-0200', 'Support Team', '+1-555-0101', 'Jane Smith', '2025-01-01 11:00:00', '2025-01-01 11:10:00', 600);

INSERT INTO call_summaries (call_id, summary, sentiment, urgency_score, key_topics)
VALUES
    (1, 'Customer called regarding billing issue. Resolved by updating payment method.', 'positive', 3, 'billing,payment,resolution'),
    (2, 'Follow-up call to check on customer satisfaction after product delivery.', 'positive', 2, 'follow-up,satisfaction,product');

INSERT INTO action_items (call_id, description, status, priority)
VALUES
    (1, 'Send confirmation email for updated payment method', 'completed', 4),
    (2, 'Schedule follow-up call in 2 weeks', 'pending', 2);
*/

-- Comments on tables for documentation
COMMENT ON TABLE calls IS 'Stores call records received from GoTo Connect webhooks';
COMMENT ON TABLE call_summaries IS 'Stores AI-generated transcripts and summaries for calls';
COMMENT ON TABLE action_items IS 'Stores action items extracted from call analysis';
COMMENT ON TABLE kpis IS 'Stores aggregated KPI metrics for different time periods';

COMMENT ON COLUMN calls.goto_call_id IS 'Unique identifier from GoTo Connect';
COMMENT ON COLUMN call_summaries.urgency_score IS 'AI-assigned urgency score from 1 (low) to 5 (critical)';
COMMENT ON COLUMN action_items.priority IS 'Priority level from 1 (low) to 5 (critical)';

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial schema with calls, summaries, action items, and KPIs');

-- Success message
SELECT 'GoTo Call Automation Database Schema Created Successfully!' AS status;
