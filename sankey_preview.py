import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
import webbrowser
import plotly.graph_objects as go

# =========================
# Config
# =========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

EXCEL_PATH = DATA_DIR / "qualification_details.xlsx"
SHEET_NAME = "notqualified"

OUTPUT_HTML = BASE_DIR / "sankey_preview.html"

# اگر reason ها زیاد شدند، برای هر Drop-off فقط Top N نمایش بده
# اگر خواستی همه reason ها بیاد، این عدد رو بزرگ‌تر کن مثلا 50
TOP_REASONS_PER_DROPOFF = 12


# =========================
# Helpers
# =========================
def normalize_digits(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"

    translation_table = {}

    for p, e in zip(persian_digits, english_digits):
        translation_table[ord(p)] = e

    for a, e in zip(arabic_digits, english_digits):
        translation_table[ord(a)] = e

    return text.translate(translation_table).strip()


def as_binary(value):
    """
    تبدیل مقدارهای مختلف به 0/1
    ساپورت می‌کند:
    1, 0, True, False, TRUE, FALSE, ۱, ۰
    """
    if pd.isna(value):
        return 0

    if isinstance(value, bool):
        return 1 if value else 0

    text = normalize_digits(value).lower()

    if text in ["true", "yes", "y"]:
        return 1

    if text in ["false", "no", "n", ""]:
        return 0

    try:
        number = float(text)
        return 1 if number > 0 else 0
    except:
        return 0


def clean_reason(value):
    if pd.isna(value):
        return "No reason"

    text = str(value).strip()

    if text == "" or text.lower() in ["nan", "none", "null"]:
        return "No reason"

    return text


def add_link(link_counts, source, target, value=1):
    link_counts[(source, target)] += value


def get_node_index(label, node_index, labels):
    if label not in node_index:
        node_index[label] = len(labels)
        labels.append(label)

    return node_index[label]


def node_color(label):
    positive_nodes = [
        "Request",
        "Qualified Request",
        "OTP Verified QR",
        "Reserve",
        "Conf Entrance",
        "Entrance",
        "Inspection",
        "Auction",
        "Buy",
    ]

    drop_nodes = [
        "Not Qualified",
        "OTP Not Verified",
        "Not Reserved",
        "No Conf Entrance",
        "No Entrance",
        "No Inspection",
        "No Auction",
        "No Buy",
    ]

    if label in positive_nodes:
        if label == "Buy":
            return "rgba(0, 255, 132, 0.85)"
        return "rgba(255, 122, 0, 0.85)"

    if label in drop_nodes:
        return "rgba(255, 176, 131, 0.85)"

    # reason nodes
    return "rgba(110, 116, 133, 0.75)"


def link_color(source, target):
    if source.startswith("No ") or source.startswith("Not ") or target.startswith("No ") or target.startswith("Not "):
        return "rgba(255, 176, 131, 0.35)"

    if "Reason" in target:
        return "rgba(255, 176, 131, 0.28)"

    return "rgba(255, 122, 0, 0.35)"


# =========================
# Read Excel
# =========================
if not EXCEL_PATH.exists():
    raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

xls = pd.ExcelFile(EXCEL_PATH)

if SHEET_NAME in xls.sheet_names:
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
else:
    print(f"Sheet '{SHEET_NAME}' not found. Reading first sheet instead.")
    df = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[0])

df.columns = df.columns.astype(str).str.strip().str.lower()

