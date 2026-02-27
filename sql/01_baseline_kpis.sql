-- Roku Patch Stability Analytics
-- Baseline KPIs and Analytics Queries
-- For firmware error rate analysis and stability monitoring

-- ============================================
-- 1. Executive Summary KPIs
-- ============================================
SELECT
    COUNT(DISTINCT firmware_version) AS total_firmware_versions,
    COUNT(DISTINCT device_id) AS total_devices,
    COUNT(*) AS total_error_events,
    COUNT(DISTINCT error_code) AS unique_error_codes,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT device_id), 2) AS errors_per_device
FROM device_events;


-- ============================================
-- 2. Error Rate by Firmware Version
-- ============================================
SELECT
    de.firmware_version,
    fr.release_date,
    COUNT(DISTINCT de.device_id) AS affected_devices,
    COUNT(*) AS total_errors,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT de.device_id), 2) AS error_rate_per_device,
    COUNT(DISTINCT de.error_code) AS unique_errors
FROM device_events de
LEFT JOIN firmware_releases fr ON de.firmware_version = fr.firmware_version
GROUP BY de.firmware_version, fr.release_date
ORDER BY fr.release_date DESC;


-- ============================================
-- 3. High-Risk Firmware Detection
-- Versions with error rates above average
-- ============================================
WITH version_stats AS (
    SELECT
        firmware_version,
        COUNT(*) AS error_count,
        COUNT(DISTINCT device_id) AS device_count,
        COUNT(*) * 1.0 / COUNT(DISTINCT device_id) AS error_rate
    FROM device_events
    GROUP BY firmware_version
),
avg_rate AS (
    SELECT AVG(error_rate) AS avg_error_rate FROM version_stats
)
SELECT
    vs.firmware_version,
    vs.error_count,
    vs.device_count,
    ROUND(vs.error_rate, 3) AS error_rate,
    ROUND(ar.avg_error_rate, 3) AS baseline_avg,
    ROUND(vs.error_rate / ar.avg_error_rate, 2) AS risk_multiplier,
    CASE
        WHEN vs.error_rate > ar.avg_error_rate * 1.5 THEN 'HIGH RISK'
        WHEN vs.error_rate > ar.avg_error_rate THEN 'MODERATE'
        ELSE 'LOW'
    END AS risk_tier
FROM version_stats vs
CROSS JOIN avg_rate ar
ORDER BY vs.error_rate DESC;


-- ============================================
-- 4. Error Code Analysis
-- ============================================
SELECT
    error_code,
    COUNT(*) AS occurrence_count,
    COUNT(DISTINCT device_id) AS affected_devices,
    COUNT(DISTINCT firmware_version) AS firmware_versions_affected,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM device_events), 1) AS pct_of_all_errors
FROM device_events
GROUP BY error_code
ORDER BY occurrence_count DESC
LIMIT 20;


-- ============================================
-- 5. Support Ticket Analysis
-- ============================================
SELECT
    error_code,
    COUNT(*) AS ticket_count,
    ROUND(AVG(tier), 2) AS avg_tier,
    SUM(rma_issued) AS total_rmas,
    ROUND(100.0 * SUM(rma_issued) / COUNT(*), 1) AS rma_rate_pct
FROM support_tickets
GROUP BY error_code
ORDER BY ticket_count DESC;


-- ============================================
-- 6. RMA Rate by Firmware Version
-- Warranty returns indicate severity
-- ============================================
SELECT
    de.firmware_version,
    COUNT(DISTINCT st.ticket_id) AS support_tickets,
    SUM(st.rma_issued) AS rma_count,
    ROUND(100.0 * SUM(st.rma_issued) / COUNT(DISTINCT st.ticket_id), 1) AS rma_rate_pct
FROM device_events de
JOIN support_tickets st
    ON de.device_id = st.device_id
    AND de.error_code = st.error_code
GROUP BY de.firmware_version
HAVING COUNT(DISTINCT st.ticket_id) >= 5  -- Minimum sample
ORDER BY rma_rate_pct DESC;


-- ============================================
-- 7. Error Trend by Week (Time Series)
-- ============================================
SELECT
    strftime('%Y-%W', timestamp) AS year_week,
    COUNT(*) AS error_count,
    COUNT(DISTINCT device_id) AS unique_devices,
    COUNT(DISTINCT firmware_version) AS active_versions
FROM device_events
GROUP BY strftime('%Y-%W', timestamp)
ORDER BY year_week;


