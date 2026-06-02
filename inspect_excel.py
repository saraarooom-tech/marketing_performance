import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "data" / "qualification_details.xlsx"

if not EXCEL_PATH.exists():
    raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

xls = pd.ExcelFile(EXCEL_PATH)

print("Sheets found:")
print(xls.sheet_names)

sheet_name = "notqualified"

if sheet_name not in xls.sheet_names:
    print(f"\nSheet '{sheet_name}' not found.")
    print("Reading first sheet instead...")
    sheet_name = xls.sheet_names[0]

df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)

df.columns = df.columns.astype(str).str.strip()

print(f"\nReading sheet: {sheet_name}")

print("\nColumns:")
for i, col in enumerate(df.columns, start=1):
    print(f"{i}. {col}")

print("\nFirst 5 rows:")
print(df.head())

print("\nShape:")
print(df.shape)