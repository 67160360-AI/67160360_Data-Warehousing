from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
with sqlite3.connect((ROOT / 'data' / 'warehouse.db').as_uri() + '?mode=ro', uri=True) as con:
    df = pd.read_sql_query('SELECT * FROM sales', con)

print('=== Raw Sales Data Head ===')
print(df.head())

# P1: province x month, sum(amount), fill_value=0, margins=True, margins_name='Total'
p1 = df.pivot_table(
    index='province',
    columns='month',
    values='amount',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Total'
)
print('\n=== P1: Pivot Table (Province x Month) ===')
print(p1)
p1.to_csv(ROOT / 'pivot_province_month.csv')

# P2: filter September, then category x province, sum(amount)
df_sep = df[df['month'] == '2026-09']
p2 = df_sep.pivot_table(
    index='category',
    columns='province',
    values='amount',
    aggfunc='sum',
    fill_value=0
)
print('\n=== P2: Pivot Table (September: Category x Province) ===')
print(p2)
p2.to_csv(ROOT / 'pivot_september.csv')

# P3: assert that the pivot grand total equals df['amount'].sum()
grand_total = p1.loc['Total', 'Total']
expected_total = df['amount'].sum()
assert grand_total == expected_total, f"Grand total mismatch: {grand_total} != {expected_total}"
print(f"\n[Assert Success] Grand Total ({grand_total}) == df['amount'].sum() ({expected_total})")

print('\nExported pivot_province_month.csv and pivot_september.csv successfully.')
