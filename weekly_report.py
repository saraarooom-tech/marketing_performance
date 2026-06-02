import pandas as pd
from pathlib import Path
from datetime import datetime
import webbrowser

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# =========================
# Config
# =========================
OTP_TARGET = 19000

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

CURRENT_PATH = DATA_DIR / "current_week.csv"
PREVIOUS_PATH = DATA_DIR / "previous_week.csv"

OUTPUT_HTML = BASE_DIR / "weekly_report.html"

ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

CHANNEL_CHART_PATH = ASSETS_DIR / "channel_split_donut.png"


# =========================
# Columns
# =========================
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

FUNNEL_STEPS = [
    ("Request", "request"),
    ("Qualified Request", "qualified request"),
    ("OTP Verified QR", "OTP verified QR"),
    ("Reserve", "Reserve"),
    ("Entrance", "Entrance"),
    ("Buy", "Buy"),
]


# =========================
# Helpers
# =========================
def read_week_file(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin1")

    df.columns = df.columns.str.strip()

    if "attribution_title" not in df.columns:
        raise ValueError("Column 'attribution_title' not found.")

    df["attribution_title"] = (
        df["attribution_title"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    for col in ADDITIVE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Remove Total row. Totals are calculated automatically.
    df = df[df["attribution_title"].str.lower() != "total"].copy()

    # Aggregate duplicate attribution_title rows if any
    df = (
        df.groupby("attribution_title", as_index=False)[ADDITIVE_COLUMNS]
        .sum()
    )

    return df


def calculate_total(df):
    return df[ADDITIVE_COLUMNS].sum(numeric_only=True)


def format_number(value):
    try:
        value = float(value)
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    except:
        return str(value)


def format_revenue(value):
    try:
        return f"{int(float(value)):,}"
    except:
        return str(value)


def format_percent(value):
    try:
        return f"{float(value):.1f}%"
    except:
        return str(value)


def format_signed_number(value):
    try:
        value = float(value)
        sign = "+" if value > 0 else ""
        if value.is_integer():
            return f"{sign}{int(value):,}"
        return f"{sign}{value:,.2f}"
    except:
        return str(value)


def format_signed_percent(value):
    try:
        value = float(value)
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.1f}%"
    except:
        return str(value)


def format_signed_pp(value):
    try:
        value = float(value)
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.1f}pp"
    except:
        return str(value)


def change_class(value):
    try:
        value = float(value)
        if value > 0:
            return "positive"
        if value < 0:
            return "negative"
        return "neutral"
    except:
        return "neutral"


def calc_delta(current, previous):
    current = float(current)
    previous = float(previous)

    delta = current - previous
    delta_pct = (delta / previous * 100) if previous else 0

    return delta, delta_pct


def calc_cr(numerator, denominator):
    numerator = float(numerator)
    denominator = float(denominator)

    if denominator == 0:
        return None

    return numerator / denominator * 100


def safe_cr(numerator, denominator):
    result = calc_cr(numerator, denominator)
    return 0 if result is None else result


def truncate_text(text, max_len=30):
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# =========================
# Read Data
# =========================
current_df = read_week_file(CURRENT_PATH)
previous_df = read_week_file(PREVIOUS_PATH)

current_total = calculate_total(current_df)
previous_total = calculate_total(previous_df)


# =========================
# KPI Calculations
# =========================
current_request = float(current_total["request"])
previous_request = float(previous_total["request"])

current_qualified = float(current_total["qualified request"])
previous_qualified = float(previous_total["qualified request"])

current_otp = float(current_total["OTP verified QR"])
previous_otp = float(previous_total["OTP verified QR"])

current_reserve = float(current_total["Reserve"])
previous_reserve = float(previous_total["Reserve"])

current_buy = float(current_total["Buy"])
previous_buy = float(previous_total["Buy"])

current_reserve_otp_cr = safe_cr(current_reserve, current_otp)
previous_reserve_otp_cr = safe_cr(previous_reserve, previous_otp)
reserve_otp_cr_change = current_reserve_otp_cr - previous_reserve_otp_cr

otp_achievement = (current_otp / OTP_TARGET * 100) if OTP_TARGET else 0
otp_progress = min(max(otp_achievement, 0), 100)
otp_gap = current_otp - OTP_TARGET

if current_otp >= OTP_TARGET:
    otp_status = "Target Achieved"
    otp_status_class = "success"
else:
    otp_status = "Below Target"
    otp_status_class = "danger"


# =========================
# KPI Cards
# =========================
def make_mini_bars(current_value, previous_value):
    max_value = max(abs(float(current_value)), abs(float(previous_value)), 1)

    current_width = max((abs(float(current_value)) / max_value) * 100, 4)
    previous_width = max((abs(float(previous_value)) / max_value) * 100, 4)

    return f"""
        <div class="metric-visual">
            <div class="mini-label">CW / PW</div>

            <div class="bar-row">
                <span>CW</span>
                <div class="mini-track">
                    <div class="mini-fill current" style="width: {current_width:.1f}%;"></div>
                </div>
            </div>

            <div class="bar-row">
                <span>PW</span>
                <div class="mini-track">
                    <div class="mini-fill previous" style="width: {previous_width:.1f}%;"></div>
                </div>
            </div>
        </div>
    """


def make_target_ring():
    return f"""
        <div class="metric-visual ring-visual">
            <div
                class="target-ring"
                style="background: conic-gradient(#ff7a00 {otp_progress:.1f}%, #343844 0);"
            >
                <span>{otp_progress:.0f}%</span>
            </div>
            <div class="mini-label">Target</div>
        </div>
    """


def make_metric_card(
    title,
    current_value,
    previous_value,
    visual_html=None,
    extra_html="",
):
    display_value = format_number(current_value)
    delta, delta_pct = calc_delta(current_value, previous_value)

    delta_cls = change_class(delta)
    arrow = "▲" if delta > 0 else "▼" if delta < 0 else "–"
    subtitle = f"{arrow} {format_signed_percent(delta_pct)} vs previous week"

    if visual_html is None:
        visual_html = make_mini_bars(current_value, previous_value)

    return f"""
        <div class="metric-card">
            <div class="metric-top-line"></div>

            {visual_html}

            <div class="metric-title">{title}</div>
            <div class="metric-value">{display_value}</div>

            <div class="metric-delta {delta_cls}">
                {subtitle}
            </div>

            {extra_html}
        </div>
    """


otp_extra_html = f"""
    <div class="otp-target-box">
        <div class="otp-target-row">
            <span>Target: {format_number(OTP_TARGET)}</span>
            <span class="target-badge {otp_status_class}">{otp_status}</span>
        </div>

        <div class="target-progress">
            <div class="target-progress-fill" style="width: {otp_progress:.1f}%;"></div>
        </div>

        <div class="otp-target-row small">
            <span>{format_percent(otp_achievement)} achieved</span>
            <span>{format_signed_number(otp_gap)}</span>
        </div>
    </div>
"""

reserve_extra_html = f"""
    <div class="sub-metric">
        <div class="sub-metric-label">Reserve / OTP CR</div>
        <div class="sub-metric-value">{format_percent(current_reserve_otp_cr)}</div>
        <div class="sub-metric-change {change_class(reserve_otp_cr_change)}">
            {format_signed_pp(reserve_otp_cr_change)} vs previous week
        </div>
    </div>
"""

metric_cards_html = f"""
    {make_metric_card("Request", current_request, previous_request)}
    {make_metric_card("Qualified Request", current_qualified, previous_qualified)}
    {make_metric_card("OTP Verified QR", current_otp, previous_otp, visual_html=make_target_ring(), extra_html=otp_extra_html)}
    {make_metric_card("Reserve", current_reserve, previous_reserve, extra_html=reserve_extra_html)}
    {make_metric_card("Buy", current_buy, previous_buy)}
"""


# =========================
# Funnel Table
# =========================
def build_funnel_rows():
    rows = []

    for i, (step_name, col) in enumerate(FUNNEL_STEPS):
        previous_value = float(previous_total[col])
        current_value = float(current_total[col])

        volume_change = current_value - previous_value

        if i == 0:
            previous_cr = None
            current_cr = None
            cr_change = None
        else:
            previous_step_col = FUNNEL_STEPS[i - 1][1]

            previous_cr = calc_cr(
                previous_total[col],
                previous_total[previous_step_col],
            )

            current_cr = calc_cr(
                current_total[col],
                current_total[previous_step_col],
            )

            if previous_cr is None or current_cr is None:
                cr_change = None
            else:
                cr_change = current_cr - previous_cr

        rows.append({
            "step": step_name,
            "previous_value": previous_value,
            "previous_cr": previous_cr,
            "current_value": current_value,
            "current_cr": current_cr,
            "volume_change": volume_change,
            "cr_change": cr_change,
        })

    return rows


def make_funnel_table():
    rows = build_funnel_rows()

    html = """
        <table class="funnel-table">
            <thead>
                <tr>
                    <th>Step of funnel</th>
                    <th>Previous Week</th>
                    <th>CR</th>
                    <th>Current Week</th>
                    <th>CR</th>
                    <th>Change in Volume</th>
                    <th>% Change in CR</th>
                </tr>
            </thead>
            <tbody>
    """

    for row in rows:
        volume_cls = change_class(row["volume_change"])
        cr_cls = change_class(row["cr_change"]) if row["cr_change"] is not None else "neutral"

        previous_cr = "-" if row["previous_cr"] is None else format_percent(row["previous_cr"])
        current_cr = "-" if row["current_cr"] is None else format_percent(row["current_cr"])
        cr_change = "-" if row["cr_change"] is None else format_signed_percent(row["cr_change"])

        html += f"""
            <tr>
                <td class="step-name">
                    <span class="step-dot"></span>
                    {row["step"]}
                </td>
                <td>{format_number(row["previous_value"])}</td>
                <td>{previous_cr}</td>
                <td>{format_number(row["current_value"])}</td>
                <td>{current_cr}</td>
                <td>
                    <span class="change-pill {volume_cls}">
                        {format_signed_number(row["volume_change"])}
                    </span>
                </td>
                <td>
                    <span class="change-pill {cr_cls}">
                        {cr_change}
                    </span>
                </td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    """

    return html


funnel_table_html = make_funnel_table()


# =========================
# Channel Split - Current Week Only
# =========================
def prepare_channel_split():
    channel_df = current_df[["attribution_title", "qualified request"]].copy()
    channel_df = channel_df.sort_values("qualified request", ascending=False)

    total_qualified = channel_df["qualified request"].sum()

    if total_qualified == 0:
        channel_df["share"] = 0
    else:
        channel_df["share"] = channel_df["qualified request"] / total_qualified * 100

    return channel_df


channel_df = prepare_channel_split()


def create_channel_donut_chart(channel_df):
    chart_df = channel_df.copy()

    top_n = 10
    top_df = chart_df.head(top_n).copy()
    others_df = chart_df.iloc[top_n:].copy()

    if not others_df.empty:
        others_value = others_df["qualified request"].sum()
        total_qualified = chart_df["qualified request"].sum()
        others_share = (others_value / total_qualified * 100) if total_qualified else 0

        others_row = pd.DataFrame([{
            "attribution_title": "Others",
            "qualified request": others_value,
            "share": others_share,
        }])

        plot_df = pd.concat([top_df, others_row], ignore_index=True)
    else:
        plot_df = top_df

    labels = [
        f"{truncate_text(row['attribution_title'], 24)}: {row['share']:.1f}%"
        for _, row in plot_df.iterrows()
    ]

    values = plot_df["qualified request"].values

    colors = [
        "#FF7A00",
        "#FF9A3D",
        "#FFB066",
        "#D96C00",
        "#C55F00",
        "#B88A5A",
        "#9E9E9E",
        "#7B7B7B",
        "#5F6368",
        "#4B4F58",
        "#303030",
    ]

    fig, ax = plt.subplots(figsize=(8.8, 5.4), facecolor="#171717")
    ax.set_facecolor("#171717")

    wedges, _ = ax.pie(
        values,
        colors=colors[:len(values)],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.38, edgecolor="#171717", linewidth=2),
    )

    ax.text(
        0,
        0.04,
        "Qualified\nRequest",
        ha="center",
        va="center",
        color="white",
        fontsize=13,
        fontweight="bold",
    )

    legend = ax.legend(
        wedges,
        labels,
        title="Attribution Share",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=9,
        title_fontsize=10,
    )

    for text in legend.get_texts():
        text.set_color("#EDEDED")

    legend.get_title().set_color("#FF9A3D")

    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(CHANNEL_CHART_PATH, dpi=180, transparent=False, facecolor="#171717")
    plt.close()


