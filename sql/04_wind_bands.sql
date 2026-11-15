-- Does wind clear the air? Pollution by wind-speed band
SELECT
    CASE
        WHEN wind_kmh < 5  THEN '1. calm (<5 km/h)'
        WHEN wind_kmh < 10 THEN '2. light (5-10)'
        WHEN wind_kmh < 20 THEN '3. moderate (10-20)'
        ELSE                    '4. strong (20+)'
    END AS wind_band,
    COUNT(*)                AS hours,
    ROUND(AVG(pm2_5), 1)    AS avg_pm2_5,
    ROUND(AVG(pm10), 1)     AS avg_pm10
FROM hourly_readings
WHERE is_forecast = 0 AND wind_kmh IS NOT NULL
GROUP BY wind_band
ORDER BY wind_band;