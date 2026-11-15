-- Data coverage and missing values (observed hours only)
SELECT
    COUNT(*)                           AS hours,
    MIN(observed_at)                   AS first_hour,
    MAX(observed_at)                   AS last_hour,
    COUNT(DISTINCT DATE(observed_at))  AS days,
    SUM(pm2_5 IS NULL)                 AS missing_pm2_5,
    SUM(pm10 IS NULL)                  AS missing_pm10,
    SUM(temperature_c IS NULL)         AS missing_temp
FROM hourly_readings
WHERE is_forecast = 0;