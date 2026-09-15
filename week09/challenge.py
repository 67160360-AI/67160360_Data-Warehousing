"""
Challenge Task Script:
ก. Analyze extended.db: Top 3 stores & monthly AOV vs overall AOV
ข. Create challenge.db, insert new records with FK check, and generate new Pivot Table
"""
from pathlib import Path
import sys, sqlite3, shutil
import pandas as pd

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'

print('=== Challenge ก: Analysis on extended.db ===')
con_ext = sqlite3.connect(DATA / 'extended.db')

# 1. Top 3 Stores
top3 = con_ext.execute('''
    SELECT s.store_name, s.province, SUM(f.quantity * f.unit_price) AS total_revenue
    FROM fact_sales f
    JOIN dim_store s ON f.store_key = s.store_key
    GROUP BY s.store_name, s.province
    ORDER BY total_revenue DESC
    LIMIT 3;
''').fetchall()
print('Top 3 Stores by Revenue:')
for rank, row in enumerate(top3, 1):
    print(f'  {rank}. {row[0]} ({row[1]}): {row[2]:,} THB')

# 2. Monthly AOV vs Overall AOV
monthly = con_ext.execute('''
    SELECT d.month, 
           SUM(f.quantity * f.unit_price) AS revenue,
           COUNT(DISTINCT f.order_id) AS orders,
           ROUND(1.0 * SUM(f.quantity * f.unit_price) / COUNT(DISTINCT f.order_id), 2) AS monthly_aov
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.month
    ORDER BY d.month;
''').fetchall()

print('\nMonthly Revenue and AOV:')
aov_list = []
for m, rev, ords, aov in monthly:
    print(f'  Month {m}: Revenue={rev:,} THB | Orders={ords:,} | AOV={aov:.2f} THB/order')
    aov_list.append(aov)

overall = con_ext.execute('''
    SELECT SUM(f.quantity * f.unit_price) AS revenue,
           COUNT(DISTINCT f.order_id) AS orders,
           ROUND(1.0 * SUM(f.quantity * f.unit_price) / COUNT(DISTINCT f.order_id), 2) AS overall_aov
    FROM fact_sales f;
''').fetchone()

simple_avg_aov = sum(aov_list) / len(aov_list)
print(f'\nComparison:')
print(f'  Average of Monthly AOVs: {simple_avg_aov:.2f} THB')
print(f'  True Overall AOV:        {overall[2]:.2f} THB (Total Rev: {overall[0]:,} / Orders: {overall[1]:,})')
print('  Explanation: Average of monthly AOVs treats every month equally, ignoring the differences in order volume per month.')
con_ext.close()

print('\n' + '='*50)
print('=== Challenge ข: challenge.db & New Pivot ===')

challenge_db = DATA / 'challenge.db'
shutil.copy(DATA / 'warehouse.db', challenge_db)

with sqlite3.connect(challenge_db) as con_ch:
    con_ch.execute('PRAGMA foreign_keys = ON;')
    
    # Insert dim_date for 2026-10-01
    con_ch.execute("INSERT INTO dim_date VALUES (20261001, '2026-10-01', 2026, '2026-10')")
    
    # Insert new orders:
    # O1007 line 1: Tea (pk=1) 3 pcs @ 50 at Bangsaen (sk=1)
    # O1007 line 2: Cookie (pk=2) 2 pcs @ 80 at Bangsaen (sk=1)
    # O1008 line 1: Tea (pk=1) 4 pcs @ 50 at Siam (sk=2)
    new_rows = [
        ('O1007', 1, 20261001, 1, 1, 3, 50),
        ('O1007', 2, 20261001, 2, 1, 2, 80),
        ('O1008', 1, 20261001, 1, 2, 4, 50)
    ]
    con_ch.executemany('INSERT INTO fact_sales VALUES (?,?,?,?,?,?,?)', new_rows)
    con_ch.commit()
    
    # Check FK
    fk_errors = con_ch.execute('PRAGMA foreign_key_check').fetchall()
    assert not fk_errors, f'FK errors found: {fk_errors}'
    print('Foreign key check passed: No errors.')
    
    # Compare before and after JOIN
    check = con_ch.execute('''
        SELECT 
            (SELECT COUNT(*) FROM fact_sales) AS fact_rows,
            (SELECT COUNT(*) FROM sales) AS view_rows,
            (SELECT COUNT(DISTINCT order_id) FROM fact_sales) AS fact_orders,
            (SELECT COUNT(DISTINCT order_id) FROM sales) AS view_orders,
            (SELECT SUM(quantity * unit_price) FROM fact_sales) AS fact_revenue,
            (SELECT SUM(amount) FROM sales) AS view_revenue;
    ''').fetchone()
    print(f'Verification: Fact Rows={check[0]}, View Rows={check[1]} | Orders={check[2]} | Total Revenue={check[4]:,} THB')
    
    # Create new Pivot Table
    df_ch = pd.read_sql_query('SELECT * FROM sales', con_ch)
    pivot_ch = df_ch.pivot_table(
        index='province',
        columns='month',
        values='amount',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Total'
    )
    print('\nNew Pivot Table (challenge.db with October):')
    print(pivot_ch)
    pivot_ch.to_csv(ROOT / 'pivot_challenge.csv')
    print('\nExported pivot_challenge.csv successfully.')
