-- Daily averages, last 30 days
SELECT
    DATE(observed_at)            AS day,
    ROUND(AVG(pm2_5), 1)         AS avg_pm2_5,
    ROUND(MAX(pm2_5), 1)         AS max_pm2_5,
    ROUND(AVG(pm10), 1)          AS avg_pm10,
    ROUND(AVG(temperature_c), 1) AS avg_temp_c,
    ROUND(AVG(humidity_pct), 0)  AS avg_humidity_pct,
    ROUND(AVG(wind_kmh), 1)      AS avg_wind_kmh,
    COUNT(*)                     AS hours
FROM hourly_readings
WHERE is_forecast = 0
GROUP BY DATE(observed_at)
ORDER BY day DESC
LIMIT 30;