def make_channel_table(channel_df):
    html = """
        <table class="standard-table">
            <thead>
                <tr>
                    <th>Attribution Title</th>
                    <th>Qualified Request</th>
                    <th>Share %</th>
                </tr>
            </thead>
            <tbody>
    """

    for _, row in channel_df.iterrows():
        html += f"""
            <tr>
                <td>{row["attribution_title"]}</td>
                <td>{format_number(row["qualified request"])}</td>
                <td>{format_percent(row["share"])}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    """

    return html


create_channel_donut_chart(channel_df)
channel_table_html = make_channel_table(channel_df)


# =========================
# Current Week Table
# =========================
def make_current_week_table():
    temp = current_df.copy()

    temp["Otp/QR"] = temp.apply(
        lambda r: safe_cr(r["OTP verified QR"], r["qualified request"]),
        axis=1
    )

    temp["Reserve/OTP"] = temp.apply(
        lambda r: safe_cr(r["Reserve"], r["OTP verified QR"]),
        axis=1
    )

    temp["Entrance/Reserve"] = temp.apply(
        lambda r: safe_cr(r["Entrance"], r["Reserve"]),
        axis=1
    )

    temp["Buy/OTP verified"] = temp.apply(
        lambda r: safe_cr(r["Buy"], r["OTP verified QR"]),
        axis=1
    )

    temp = temp.sort_values("request", ascending=False)

    columns = [
        "attribution_title",
        "request",
        "qualified request",
        "OTP verified QR",
        "Reserve",
        "Entrance",
        "Buy",
        "revenue",
        "Otp/QR",
        "Reserve/OTP",
        "Entrance/Reserve",
        "Buy/OTP verified",
    ]

    html = """
        <table class="standard-table">
            <thead>
                <tr>
    """

    for col in columns:
        html += f"<th>{col}</th>"

    html += """
                </tr>
            </thead>
            <tbody>
    """

    for _, row in temp.iterrows():
        html += "<tr>"

        for col in columns:
            if col == "revenue":
                value = format_revenue(row[col])
            elif col in ["Otp/QR", "Reserve/OTP", "Entrance/Reserve", "Buy/OTP verified"]:
                value = format_percent(row[col])
            elif col == "attribution_title":
                value = row[col]
            else:
                value = format_number(row[col])

            html += f"<td>{value}</td>"

        html += "</tr>"

    html += """
            </tbody>
        </table>
    """

    return html


