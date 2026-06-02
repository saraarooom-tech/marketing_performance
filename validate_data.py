import pandas as pd
from pathlib import Path

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

CURRENT_PATH = DATA_DIR / "current_week.csv"
PREVIOUS_PATH = DATA_DIR / "previous_week.csv"

# =========================
# Required columns
# =========================
REQUIRED_COLUMNS = [
    "attribution_title",
    "request",
    "qualified request",
    "OTP verified QR",
    "Reserve Request",
    "Reserve",
    "Entrance",
    "Buy",
    "revenue",
    "Otp/QR",
    "Reserve/OTP",
    "Entrance/Reserve",
    "Buy/OTP verified",
]

ADDITIVE_COLUMNS = [
    "request",
    "qualified request",
    "OTP verified QR",
    "Reserve Request",
    "Reserve",
    "Entrance",
    "Buy",
    "revenue",
]

RATE_COLUMNS = [
    "Otp/QR",
    "Reserve/OTP",
    "Entrance/Reserve",
    "Buy/OTP verified",
]


# =========================
# Helpers
# =========================
def read_csv_safely(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin1")

    df.columns = df.columns.str.strip()

    if "attribution_title" in df.columns:
        df["attribution_title"] = (
            df["attribution_title"]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )

    for col in REQUIRED_COLUMNS:
        if col in df.columns and col != "attribution_title":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def format_number(value):
    try:
        value = float(value)
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    except:
        return str(value)


def format_percent(value):
    try:
        return f"{float(value):.2f}%"
    except:
        return str(value)


def check_columns(df, name):
    print(f"\n==============================")
    print(f"Checking columns: {name}")
    print(f"==============================")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    extra = [col for col in df.columns if col not in REQUIRED_COLUMNS]

    if missing:
        print("❌ Missing columns:")
        for col in missing:
            print(f"   - {col}")
    else:
        print("✅ No missing required columns.")

    if extra:
        print("⚠️ Extra columns found:")
        for col in extra:
            print(f"   - {col}")
    else:
        print("✅ No extra columns.")

    return len(missing) == 0


def get_detail_and_total(df):
    is_total = df["attribution_title"].str.lower() == "total"
    total_row = df[is_total].copy()
    detail_df = df[~is_total].copy()

    calculated_total = detail_df[ADDITIVE_COLUMNS].sum(numeric_only=True)

    return detail_df, total_row, calculated_total


def check_total(df, name):
    print(f"\n==============================")
    print(f"Checking Total row: {name}")
    print(f"==============================")

    detail_df, total_row, calculated_total = get_detail_and_total(df)

    print(f"Rows including Total: {len(df)}")
    print(f"Rows excluding Total: {len(detail_df)}")

    if total_row.empty:
        print("⚠️ No Total row found.")
        print("The report will calculate totals from detail rows.")
        return True

    manual_total = total_row.iloc[0]

    has_issue = False

    print("\nManual Total vs Calculated Total:")

    for col in ADDITIVE_COLUMNS:
        manual_value = float(manual_total[col])
        calculated_value = float(calculated_total[col])
        diff = manual_value - calculated_value

        status = "✅"
        if abs(diff) > 0.01:
            status = "❌"
            has_issue = True

        print(
            f"{status} {col}: "
            f"manual={format_number(manual_value)} | "
            f"calculated={format_number(calculated_value)} | "
            f"diff={format_number(diff)}"
        )

    if has_issue:
        print("\n❌ Total row has mismatch.")
        print("Recommendation: Use calculated totals from detail rows in report.")
    else:
        print("\n✅ Total row matches detail rows.")

    return not has_issue


def check_duplicate_attributions(df, name):
    print(f"\n==============================")
    print(f"Checking duplicate attribution_title: {name}")
    print(f"==============================")

    detail_df, _, _ = get_detail_and_total(df)

    duplicates = detail_df[
        detail_df["attribution_title"].duplicated(keep=False)
    ]["attribution_title"].unique()

    if len(duplicates) == 0:
        print("✅ No duplicate attribution_title found.")
        return True

    print("⚠️ Duplicate attribution_title found:")
    for item in duplicates:
        print(f"   - {item}")

    print("This may be okay, but for comparison accuracy it is better to aggregate duplicates.")
    return False


def calculated_rates(total):
    request = float(total.get("request", 0))
    qualified = float(total.get("qualified request", 0))
    otp = float(total.get("OTP verified QR", 0))
    reserve = float(total.get("Reserve", 0))
    entrance = float(total.get("Entrance", 0))
    buy = float(total.get("Buy", 0))

    return {
        "Otp/QR": (otp / qualified * 100) if qualified else 0,
        "Reserve/OTP": (reserve / otp * 100) if otp else 0,
        "Entrance/Reserve": (entrance / reserve * 100) if reserve else 0,
        "Buy/OTP verified": (buy / otp * 100) if otp else 0,
    }


def compare_weekly_totals(current_df, previous_df):
    print(f"\n==============================")
    print("Weekly Total Comparison")
    print(f"==============================")

    current_detail, _, current_total = get_detail_and_total(current_df)
    previous_detail, _, previous_total = get_detail_and_total(previous_df)

    print("\nMetric | Current | Previous | Change | Change %")
    print("-" * 80)

    for col in ADDITIVE_COLUMNS:
        current_value = float(current_total[col])
        previous_value = float(previous_total[col])
        change = current_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value else 0

        arrow = "▲" if change > 0 else "▼" if change < 0 else "-"

        print(
            f"{col} | "
            f"{format_number(current_value)} | "
            f"{format_number(previous_value)} | "
            f"{arrow} {format_number(change)} | "
            f"{format_percent(change_pct)}"
        )

    print("\nCalculated conversion rates for Current Week:")
    current_rates = calculated_rates(current_total)
    for key, value in current_rates.items():
        print(f"   {key}: {format_percent(value)}")

    print("\nCalculated conversion rates for Previous Week:")
    previous_rates = calculated_rates(previous_total)
    for key, value in previous_rates.items():
        print(f"   {key}: {format_percent(value)}")


def check_attribution_match(current_df, previous_df):
    print(f"\n==============================")
    print("Checking attribution_title matching")
    print(f"==============================")

    current_detail, _, _ = get_detail_and_total(current_df)
    previous_detail, _, _ = get_detail_and_total(previous_df)

    current_titles = set(current_detail["attribution_title"])
    previous_titles = set(previous_detail["attribution_title"])

    only_current = sorted(current_titles - previous_titles)
    only_previous = sorted(previous_titles - current_titles)

    print(f"Current week attribution count: {len(current_titles)}")
    print(f"Previous week attribution count: {len(previous_titles)}")

    if only_current:
        print("\n⚠️ Titles only in current week:")
        for title in only_current[:20]:
            print(f"   - {title}")
        if len(only_current) > 20:
            print(f"   ... and {len(only_current) - 20} more")

    if only_previous:
        print("\n⚠️ Titles only in previous week:")
        for title in only_previous[:20]:
            print(f"   - {title}")
        if len(only_previous) > 20:
            print(f"   ... and {len(only_previous) - 20} more")

    if not only_current and not only_previous:
        print("✅ Attribution titles match between weeks.")


# =========================
# Main
# =========================
print("Starting data validation...")

current_df = read_csv_safely(CURRENT_PATH)
previous_df = read_csv_safely(PREVIOUS_PATH)

current_columns_ok = check_columns(current_df, "current_week.csv")
previous_columns_ok = check_columns(previous_df, "previous_week.csv")

print(f"\n==============================")
print("Comparing columns between files")
print(f"==============================")

if list(current_df.columns) == list(previous_df.columns):
    print("✅ Column order and names are exactly the same.")
else:
    print("⚠️ Column order or names are different.")
    print("\nCurrent columns:")
    print(list(current_df.columns))
    print("\nPrevious columns:")
    print(list(previous_df.columns))

check_total(current_df, "current_week.csv")
check_total(previous_df, "previous_week.csv")

check_duplicate_attributions(current_df, "current_week.csv")
check_duplicate_attributions(previous_df, "previous_week.csv")

check_attribution_match(current_df, previous_df)

compare_weekly_totals(current_df, previous_df)

print("\n==============================")
print("Validation finished.")
print("==============================")