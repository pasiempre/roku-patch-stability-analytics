-- Drop tables if they exist (for repeatable setup)
DROP TABLE IF EXISTS device_events;
DROP TABLE IF EXISTS firmware_releases;
DROP TABLE IF EXISTS support_tickets;

-- device_events: synthetic Roku device error telemetry
CREATE TABLE device_events (
    event_id          INTEGER PRIMARY KEY,
    device_id         TEXT NOT NULL,
    error_code        TEXT NOT NULL,
    timestamp         TEXT NOT NULL,      -- ISO8601 datetime string
    firmware_version  TEXT NOT NULL,
    model             TEXT NOT NULL,
    region            TEXT NOT NULL
);

-- firmware_releases: firmware version timeline & notes
CREATE TABLE firmware_releases (
    firmware_version  TEXT PRIMARY KEY,
    release_date      TEXT NOT NULL,      -- ISO8601 datetime string
    notes             TEXT
);

-- support_tickets: support contacts tied to device errors
CREATE TABLE support_tickets (
    ticket_id     INTEGER PRIMARY KEY,
    device_id     TEXT NOT NULL,
    error_code    TEXT NOT NULL,
    created_at    TEXT NOT NULL,          -- ISO8601 datetime string
    tier          INTEGER NOT NULL,
    resolution    TEXT NOT NULL,
    rma_issued    INTEGER NOT NULL        -- 0 = no RMA, 1 = RMA issued
);

-- Helpful indexes for analytics performance
CREATE INDEX idx_device_events_fw      ON device_events (firmware_version);
CREATE INDEX idx_device_events_device  ON device_events (device_id);
CREATE INDEX idx_device_events_ts      ON device_events (timestamp);

CREATE INDEX idx_support_device        ON support_tickets (device_id);
CREATE INDEX idx_support_error         ON support_tickets (error_code);
CREATE INDEX idx_support_rma           ON support_tickets (rma_issued);

CREATE INDEX idx_firmware_release_date ON firmware_releases (release_date);