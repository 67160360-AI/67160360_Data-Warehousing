-- q09.sql: UNION ALL แสดงยอดรายเดือนและแถว ALL
SELECT month, SUM(amount) AS revenue
FROM sales
GROUP BY month
UNION ALL
SELECT 'ALL' AS month, SUM(amount) AS revenue
FROM sales;