required_columns = [
    "notqualified",
    "reason",
    "otp_verified",
    "reserve",
    "confentrance",
    "entrance",
    "inspection",
    "auction",
    "buy",
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    raise ValueError(f"Missing columns in Excel: {missing_columns}")

# Clean needed columns
df["reason"] = df["reason"].apply(clean_reason)

for col in [
    "notqualified",
    "otp_verified",
    "reserve",
    "confentrance",
    "entrance",
    "inspection",
    "auction",
    "buy",
]:
    df[col] = df[col].apply(as_binary)


# =========================
# Build Sankey Logic
# =========================
link_counts = defaultdict(int)
reason_events = defaultdict(Counter)

total_requests = len(df)

# مراحل مثبت بعد از Qualified
TRANSITIONS = [
    {
        "from": "Qualified Request",
        "to": "OTP Verified QR",
        "column": "otp_verified",
        "drop": "OTP Not Verified",
    },
    {
        "from": "OTP Verified QR",
        "to": "Reserve",
        "column": "reserve",
        "drop": "Not Reserved",
    },
    {
        "from": "Reserve",
        "to": "Conf Entrance",
        "column": "confentrance",
        "drop": "No Conf Entrance",
    },
    {
        "from": "Conf Entrance",
        "to": "Entrance",
        "column": "entrance",
        "drop": "No Entrance",
    },
    {
        "from": "Entrance",
        "to": "Inspection",
        "column": "inspection",
        "drop": "No Inspection",
    },
    {
        "from": "Inspection",
        "to": "Auction",
        "column": "auction",
        "drop": "No Auction",
    },
    {
        "from": "Auction",
        "to": "Buy",
        "column": "buy",
        "drop": "No Buy",
    },
]

for _, row in df.iterrows():
    reason = clean_reason(row["reason"])

    # مسیر Not Qualified
    if row["notqualified"] == 1:
        add_link(link_counts, "Request", "Not Qualified", 1)
        reason_events["Not Qualified"][reason] += 1
        continue

    # مسیر Qualified
    add_link(link_counts, "Request", "Qualified Request", 1)

    current_stage = "Qualified Request"

    for transition in TRANSITIONS:
        expected_from = transition["from"]
        next_stage = transition["to"]
        column = transition["column"]
        drop_stage = transition["drop"]

        # اگر مرحله جاری با from یکی نیست، ادامه نده
        if current_stage != expected_from:
            break

        if row[column] == 1:
            add_link(link_counts, current_stage, next_stage, 1)
            current_stage = next_stage
        else:
            add_link(link_counts, current_stage, drop_stage, 1)
            reason_events[drop_stage][reason] += 1
            break


# =========================
# Add Reason Links
# =========================
for drop_stage, counter in reason_events.items():
    most_common = counter.most_common(TOP_REASONS_PER_DROPOFF)

    shown_reasons = set()

    for reason, count in most_common:
        reason_label = f"{drop_stage} Reason: {reason}"
        add_link(link_counts, drop_stage, reason_label, count)
        shown_reasons.add(reason)

    others_count = sum(
        count for reason, count in counter.items()
        if reason not in shown_reasons
    )

    if others_count > 0:
        reason_label = f"{drop_stage} Reason: Others"
        add_link(link_counts, drop_stage, reason_label, others_count)


# =========================
# Convert to Plotly Nodes/Links
# =========================
labels = []
node_index = {}

sources = []
targets = []
values = []
colors = []

for (source, target), value in link_counts.items():
    source_index = get_node_index(source, node_index, labels)
    target_index = get_node_index(target, node_index, labels)

    sources.append(source_index)
    targets.append(target_index)
    values.append(value)
    colors.append(link_color(source, target))

node_colors = [node_color(label) for label in labels]

fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=20,
                thickness=20,
                line=dict(color="rgba(255,255,255,0.15)", width=1),
                label=labels,
                color=node_colors,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=colors,
            ),
        )
    ]
)

fig.update_layout(
    title=dict(
        text="Sankey Funnel - Request to Buy with Drop-off Reasons",
        font=dict(size=22, color="#FFFFFF"),
    ),
    font=dict(size=12, color="#FFFFFF"),
    paper_bgcolor="#151515",
    plot_bgcolor="#151515",
    height=760,
    margin=dict(l=20, r=20, t=70, b=20),
)


# =========================
# Reason Breakdown Table
# =========================
reason_rows = []

for drop_stage, counter in reason_events.items():
    total_drop = sum(counter.values())

    for reason, count in counter.most_common():
        share = (count / total_drop * 100) if total_drop else 0

        reason_rows.append({
            "Drop-off Stage": drop_stage,
            "Reason": reason,
            "Count": count,
            "Share %": share,
        })

reason_df = pd.DataFrame(reason_rows)

if not reason_df.empty:
    reason_table_html = reason_df.to_html(
        index=False,
        classes="reason-table",
        border=0,
        formatters={
            "Count": lambda x: f"{int(x):,}",
            "Share %": lambda x: f"{x:.1f}%",
        },
    )
else:
    reason_table_html = "<p>No reason data found.</p>"


