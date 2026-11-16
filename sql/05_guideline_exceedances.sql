-- Days above the WHO 24-hour guideline values (PM2.5: 15, PM10: 45 ug/m3)
-- Only (nearly) complete days are counted
SELECT
    DATE(observed_at)     AS day,
    ROUND(AVG(pm2_5), 1)  AS avg_pm2_5,
    ROUND(AVG(pm10), 1)   AS avg_pm10,
    COUNT(*)              AS hours
FROM hourly_readings
WHERE is_forecast = 0
GROUP BY DATE(observed_at)
HAVING COUNT(*) >= 20
   AND (AVG(pm2_5) > 15 OR AVG(pm10) > 45)
ORDER BY day DESC;