-- ============================================
-- 8. Device Model Analysis
-- ============================================
SELECT
    model,
    COUNT(DISTINCT device_id) AS device_count,
    COUNT(*) AS total_errors,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT device_id), 2) AS errors_per_device,
    COUNT(DISTINCT error_code) AS unique_error_types
FROM device_events
GROUP BY model
ORDER BY errors_per_device DESC;


-- ============================================
-- 9. Regional Analysis
-- ============================================
SELECT
    region,
    COUNT(DISTINCT device_id) AS device_count,
    COUNT(*) AS total_errors,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT device_id), 2) AS errors_per_device,
    COUNT(DISTINCT firmware_version) AS firmware_versions
FROM device_events
GROUP BY region
ORDER BY errors_per_device DESC;


-- ============================================
-- 10. Error Co-occurrence (Same Device)
-- Find errors that frequently appear together
-- ============================================
SELECT
    de1.error_code AS error_1,
    de2.error_code AS error_2,
    COUNT(DISTINCT de1.device_id) AS devices_with_both,
    ROUND(100.0 * COUNT(DISTINCT de1.device_id) /
          (SELECT COUNT(DISTINCT device_id) FROM device_events), 1) AS pct_of_devices
FROM device_events de1
JOIN device_events de2
    ON de1.device_id = de2.device_id
    AND de1.error_code < de2.error_code
GROUP BY de1.error_code, de2.error_code
HAVING COUNT(DISTINCT de1.device_id) >= 5
ORDER BY devices_with_both DESC
LIMIT 15;


-- ============================================
-- 11. Firmware Version Regression Detection
-- Compare consecutive versions
-- ============================================
WITH version_errors AS (
    SELECT
        firmware_version,
        COUNT(*) * 1.0 / COUNT(DISTINCT device_id) AS error_rate
    FROM device_events
    GROUP BY firmware_version
),
version_sequence AS (
    SELECT
        v1.firmware_version AS current_version,
        v2.firmware_version AS previous_version,
        v1.error_rate AS current_rate,
        v2.error_rate AS previous_rate
    FROM version_errors v1
    JOIN version_errors v2
    WHERE v1.firmware_version > v2.firmware_version
)
SELECT
    current_version,
    previous_version,
    ROUND(current_rate, 3) AS current_error_rate,
    ROUND(previous_rate, 3) AS previous_error_rate,
    ROUND(current_rate - previous_rate, 3) AS rate_change,
    CASE
        WHEN current_rate > previous_rate * 1.2 THEN 'REGRESSION'
        WHEN current_rate < previous_rate * 0.8 THEN 'IMPROVEMENT'
        ELSE 'STABLE'
    END AS status
FROM version_sequence
WHERE ABS(current_rate - previous_rate) > 0.1
ORDER BY rate_change DESC;


-- ============================================
-- 12. Support Escalation Analysis
-- Tier distribution by error type
-- ============================================
SELECT
    error_code,
    SUM(CASE WHEN tier = 1 THEN 1 ELSE 0 END) AS tier_1,
    SUM(CASE WHEN tier = 2 THEN 1 ELSE 0 END) AS tier_2,
    SUM(CASE WHEN tier = 3 THEN 1 ELSE 0 END) AS tier_3,
    COUNT(*) AS total_tickets,
    ROUND(100.0 * SUM(CASE WHEN tier >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS escalation_rate_pct
FROM support_tickets
GROUP BY error_code
HAVING COUNT(*) >= 5
ORDER BY escalation_rate_pct DESC;


-- ============================================
-- 13. Firmware Release Health Score
-- Composite metric for release quality
-- ============================================
WITH fw_metrics AS (
    SELECT
        de.firmware_version,
        COUNT(*) * 1.0 / COUNT(DISTINCT de.device_id) AS error_rate,
        COALESCE(SUM(st.rma_issued) * 1.0 / NULLIF(COUNT(st.ticket_id), 0), 0) AS rma_rate,
        COALESCE(AVG(st.tier), 1) AS avg_support_tier
    FROM device_events de
    LEFT JOIN support_tickets st
        ON de.device_id = st.device_id
        AND de.error_code = st.error_code
    GROUP BY de.firmware_version
)
SELECT
    firmware_version,
    ROUND(error_rate, 3) AS error_rate,
    ROUND(rma_rate, 3) AS rma_rate,
    ROUND(avg_support_tier, 2) AS avg_support_tier,
    -- Health score: lower is better (normalized 0-100)
    ROUND(
        100 - (
            (error_rate * 30) +
            (rma_rate * 40) +
            ((avg_support_tier - 1) / 2 * 30)
        ),
        1
    ) AS health_score
FROM fw_metrics
ORDER BY health_score DESC;