# =========================
# Build Preview HTML
# =========================
chart_html = fig.to_html(
    full_html=False,
    include_plotlyjs="cdn",
)

html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sankey Preview</title>

<style>
    body {{
        margin: 0;
        padding: 28px;
        background:
            radial-gradient(circle at top left, rgba(255,122,0,0.12), transparent 30%),
            linear-gradient(135deg, #0f0f0f, #191919, #0b0b0b);
        color: #ffffff;
        font-family: Arial, Segoe UI, sans-serif;
    }}

    .page {{
        max-width: 1600px;
        margin: 0 auto;
        background: linear-gradient(135deg, #202020, #151515);
        border: 1px solid #333333;
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 24px 60px rgba(0,0,0,0.45);
    }}

    .header {{
        border-bottom: 4px solid #ff7a00;
        padding-bottom: 18px;
        margin-bottom: 24px;
    }}

    h1 {{
        margin: 0;
        font-size: 32px;
    }}

    .subtitle {{
        color: #b8b8b8;
        margin-top: 8px;
        font-size: 14px;
    }}

    .summary {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }}

    .summary-card {{
        background: linear-gradient(135deg, #34363d, #1b1c22);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 16px;
    }}

    .summary-title {{
        color: #b8b8b8;
        font-size: 13px;
        margin-bottom: 8px;
    }}

    .summary-value {{
        color: #ffffff;
        font-size: 26px;
        font-weight: bold;
    }}

    .chart-box {{
        background: #151515;
        border: 1px solid #333333;
        border-radius: 20px;
        padding: 12px;
        margin-bottom: 28px;
    }}

    .table-box {{
        background: #151515;
        border: 1px solid #333333;
        border-radius: 20px;
        padding: 16px;
        max-height: 520px;
        overflow: auto;
    }}

    table.reason-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        color: #ffffff;
    }}

    table.reason-table thead {{
        background: #2a2a2a;
        position: sticky;
        top: 0;
    }}

    table.reason-table th {{
        color: #ff9a3d;
        padding: 12px 10px;
        text-align: left;
        border-bottom: 1px solid #444444;
    }}

    table.reason-table td {{
        padding: 10px;
        border-bottom: 1px solid #2c2c2c;
        color: #eeeeee;
    }}

    table.reason-table tr:nth-child(even) {{
        background: rgba(255,255,255,0.025);
    }}

    table.reason-table tr:hover {{
        background: rgba(255,122,0,0.08);
    }}
</style>
</head>

<body>
    <div class="page">
        <div class="header">
            <h1>Sankey Funnel Preview</h1>
            <div class="subtitle">
                Request to Buy path with negative drop-off reasons from qualification_details.xlsx
            </div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-title">Total Rows / Requests</div>
                <div class="summary-value">{total_requests:,}</div>
            </div>

            <div class="summary-card">
                <div class="summary-title">Not Qualified</div>
                <div class="summary-value">{int(df["notqualified"].sum()):,}</div>
            </div>

            <div class="summary-card">
                <div class="summary-title">OTP Verified</div>
                <div class="summary-value">{int(df["otp_verified"].sum()):,}</div>
            </div>

            <div class="summary-card">
                <div class="summary-title">Buy</div>
                <div class="summary-value">{int(df["buy"].sum()):,}</div>
            </div>
        </div>

        <div class="chart-box">
            {chart_html}
        </div>

        <h2>Drop-off Reason Breakdown</h2>

        <div class="table-box">
            {reason_table_html}
        </div>
    </div>
</body>
</html>
"""

OUTPUT_HTML.write_text(html, encoding="utf-8")

print(f"Sankey preview created successfully: {OUTPUT_HTML}")
print(f"Total rows: {total_requests:,}")
print(f"Not Qualified: {int(df['notqualified'].sum()):,}")
print(f"OTP Verified: {int(df['otp_verified'].sum()):,}")
print(f"Reserve: {int(df['reserve'].sum()):,}")
print(f"Conf Entrance: {int(df['confentrance'].sum()):,}")
print(f"Entrance: {int(df['entrance'].sum()):,}")
print(f"Inspection: {int(df['inspection'].sum()):,}")
print(f"Auction: {int(df['auction'].sum()):,}")
print(f"Buy: {int(df['buy'].sum()):,}")

webbrowser.open(OUTPUT_HTML.as_uri())