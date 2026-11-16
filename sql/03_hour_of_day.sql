-- Typical daily pattern: average by hour of day
SELECT
    CAST(strftime('%H', observed_at) AS INTEGER) AS hour,
    ROUND(AVG(pm2_5), 1)         AS avg_pm2_5,
    ROUND(AVG(pm10), 1)          AS avg_pm10,
    ROUND(AVG(wind_kmh), 1)      AS avg_wind_kmh,
    ROUND(AVG(temperature_c), 1) AS avg_temp_c
FROM hourly_readings
WHERE is_forecast = 0
GROUP BY hour
ORDER BY hour;