current_week_table_html = make_current_week_table()


# =========================
# Build HTML
# =========================
generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Marketing Performance Weekly Report</title>

<style>
    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        padding: 0;
        background:
            radial-gradient(circle at top left, rgba(255,122,0,0.12), transparent 30%),
            radial-gradient(circle at bottom right, rgba(255,122,0,0.08), transparent 32%),
            linear-gradient(135deg, #0f0f0f 0%, #191919 48%, #0b0b0b 100%);
        color: #ffffff;
        font-family: Arial, Segoe UI, sans-serif;
    }}

    .page {{
        width: 95%;
        max-width: 1680px;
        margin: 34px auto;
        background: linear-gradient(135deg, #202020 0%, #181818 52%, #121212 100%);
        border: 1px solid #333333;
        border-radius: 30px;
        padding: 34px;
        box-shadow: 0 24px 60px rgba(0,0,0,0.48);
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 4px solid #ff7a00;
        padding-bottom: 22px;
        margin-bottom: 30px;
        gap: 24px;
    }}

    .header h1 {{
        margin: 0;
        font-size: 38px;
        color: #ffffff;
        letter-spacing: -0.6px;
    }}

    .header p {{
        margin: 8px 0 0;
        color: #b8b8b8;
        font-size: 15px;
    }}

    .badge {{
        background: linear-gradient(135deg, #2f2f2f, #1d1d1d);
        color: #ff9a3d;
        border: 1px solid #ff7a00;
        border-radius: 999px;
        padding: 10px 18px;
        font-size: 14px;
        white-space: nowrap;
    }}

    /* =========================
       Metric Cards - Dark Theme
    ========================= */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 16px;
        margin-bottom: 30px;
    }}

    .metric-card {{
        min-height: 205px;
        background:
            radial-gradient(circle at top right, rgba(255,122,0,0.16), transparent 34%),
            linear-gradient(135deg, #34363d 0%, #24262d 48%, #17181d 100%);
        border-radius: 18px;
        overflow: hidden;
        position: relative;
        color: #ffffff;
        box-shadow: 0 14px 30px rgba(0,0,0,0.38);
        border: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 16px;
    }}

    .metric-card::before {{
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 7px;
        height: 100%;
        background: linear-gradient(180deg, #ff7a00, #ffb066);
    }}

    .metric-top-line {{
        height: 5px;
        background: linear-gradient(90deg, #ff7a00, rgba(255,122,0,0.15));
    }}

    .metric-title {{
        padding: 20px 18px 0;
        color: #cfd0d5;
        font-size: 14px;
        font-weight: bold;
        padding-right: 92px;
    }}

    .metric-value {{
        padding: 10px 18px 0;
        color: #ffffff;
        font-size: 32px;
        font-weight: bold;
        letter-spacing: -0.6px;
    }}

    .metric-delta {{
        padding: 5px 18px 0;
        font-size: 12px;
        font-weight: bold;
    }}

    .metric-visual {{
        position: absolute;
        top: 22px;
        right: 16px;
        width: 76px;
        padding: 8px;
        border-radius: 14px;
        background: rgba(0,0,0,0.22);
        border: 1px solid rgba(255,255,255,0.08);
    }}

    .mini-label {{
        color: #aeb0b8;
        font-size: 9px;
        font-weight: bold;
        margin-bottom: 6px;
        text-align: center;
    }}

    .bar-row {{
        display: grid;
        grid-template-columns: 22px 1fr;
        align-items: center;
        gap: 5px;
        margin-bottom: 5px;
    }}

    .bar-row span {{
        color: #bfc1ca;
        font-size: 9px;
        font-weight: bold;
    }}

    .mini-track {{
        height: 6px;
        border-radius: 999px;
        background: #343844;
        overflow: hidden;
    }}

    .mini-fill {{
        height: 100%;
        border-radius: 999px;
    }}

    .mini-fill.current {{
        background: linear-gradient(90deg, #ff7a00, #ffb066);
    }}

    .mini-fill.previous {{
        background: linear-gradient(90deg, #7d8294, #c1c4cf);
    }}

    .ring-visual {{
        width: 70px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}

    .target-ring {{
        width: 46px;
        height: 46px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }}

    .target-ring::after {{
        content: "";
        position: absolute;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #22242b;
    }}

    .target-ring span {{
        position: relative;
        z-index: 2;
        font-size: 10px;
        font-weight: bold;
        color: #ffffff;
    }}

    .positive {{
        color: #00ff84 !important;
        font-weight: bold;
    }}

    .negative {{
        color: #ffb083 !important;
        font-weight: bold;
    }}

    .neutral {{
        color: #d0d0d0 !important;
        font-weight: bold;
    }}

    .otp-target-box {{
        padding: 12px 18px 0;
    }}

    .otp-target-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: #cfd0d5;
        gap: 8px;
        margin-bottom: 6px;
    }}

    .otp-target-row.small {{
        margin-top: 6px;
        margin-bottom: 0;
        color: #aeb0b8;
    }}

    .target-badge {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: bold;
        white-space: nowrap;
    }}

    .target-badge.success {{
        background: rgba(0, 255, 132, 0.10);
        color: #00ff84;
        border: 1px solid rgba(0,255,132,0.45);
    }}

    .target-badge.danger {{
        background: rgba(255, 122, 0, 0.14);
        color: #ffb083;
        border: 1px solid rgba(255,122,0,0.55);
    }}

    .target-progress {{
        width: 100%;
        height: 8px;
        background: #343844;
        border-radius: 999px;
        overflow: hidden;
    }}

    .target-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, #ff7a00, #ffb066);
        border-radius: 999px;
    }}

    .sub-metric {{
        margin: 12px 18px 0;
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(0,0,0,0.22);
        border: 1px solid rgba(255,255,255,0.08);
    }}

    .sub-metric-label {{
        color: #aeb0b8;
        font-size: 11px;
        font-weight: bold;
    }}

    .sub-metric-value {{
        color: #ffffff;
        font-size: 19px;
        font-weight: bold;
        margin-top: 3px;
    }}

    .sub-metric-change {{
        font-size: 11px;
        margin-top: 3px;
    }}

    /* =========================
       Tabs - Dark Theme
    ========================= */
    .tabs-shell {{
        margin-top: 8px;
        background:
            linear-gradient(135deg, #24262d 0%, #191a20 100%);
        border: 1px solid #333743;
        border-radius: 22px;
        padding: 14px;
        box-shadow: 0 18px 38px rgba(0,0,0,0.28);
    }}

    .tabs {{
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-bottom: 14px;
    }}

    .tab-button {{
        min-width: 210px;
        border: 1px solid rgba(255,255,255,0.08);
        outline: none;
        cursor: pointer;
        padding: 14px 18px;
        border-radius: 14px;
        background: linear-gradient(135deg, #343844, #242832);
        color: #d8d9de;
        font-size: 14px;
        font-weight: bold;
        transition: all 0.2s ease;
        box-shadow: 0 8px 18px rgba(0,0,0,0.18);
    }}

    .tab-button:hover {{
        transform: translateY(-2px);
        border-color: rgba(255,122,0,0.5);
        color: #ffffff;
    }}

    .tab-button.active {{
        background: linear-gradient(135deg, #ff7a00, #d96c00);
        color: #ffffff;
        border-color: #ff9a3d;
        box-shadow: 0 12px 24px rgba(255,122,0,0.18);
    }}

    .tab-content {{
        display: none;
        background:
            radial-gradient(circle at top right, rgba(255,122,0,0.07), transparent 28%),
            linear-gradient(135deg, #1d1f26, #14151a);
        padding: 24px;
        border-radius: 18px;
        color: #ffffff;
        border: 1px solid rgba(255,255,255,0.06);
    }}

    .tab-content.active {{
        display: block;
    }}

    .tab-section-title {{
        color: #ffffff;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 6px;
    }}

    .tab-section-subtitle {{
        color: #aeb0b8;
        font-size: 13px;
        margin-bottom: 18px;
    }}

    .panel {{
        background: linear-gradient(135deg, #1d1d1d, #151515);
        border: 1px solid #333333;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 14px 32px rgba(0,0,0,0.25);
    }}

    .table-wrapper {{
        overflow-x: auto;
        border-radius: 16px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
    }}

    /* =========================
       Funnel Table - Cleaner Template
    ========================= */
    .funnel-table {{
        background: #17191f;
        color: #ffffff;
        font-size: 14px;
        border-collapse: separate;
        border-spacing: 0;
        overflow: hidden;
        border-radius: 16px;
    }}

    .funnel-table thead {{
        background: linear-gradient(135deg, #2b2f3a, #22252e);
    }}

    .funnel-table th {{
        color: #ff9a3d;
        padding: 15px 14px;
        text-align: center;
        font-size: 13px;
        letter-spacing: 0.2px;
        border-bottom: 1px solid rgba(255,122,0,0.35);
        white-space: nowrap;
    }}

    .funnel-table th:first-child {{
        text-align: left;
    }}

    .funnel-table td {{
        padding: 14px;
        text-align: center;
        color: #f1f1f1;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        white-space: nowrap;
    }}

    .funnel-table tbody tr {{
        background: linear-gradient(135deg, #20232b, #1a1c22);
        transition: all 0.18s ease;
    }}

    .funnel-table tbody tr:nth-child(even) {{
        background: linear-gradient(135deg, #242731, #1d2028);
    }}

    .funnel-table tbody tr:hover {{
        background: linear-gradient(135deg, rgba(255,122,0,0.16), rgba(255,122,0,0.05));
        transform: scale(1.002);
    }}

    .funnel-table .step-name {{
        text-align: left;
        color: #ffffff;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 9px;
    }}

    .step-dot {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #ff7a00;
        box-shadow: 0 0 0 4px rgba(255,122,0,0.12);
        flex: 0 0 auto;
    }}

    .change-pill {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 72px;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: bold;
        background: rgba(255,255,255,0.06);
    }}

    .change-pill.positive {{
        background: rgba(0,255,132,0.10);
        border: 1px solid rgba(0,255,132,0.28);
    }}

    .change-pill.negative {{
        background: rgba(255,122,0,0.13);
        border: 1px solid rgba(255,122,0,0.32);
    }}

    .change-pill.neutral {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
    }}

    /* =========================
       Channel Split
    ========================= */
    .channel-grid {{
        display: grid;
        grid-template-columns: 0.95fr 1.05fr;
        gap: 22px;
        align-items: stretch;
    }}

    .chart-panel {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 455px;
    }}

    .chart-panel img {{
        width: 100%;
        max-width: 760px;
        border-radius: 16px;
    }}

    .scroll-box {{
        max-height: 455px;
        overflow: auto;
        border-radius: 12px;
        border: 1px solid #333333;
    }}

    .standard-table {{
        background: #171717;
        color: #ffffff;
        font-size: 13px;
    }}

    .standard-table thead {{
        background: #2a2a2a;
        position: sticky;
        top: 0;
        z-index: 2;
    }}

    .standard-table th {{
        color: #ff9a3d;
        padding: 12px 10px;
        text-align: left;
        border-bottom: 1px solid #444444;
        white-space: nowrap;
    }}

    .standard-table td {{
        color: #eeeeee;
        padding: 10px;
        border-bottom: 1px solid #2c2c2c;
        white-space: nowrap;
    }}

    .standard-table tr:nth-child(even) {{
        background: rgba(255,255,255,0.025);
    }}

    .standard-table tr:hover {{
        background: rgba(255,122,0,0.08);
    }}

    .footer {{
        margin-top: 28px;
        padding-top: 18px;
        border-top: 1px solid #333333;
        color: #888888;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        gap: 18px;
    }}

    @media screen and (max-width: 1450px) {{
        .metric-grid {{
            grid-template-columns: repeat(3, 1fr);
        }}

        .channel-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    @media screen and (max-width: 900px) {{
        .page {{
            width: 98%;
            padding: 22px;
        }}

        .header {{
            flex-direction: column;
        }}

        .metric-grid {{
            grid-template-columns: 1fr;
        }}

        .tabs {{
            flex-direction: column;
        }}

        .tab-button {{
            width: 100%;
        }}
    }}
</style>
</head>

<body>
    <div class="page">
        <div class="header">
            <div>
                <h1>Marketing Performance Weekly Report</h1>
                <p>Current Week vs Previous Week</p>
                <p>Source files: data/current_week.csv and data/previous_week.csv</p>
            </div>

            <div class="badge">
                Generated: {generated_at}
            </div>
        </div>

        <div class="metric-grid">
            {metric_cards_html}
        </div>

        <div class="tabs-shell">
            <div class="tabs">
                <button class="tab-button active" onclick="openTab(event, 'funnel-tab')">
                    Funnel Performance
                </button>

                <button class="tab-button" onclick="openTab(event, 'channel-tab')">
                    Channel Split
                </button>

                <button class="tab-button" onclick="openTab(event, 'current-table-tab')">
                    Current Week Table
                </button>
            </div>

            <div id="funnel-tab" class="tab-content active">
                <div class="tab-section-title">Funnel Performance</div>
                <div class="tab-section-subtitle">
                    Reserve Request is ignored. Reserve is used as the funnel step.
                </div>

                <div class="panel">
                    <div class="table-wrapper">
                        {funnel_table_html}
                    </div>
                </div>
            </div>

            <div id="channel-tab" class="tab-content">
                <div class="tab-section-title">Channel Split by Qualified Request</div>
                <div class="tab-section-subtitle">
                    Current week only. Distribution based on attribution title and qualified request.
                </div>

                <div class="channel-grid">
                    <div class="panel chart-panel">
                        <img src="assets/channel_split_donut.png" alt="Channel Split Donut Chart">
                    </div>

                    <div class="panel">
                        <div class="scroll-box">
                            {channel_table_html}
                        </div>
                    </div>
                </div>
            </div>

            <div id="current-table-tab" class="tab-content">
                <div class="tab-section-title">Current Week Attribution Performance</div>
                <div class="tab-section-subtitle">
                    Current week only. Sorted by request descending.
                </div>

                <div class="panel">
                    <div class="scroll-box">
                        {current_week_table_html}
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <span>Report generated automatically using Python.</span>
            <span>OTP Target: {format_number(OTP_TARGET)}</span>
        </div>
    </div>

<script>
    function openTab(event, tabId) {{
        const contents = document.querySelectorAll('.tab-content');
        const buttons = document.querySelectorAll('.tab-button');

        contents.forEach(content => {{
            content.classList.remove('active');
        }});

        buttons.forEach(button => {{
            button.classList.remove('active');
        }});

        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');
    }}
</script>

</body>
</html>
"""

OUTPUT_HTML.write_text(html, encoding="utf-8")

print(f"Weekly report created successfully: {OUTPUT_HTML}")
print(f"Channel chart created: {CHANNEL_CHART_PATH}")
print(f"OTP Target: {format_number(OTP_TARGET)}")
print(f"OTP Actual: {format_number(current_otp)}")
print(f"OTP Achievement: {format_percent(otp_achievement)}")
print(f"OTP Status: {otp_status}")
print(f"Reserve: {format_number(current_reserve)}")
print(f"Reserve / OTP CR: {format_percent(current_reserve_otp_cr)}")

webbrowser.open(OUTPUT_HTML.as_uri())