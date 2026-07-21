import csv
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SHEET_PATH = DATA_DIR / "sheet_raw.csv"
OUTPUT_HTML = BASE_DIR / "seo_weekly_report.html"

CARD_COLORS = {
    "clicks": "#00d4ff",
    "impressions": "#4f8cff",
    "ctr": "#b86bff",
    "position": "#ffc247",
}

SECTION_SPECS = [
    ("seed_keywords", "Seed Keywords", "کلمات Seed"),
    ("category_keywords", "Category Keywords", "کلمات Category"),
    ("city_keywords", "City Landing Pages", "صفحات شهری"),
]

SEARCH_CONSOLE_METRICS = [
    ("click", "Clicks", CARD_COLORS["clicks"], "number"),
    ("impression", "Impressions", CARD_COLORS["impressions"], "number"),
    ("ctr", "CTR", CARD_COLORS["ctr"], "percent"),
    ("rank", "Avg. Position", CARD_COLORS["position"], "position"),
]

BUSINESS_METRICS = [
    "Q request",
    "Q request - non blog",
    "Buy",
    "Buy - non blog",
    "Organic users",
    "Organic new users",
    "Sessions",
    "Engaged Sessions",
    "Click-branded",
    "Click-non branded",
    "Brand Click Share",
]


def read_sheet_rows(path: Path) -> list[list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Sheet export not found: {path}")

    for encoding in ("utf-8-sig", "utf-8", "cp1256", "latin1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.reader(handle))
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode sheet export")


def clean_text(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def parse_number(value):
    text = clean_text(value)
    if not text or text in {"-", "#DIV/0!", "#REF!", "#N/A"}:
        return None

    text = text.replace("%", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def format_number(value, decimals=0):
    number = parse_number(value)
    if number is None:
        return "-"

    if decimals == 0:
        if float(number).is_integer():
            return f"{int(number):,}"
        return f"{number:,.1f}"

    return f"{number:,.{decimals}f}"


def format_percent(value, decimals=1):
    number = parse_number(value)
    if number is None:
        return "-"
    return f"{number:.{decimals}f}%"


def format_signed_percent(value, decimals=1):
    number = parse_number(value)
    if number is None:
        return "-"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.{decimals}f}%"


def format_signed_number(value, decimals=0):
    number = parse_number(value)
    if number is None:
        return "-"
    sign = "+" if number > 0 else ""
    if decimals == 0 and float(number).is_integer():
        return f"{sign}{int(number):,}"
    return f"{sign}{number:,.{decimals}f}"


def change_class(delta, invert=False):
    number = parse_number(delta)
    if number is None or number == 0:
        return "neutral"

    if invert:
        number = -number

    if number > 0:
        return "positive"
    return "negative"


def calc_delta(current, previous):
    current_value = parse_number(current) or 0
    previous_value = parse_number(previous) or 0
    delta = current_value - previous_value
    delta_pct = (delta / previous_value * 100) if previous_value else 0
    return delta, delta_pct


def normalize_week_label(raw_label: str) -> str:
    text = clean_text(raw_label)
    if not text:
        return ""

    match = re.match(r"(W\d+)\s*\[(.+?)\]", text, flags=re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()} [{match.group(2)}]"
    return ""


def week_code(week_label: str) -> str:
    match = re.match(r"(W\d+)", week_label or "", flags=re.IGNORECASE)
    return match.group(1).upper() if match else week_label


def extract_week_labels(row: list[str]) -> list[str]:
    labels = []
    for index in range(2, len(row), 2):
        label = normalize_week_label(row[index] if index < len(row) else "")
        if label:
            labels.append(label)
    return labels


def find_week_header(rows: list[list[str]], start_index: int):
    for offset in range(0, 4):
        row_index = start_index - offset
        if row_index < 0:
            continue

        candidate = rows[row_index]
        if len(candidate) < 4:
            continue

        labels = extract_week_labels(candidate)
        if labels:
            return labels

    return []


def parse_keyword_sections(rows: list[list[str]]):
    sections = {key: [] for key, _, _ in SECTION_SPECS}

    for index, row in enumerate(rows):
        if len(row) < 4:
            continue

        header = [clean_text(cell).lower() for cell in row[:4]]
        section_key = None
        keyword_col_name = None

        if header[:2] == ["category", "seed keyword"]:
            section_key = "seed_keywords"
            keyword_col_name = "seed_keyword"
        elif header[:2] == ["category", "category keyword"]:
            section_key = "category_keywords"
            keyword_col_name = "category_keyword"
        elif header[:2] == ["city", "seed keyword"]:
            section_key = "city_keywords"
            keyword_col_name = "seed_keyword"
        else:
            continue

        week_labels = find_week_header(rows, index)
        if not week_labels:
            continue

        for data_row in rows[index + 1 :]:
            if not any(clean_text(cell) for cell in data_row):
                break

            category = clean_text(data_row[0] if len(data_row) > 0 else "")
            keyword = clean_text(data_row[1] if len(data_row) > 1 else "")
            lowered_keyword = keyword.lower()

            if not keyword or lowered_keyword.startswith("total"):
                continue

            metrics = {}
            for week_index, week_label in enumerate(week_labels):
                imp_index = 2 + (week_index * 2)
                pos_index = imp_index + 1
                metrics[week_label] = {
                    "impressions": parse_number(
                        data_row[imp_index] if imp_index < len(data_row) else ""
                    ),
                    "position": parse_number(
                        data_row[pos_index] if pos_index < len(data_row) else ""
                    ),
                }

            sections[section_key].append(
                {
                    "category": category,
                    "keyword": keyword,
                    keyword_col_name: keyword,
                    "metrics": metrics,
                }
            )

    return sections


def parse_kpi_section(rows: list[list[str]]):
    for index, row in enumerate(rows):
        if len(row) < 3:
            continue

        if clean_text(row[0]).lower() == "kpi" or clean_text(row[1]).lower() == "kpi":
            header_row = row
            break
    else:
        return [], {}

    week_labels = []
    for col_index in range(2, len(header_row), 2):
        label = normalize_week_label(header_row[col_index])
        if label and label.lower() != "kpi":
            week_labels.append(label)

    metrics = {}
    for data_row in rows[index + 1 :]:
        metric_name = clean_text(data_row[1] if len(data_row) > 1 else data_row[0])
        if not metric_name:
            continue

        if metric_name.lower() == "metrics":
            continue

        if metric_name.lower() in {"da"}:
            continue

        week_values = {}
        for week_index, week_label in enumerate(week_labels):
            value_index = 2 + (week_index * 2)
            growth_index = value_index + 1
            week_values[week_label] = {
                "value": parse_number(
                    data_row[value_index] if value_index < len(data_row) else ""
                ),
                "growth_pct": parse_number(
                    data_row[growth_index] if growth_index < len(data_row) else ""
                ),
            }

        metrics[metric_name] = week_values

    return week_labels, metrics


def build_section_weekly_totals(keyword_sections: dict, week_labels: list[str]):
    totals = {}
    for section_key, _, _ in SECTION_SPECS:
        totals[section_key] = {}
        for week_label in week_labels:
            impressions = 0
            weighted_position = 0
            position_weight = 0

            for row in keyword_sections[section_key]:
                week_metrics = row["metrics"].get(week_label, {})
                imp = week_metrics.get("impressions") or 0
                pos = week_metrics.get("position")
                impressions += imp
                if imp and pos is not None:
                    weighted_position += imp * pos
                    position_weight += imp

            avg_position = (
                weighted_position / position_weight if position_weight else None
            )
            totals[section_key][week_label] = {
                "impressions": impressions,
                "position": avg_position,
            }

    return totals


CATEGORY_GROUPS = [
    {"key": "forosh", "title": "دسته‌بندی فروش"},
    {"key": "price", "title": "قیمت و تخمین قیمت"},
    {"key": "buy", "title": "خرید"},
    {"key": "city", "title": "شهر"},
]


def normalize_category(value) -> str:
    return clean_text(value).strip()


def belongs_to_category_group(group_key: str, section_key: str, category: str) -> bool:
    normalized = normalize_category(category)

    if group_key == "forosh":
        return section_key == "seed_keywords" and normalized == "فروش"

    if group_key == "price":
        return (
            section_key == "seed_keywords"
            and normalized in {"قیمت", "تخمین قیمت"}
        ) or section_key == "category_keywords"

    if group_key == "buy":
        return section_key == "seed_keywords" and normalized == "خرید"

    if group_key == "city":
        return section_key == "city_keywords"

    return False


def build_category_groups(keyword_sections: dict):
    groups = []

    for group_def in CATEGORY_GROUPS:
        rows = []
        for section_key in ("seed_keywords", "category_keywords", "city_keywords"):
            for row in keyword_sections.get(section_key, []):
                if not belongs_to_category_group(
                    group_def["key"],
                    section_key,
                    row.get("category", ""),
                ):
                    continue

                rows.append(
                    {
                        "category": normalize_category(row.get("category", "")),
                        "keyword": row.get("keyword", ""),
                        "metrics": row.get("metrics", {}),
                    }
                )

        groups.append(
            {
                "key": group_def["key"],
                "title": group_def["title"],
                "rows": rows,
            }
        )

    return groups


def build_report_context():
    rows = read_sheet_rows(SHEET_PATH)
    keyword_sections = parse_keyword_sections(rows)
    week_labels, kpi_metrics = parse_kpi_section(rows)

    if len(week_labels) < 2:
        raise ValueError("At least two weekly columns are required in the sheet export.")

    categories = sorted(
        {
            row["category"]
            for section_rows in keyword_sections.values()
            for row in section_rows
            if row.get("category")
        }
    )

    section_totals = build_section_weekly_totals(keyword_sections, week_labels)
    category_groups = build_category_groups(keyword_sections)

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "week_labels": week_labels,
        "default_week": week_labels[-1],
        "kpi_metrics": kpi_metrics,
        "keyword_sections": keyword_sections,
        "section_totals": section_totals,
        "category_groups": category_groups,
        "categories": categories,
        "search_console_metrics": [item[0] for item in SEARCH_CONSOLE_METRICS],
        "business_metrics": [
            metric for metric in BUSINESS_METRICS if metric in kpi_metrics
        ],
    }


def render_html(context: dict) -> str:
    week_options = "".join(
        f'<option value="{week}"{" selected" if week == context["default_week"] else ""}>{week}</option>'
        for week in context["week_labels"]
    )

    trend_week_options = """
        <option value="4">۴ هفته اخیر</option>
        <option value="8" selected>۸ هفته اخیر</option>
        <option value="all">همه هفته‌ها</option>
    """

    category_options = "".join(
        f'<option value="{category}">{category}</option>'
        for category in context["categories"]
    )

    payload = {
        "weekLabels": context["week_labels"],
        "defaultWeek": context["default_week"],
        "kpiMetrics": context["kpi_metrics"],
        "keywordSections": context["keyword_sections"],
        "sectionTotals": context["section_totals"],
        "categoryGroups": context["category_groups"],
        "searchConsoleMetrics": context["search_console_metrics"],
        "businessMetrics": context["business_metrics"],
    }

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>گزارش هفتگی SEO</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        background:
            radial-gradient(circle at top left, rgba(255,122,0,0.12), transparent 30%),
            radial-gradient(circle at bottom right, rgba(0,212,255,0.08), transparent 32%),
            linear-gradient(135deg, #0f0f0f 0%, #191919 48%, #0b0b0b 100%);
        color: #fff;
        font-family: Tahoma, Arial, sans-serif;
    }}
    .page {{
        width: 95%;
        max-width: 1680px;
        margin: 34px auto;
        background: linear-gradient(135deg, #202020 0%, #181818 52%, #121212 100%);
        border: 1px solid #333;
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
        margin-bottom: 24px;
        gap: 24px;
    }}
    .header h1 {{ margin: 0; font-size: 34px; }}
    .header p {{ margin: 8px 0 0; color: #b8b8b8; font-size: 14px; }}
    .badge {{
        background: linear-gradient(135deg, #2f2f2f, #1d1d1d);
        color: #ff9a3d;
        border: 1px solid #ff7a00;
        border-radius: 999px;
        padding: 10px 18px;
        font-size: 13px;
        white-space: nowrap;
    }}
    .section-label {{
        color: #ff9a3d;
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 10px;
        letter-spacing: 0.4px;
    }}
    .filters {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 18px;
    }}
    .sc-filters {{
        grid-template-columns: 1fr 1fr;
        margin-bottom: 12px;
    }}
    .filter-group label {{
        display: block;
        color: #aeb0b8;
        font-size: 12px;
        margin-bottom: 6px;
    }}
    .filter-group select,
    .filter-group input {{
        width: 100%;
        background: #171717;
        border: 1px solid #555;
        color: #fff;
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 14px;
    }}
    .compare-note {{
        margin: 0 0 18px;
        color: #aeb0b8;
        font-size: 13px;
    }}
    .compare-note strong {{ color: #ff9a3d; }}
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 28px;
    }}
    .metric-card {{
        min-height: 190px;
        background: linear-gradient(135deg, #34363d 0%, #24262d 48%, #17181d 100%);
        border-radius: 18px;
        overflow: hidden;
        position: relative;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 14px 30px rgba(0,0,0,0.38);
    }}
    .metric-card::before {{
        content: "";
        position: absolute;
        right: 0;
        top: 0;
        width: 7px;
        height: 100%;
        background: linear-gradient(180deg, var(--accent-color), rgba(255,255,255,0.35));
    }}
    .metric-top-line {{
        height: 5px;
        background: linear-gradient(90deg, var(--accent-color), rgba(255,255,255,0.08));
    }}
    .metric-title {{ padding: 20px 18px 0; color: #cfd0d5; font-size: 14px; font-weight: bold; }}
    .metric-value {{ padding: 10px 18px 0; font-size: 30px; font-weight: bold; }}
    .metric-delta {{ padding: 5px 18px 0; font-size: 12px; font-weight: bold; }}
    .metric-visual {{
        position: absolute;
        top: 22px;
        left: 16px;
        width: 76px;
        padding: 8px;
        border-radius: 14px;
        background: rgba(0,0,0,0.22);
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .mini-label {{ color: #aeb0b8; font-size: 9px; font-weight: bold; margin-bottom: 6px; text-align: center; }}
    .bar-row {{ display: grid; grid-template-columns: 22px 1fr; gap: 5px; margin-bottom: 5px; align-items: center; }}
    .bar-row span {{ color: #bfc1ca; font-size: 9px; font-weight: bold; }}
    .mini-track {{ height: 6px; border-radius: 999px; background: #343844; overflow: hidden; }}
    .mini-fill {{ height: 100%; border-radius: 999px; }}
    .mini-fill.previous {{ background: linear-gradient(90deg, #7d8294, #c1c4cf); }}
    .positive {{ color: #00ff84 !important; }}
    .negative {{ color: #ffb083 !important; }}
    .neutral {{ color: #d0d0d0 !important; }}
    .sc-trend-panel {{
        margin-bottom: 28px;
        background: linear-gradient(135deg, #1d1d1d, #151515);
        border: 1px solid #333;
        border-radius: 18px;
        padding: 18px;
    }}
    .sc-trend-title {{ color: #ff9a3d; font-weight: bold; margin-bottom: 12px; }}
    .chart-canvas-wrap {{ position: relative; height: 320px; }}
    .tabs-shell {{
        background: linear-gradient(135deg, #24262d 0%, #191a20 100%);
        border: 1px solid #333743;
        border-radius: 22px;
        padding: 14px;
    }}
    .tabs {{ display: flex; justify-content: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }}
    .tab-button {{
        min-width: 160px;
        border: 1px solid rgba(255,255,255,0.08);
        cursor: pointer;
        padding: 14px 18px;
        border-radius: 14px;
        background: linear-gradient(135deg, #343844, #242832);
        color: #d8d9de;
        font-weight: bold;
    }}
    .tab-button.active {{
        background: linear-gradient(135deg, #ff7a00, #d96c00);
        color: #fff;
        border-color: #ff9a3d;
    }}
    .tab-content {{ display: none; background: linear-gradient(135deg, #1d1f26, #14151a); padding: 24px; border-radius: 18px; border: 1px solid rgba(255,255,255,0.06); }}
    .tab-content.active {{ display: block; }}
    .tab-section-title {{ font-size: 22px; font-weight: bold; margin-bottom: 6px; }}
    .tab-section-subtitle {{ color: #aeb0b8; font-size: 13px; margin-bottom: 18px; }}
    .panel {{ background: linear-gradient(135deg, #1d1d1d, #151515); border: 1px solid #333; border-radius: 18px; padding: 16px; }}
    .trend-panel {{ margin-bottom: 18px; }}
    .trend-panel-header {{ display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }}
    .trend-panel-title {{ color: #ff9a3d; font-weight: bold; }}
    .trend-panel-note {{ color: #aeb0b8; font-size: 12px; }}
    .table-wrapper {{ overflow: auto; border-radius: 16px; max-height: 620px; }}
    .keyword-table, .kpi-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .keyword-table thead, .kpi-table thead {{ position: sticky; top: 0; z-index: 2; background: #2a2f3a; }}
    .keyword-table th, .keyword-table td, .kpi-table th, .kpi-table td {{
        padding: 12px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        white-space: nowrap;
        text-align: center;
    }}
    .keyword-table .text-keyword, .kpi-table .metric-name {{ text-align: right; }}
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
    .change-pill.positive {{ background: rgba(0,255,132,0.10); border: 1px solid rgba(0,255,132,0.28); }}
    .change-pill.negative {{ background: rgba(255,122,0,0.13); border: 1px solid rgba(255,122,0,0.32); }}
    .bar-cell {{
        position: relative;
        min-width: 120px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        overflow: hidden;
    }}
    .bar-cell-fill {{ position: absolute; right: 0; top: 0; bottom: 0; opacity: 0.28; }}
    .bar-cell span {{ position: relative; z-index: 1; font-weight: bold; }}
    .category-groups {{ margin-bottom: 28px; }}
    .keyword-tabs-shell {{
        background: linear-gradient(135deg, #24262d 0%, #191a20 100%);
        border: 1px solid #333743;
        border-radius: 22px;
        padding: 14px;
    }}
    .keyword-tabs {{
        display: flex;
        gap: 10px;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }}
    .keyword-tab-button {{
        min-width: 150px;
        border: 1px solid rgba(255,255,255,0.08);
        cursor: pointer;
        padding: 12px 16px;
        border-radius: 12px;
        background: linear-gradient(135deg, #3a3a3a, #2a2a2a);
        color: #d8d9de;
        font-weight: bold;
        font-size: 13px;
    }}
    .keyword-tab-button.active {{
        background: linear-gradient(135deg, #ff7a00, #d96c00);
        color: #fff;
        border-color: #ff9a3d;
    }}
    .keyword-panel {{
        background: linear-gradient(135deg, #1d1f26, #14151a);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 16px;
    }}
    .keyword-panel-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
        flex-wrap: wrap;
    }}
    .keyword-panel-title {{
        color: #ff9a3d;
        font-size: 18px;
        font-weight: bold;
    }}
    .keyword-panel-week {{
        color: #aeb0b8;
        font-size: 13px;
    }}
    .table-scroll {{
        max-height: 420px;
        overflow: auto;
        border-radius: 14px;
        border: 1px solid #3a3a3a;
    }}
    .sheet-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .sheet-table thead th {{
        background: linear-gradient(135deg, #3a3a3a, #2d2d2d);
        color: #ff9a3d;
        padding: 12px 14px;
        text-align: center;
        border-bottom: 2px solid #ff7a00;
        position: sticky;
        top: 0;
        z-index: 2;
    }}
    .sheet-table thead th.text-col {{ text-align: right; }}
    .sheet-table tbody td {{
        padding: 11px 14px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        text-align: center;
        background: rgba(255,255,255,0.02);
        color: #e8e8e8;
    }}
    .sheet-table tbody td.text-col {{
        text-align: right;
        background: rgba(255, 122, 0, 0.06);
        color: #f5f5f5;
    }}
    .sheet-table tbody tr:nth-child(even) td {{
        background: rgba(255,255,255,0.03);
    }}
    .sheet-table tbody tr:nth-child(even) td.text-col {{
        background: rgba(255, 122, 0, 0.09);
    }}
    .sheet-table tbody tr.total-row td {{
        background: #2a2a2a !important;
        color: #ff9a3d;
        font-weight: bold;
        border-top: 2px solid #ff7a00;
        position: sticky;
        bottom: 0;
    }}
    .sheet-table tbody tr.kw-row {{
        cursor: pointer;
        transition: background 0.15s ease;
    }}
    .sheet-table tbody tr.kw-row:hover {{
        background: rgba(255,122,0,0.10) !important;
    }}
    .sheet-table tbody tr.kw-row.selected td {{
        background: rgba(255,122,0,0.18) !important;
        box-shadow: inset 3px 0 0 #ff7a00;
    }}
    .kw-trend-panel {{
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #3a3a3a;
    }}
    .kw-trend-title {{
        color: #ff9a3d;
        font-weight: bold;
        margin-bottom: 8px;
    }}
    .kw-trend-note {{
        color: #aeb0b8;
        font-size: 12px;
        margin-bottom: 10px;
    }}
    .kw-trend-chart-wrap {{
        position: relative;
        height: 260px;
    }}
    .kw-trend-filters {{
        grid-template-columns: repeat(3, 1fr);
        margin-bottom: 14px;
    }}
    .footer {{
        margin-top: 24px;
        padding-top: 18px;
        border-top: 1px solid #333;
        color: #888;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        gap: 18px;
        flex-wrap: wrap;
    }}
    @media (max-width: 1200px) {{
        .metric-grid, .filters {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 700px) {{
        .metric-grid, .filters {{ grid-template-columns: 1fr; }}
        .page {{ padding: 22px; }}
    }}
</style>
</head>
<body>
<div class="page">
    <div class="header">
        <div>
            <h1>گزارش هفتگی SEO</h1>
        </div>
        <div class="badge">Generated: {context["generated_at"]}</div>
    </div>

    <div class="section-label">Search Console Overview</div>
    <div class="filters sc-filters">
        <div class="filter-group">
            <label for="sc-week-filter">هفته گزارش</label>
            <select id="sc-week-filter">{week_options}</select>
        </div>
        <div class="filter-group">
            <label for="sc-trend-range">بازه ترند</label>
            <select id="sc-trend-range">{trend_week_options}</select>
        </div>
    </div>
    <div class="compare-note" id="sc-compare-note"></div>
    <div class="metric-grid" id="sc-cards"></div>

    <div class="sc-trend-panel">
        <div class="sc-trend-title">ترند هفتگی</div>
        <div class="chart-canvas-wrap">
            <canvas id="sc-trend-chart"></canvas>
        </div>
    </div>

    <div class="section-label">تفکیک کلیدواژه‌ها بر اساس دسته (مطابق شیت)</div>
    <div class="filters">
        <div class="filter-group">
            <label for="week-filter">هفته انتخابی</label>
            <select id="week-filter">{week_options}</select>
        </div>
        <div class="filter-group">
            <label for="category-filter">Category</label>
            <select id="category-filter">
                <option value="all">همه</option>
                {category_options}
            </select>
        </div>
        <div class="filter-group">
            <label for="keyword-search">جستجوی کلمه</label>
            <input id="keyword-search" type="text" placeholder="مثلاً قیمت خودرو">
        </div>
    </div>
    <div class="compare-note" id="compare-note"></div>

    <div class="filters kw-trend-filters">
        <div class="filter-group">
            <label for="kw-from-week">ترند Po از هفته</label>
            <select id="kw-from-week"></select>
        </div>
        <div class="filter-group">
            <label for="kw-to-week">تا هفته</label>
            <select id="kw-to-week"></select>
        </div>
        <div class="filter-group">
            <label for="kw-trend-select">کلیدواژه</label>
            <select id="kw-trend-select"></select>
        </div>
    </div>

    <div class="category-groups keyword-tabs-shell">
        <div class="keyword-tabs" id="keyword-tabs"></div>
        <div class="keyword-panel" id="keyword-panel"></div>
    </div>

    <div class="tabs-shell">
        <div class="tabs">
            <button class="tab-button active" data-tab="business-tab">Business KPIs</button>
            <button class="tab-button" data-tab="kpi-tab">KPI Full Trend</button>
        </div>

        <div id="business-tab" class="tab-content active">
            <div class="tab-section-title">Business KPIs</div>
            <div class="tab-section-subtitle">Q request، Buy، Sessions و سایر شاخص‌های بیزینسی به تفکیک هفته.</div>
            <div class="panel">
                <div class="table-wrapper">
                    <table class="kpi-table" id="business-table">
                        <thead></thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="kpi-tab" class="tab-content">
            <div class="tab-section-title">KPI Weekly Trend</div>
            <div class="tab-section-subtitle">تمام شاخص‌های بلوک KPI شیت با رشد هفتگی.</div>
            <div class="panel">
                <div class="table-wrapper">
                    <table class="kpi-table" id="kpi-table">
                        <thead></thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <span>گزارش از خروجی هفتگی شیت ساخته شده است.</span>
        <span id="footer-week-note"></span>
    </div>
</div>

<script>
const reportData = {json.dumps(payload, ensure_ascii=False)};

const SC_CARD_DEFS = {json.dumps(
    [
        {"key": key, "title": title, "color": color, "format": fmt}
        for key, title, color, fmt in SEARCH_CONSOLE_METRICS
    ],
    ensure_ascii=False,
)};

let scTrendChart = null;
let keywordPoChart = null;
let activeKeywordTab = 'forosh';
let selectedKeywordIndex = 0;
let currentKeywordRows = [];

function populateKeywordTrendFilters() {{
    const weeks = reportData.weekLabels || [];
    const fromSelect = document.getElementById('kw-from-week');
    const toSelect = document.getElementById('kw-to-week');
    if (!fromSelect || !toSelect || !weeks.length) return;

    const options = weeks.map(week => `<option value="${{week}}">${{week}}</option>`).join('');
    fromSelect.innerHTML = options;
    toSelect.innerHTML = options;

    const defaultFromIndex = Math.max(0, weeks.length - 6);
    fromSelect.value = weeks[defaultFromIndex];
    toSelect.value = weeks[weeks.length - 1];
}}

function getKeywordTrendWeeks() {{
    const weeks = reportData.weekLabels || [];
    const fromWeek = document.getElementById('kw-from-week')?.value;
    const toWeek = document.getElementById('kw-to-week')?.value;
    const fromIndex = weeks.indexOf(fromWeek);
    const toIndex = weeks.indexOf(toWeek);

    if (fromIndex < 0 || toIndex < 0) {{
        return weeks.slice(Math.max(0, weeks.length - 6));
    }}

    const start = Math.min(fromIndex, toIndex);
    const end = Math.max(fromIndex, toIndex);
    return weeks.slice(start, end + 1);
}}

function selectKeywordForTrend(index) {{
    selectedKeywordIndex = index;
    const trendSelect = document.getElementById('kw-trend-select');
    if (trendSelect) trendSelect.value = String(index);
    document.querySelectorAll('.kw-row').forEach((row, rowIndex) => {{
        row.classList.toggle('selected', rowIndex === index);
    }});
    renderKeywordPoTrendChart();
}}

function getWeekMetrics(metrics, weekLabel) {{
    if (!metrics) return {{}};
    if (metrics[weekLabel]) return metrics[weekLabel];

    const selectedCode = weekCode(weekLabel);
    const matchedKey = Object.keys(metrics).find(key => weekCode(key) === selectedCode);
    return matchedKey ? metrics[matchedKey] : {{}};
}}

function openKeywordTab(groupKey) {{
    activeKeywordTab = groupKey;
    selectedKeywordIndex = 0;
    document.querySelectorAll('.keyword-tab-button').forEach(button => {{
        button.classList.toggle('active', button.dataset.kwTab === groupKey);
    }});
    renderCategoryGroups();
}}

function formatNumber(value, decimals = 0) {{
    const number = Number(value ?? 0);
    if (!Number.isFinite(number)) return '-';
    return number.toLocaleString('en-US', {{
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }});
}}

function formatPercent(value) {{
    const number = Number(value ?? 0);
    if (!Number.isFinite(number)) return '-';
    return `${{number.toFixed(1)}}%`;
}}

function getScWeek() {{
    return document.getElementById('sc-week-filter').value;
}}

function getSelectedWeek() {{
    return document.getElementById('week-filter').value;
}}

function getPreviousWeek(weekLabel) {{
    const index = reportData.weekLabels.indexOf(weekLabel);
    return index > 0 ? reportData.weekLabels[index - 1] : null;
}}

function getTrendWeeks() {{
    const selected = getScWeek();
    const range = document.getElementById('sc-trend-range').value;
    const endIndex = reportData.weekLabels.indexOf(selected);
    if (endIndex < 0) return reportData.weekLabels;

    if (range === 'all') return reportData.weekLabels.slice(0, endIndex + 1);
    const count = range === '4' ? 4 : 8;
    const startIndex = Math.max(0, endIndex - count + 1);
    return reportData.weekLabels.slice(startIndex, endIndex + 1);
}}

function metricValue(metricName, weekLabel) {{
    return reportData.kpiMetrics?.[metricName]?.[weekLabel]?.value ?? null;
}}

function metricGrowth(metricName, weekLabel) {{
    return reportData.kpiMetrics?.[metricName]?.[weekLabel]?.growth_pct ?? null;
}}

function deltaInfo(current, previous, invert = false) {{
    if (current === null || current === undefined) {{
        return {{ delta: null, deltaPct: null, cls: 'neutral', arrow: '–' }};
    }}

    const currentValue = Number(current);
    const previousValue = previous === null || previous === undefined ? null : Number(previous);
    const delta = previousValue === null ? null : currentValue - previousValue;
    const deltaPct = previousValue ? (delta / previousValue) * 100 : null;
    let cls = 'neutral';
    if (delta !== null) {{
        const adjusted = invert ? -delta : delta;
        if (adjusted > 0) cls = 'positive';
        if (adjusted < 0) cls = 'negative';
    }}
    const arrow = delta === null ? '–' : delta > 0 ? '▲' : delta < 0 ? '▼' : '–';
    return {{ delta, deltaPct, cls, arrow }};
}}

function makeMiniBars(currentValue, previousValue, accentColor) {{
    const current = Math.abs(Number(currentValue ?? 0));
    const previous = Math.abs(Number(previousValue ?? 0));
    const maxValue = Math.max(current, previous, 1);
    const currentWidth = Math.max((current / maxValue) * 100, 4);
    const previousWidth = Math.max((previous / maxValue) * 100, 4);
    return `
        <div class="metric-visual">
            <div class="mini-label">CW / PW</div>
            <div class="bar-row"><span>CW</span><div class="mini-track"><div class="mini-fill" style="width:${{currentWidth}}%; background:linear-gradient(90deg, ${{accentColor}}, rgba(255,255,255,0.45));"></div></div></div>
            <div class="bar-row"><span>PW</span><div class="mini-track"><div class="mini-fill previous" style="width:${{previousWidth}}%;"></div></div></div>
        </div>
    `;
}}

function formatMetricValue(value, formatType) {{
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
    if (formatType === 'percent') return formatPercent(value);
    if (formatType === 'position') return Number(value).toFixed(1);
    return formatNumber(value);
}}

function renderSearchConsoleCards() {{
    const selectedWeek = getScWeek();
    const previousWeek = getPreviousWeek(selectedWeek);
    const container = document.getElementById('sc-cards');

    container.innerHTML = SC_CARD_DEFS.map(def => {{
        const current = metricValue(def.key, selectedWeek);
        const previous = previousWeek ? metricValue(def.key, previousWeek) : null;
        const invert = def.key === 'rank';
        const change = deltaInfo(current, previous, invert);
        const display = formatMetricValue(current, def.format);
        const deltaText = change.deltaPct === null
            ? '– vs previous week'
            : `${{change.arrow}} ${{formatPercent(change.deltaPct)}} vs previous week`;
        return `
            <div class="metric-card" style="--accent-color:${{def.color}}">
                <div class="metric-top-line"></div>
                ${{makeMiniBars(current ?? 0, previous ?? 0, def.color)}}
                <div class="metric-title">${{def.title}}</div>
                <div class="metric-value">${{display}}</div>
                <div class="metric-delta ${{change.cls}}">${{deltaText}}</div>
            </div>
        `;
    }}).join('');

    document.getElementById('sc-compare-note').innerHTML =
        `داده از بلوک Metrics شیت | هفته: <strong>${{selectedWeek}}</strong> در برابر <strong>${{previousWeek || '-'}}</strong>`;
}}

function renderScTrendChart() {{
    const weeks = getTrendWeeks();
    const ctx = document.getElementById('sc-trend-chart');
    const datasets = [
        {{ key: 'click', label: 'Clicks', color: '#00d4ff', axis: 'y' }},
        {{ key: 'impression', label: 'Impressions', color: '#4f8cff', axis: 'y1' }},
        {{ key: 'ctr', label: 'CTR', color: '#b86bff', axis: 'y' }},
        {{ key: 'rank', label: 'Avg Position', color: '#ffc247', axis: 'y' }},
    ].map(item => ({{
        label: item.label,
        data: weeks.map(week => metricValue(item.key, week)),
        borderColor: item.color,
        backgroundColor: item.color + '22',
        tension: 0.25,
        yAxisID: item.axis,
    }}));

    if (scTrendChart) scTrendChart.destroy();
    scTrendChart = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: weeks.map(week => weekCode(week)),
            datasets,
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ labels: {{ color: '#ddd' }} }} }},
            scales: {{
                x: {{ ticks: {{ color: '#bbb' }}, grid: {{ color: 'rgba(255,255,255,0.06)' }} }},
                y: {{ position: 'left', ticks: {{ color: '#bbb' }}, grid: {{ color: 'rgba(255,255,255,0.06)' }} }},
                y1: {{ position: 'right', ticks: {{ color: '#bbb' }}, grid: {{ drawOnChartArea: false }} }},
            }},
        }},
    }});
}}

function weekCode(label) {{
    const match = String(label).match(/W\\d+/i);
    return match ? match[0].toUpperCase() : label;
}}

function formatPosition(value) {{
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
    return Number(value).toFixed(1);
}}

function renderKeywordPoTrendChart() {{
    const canvas = document.getElementById('keyword-po-chart');
    if (!canvas) return;

    const weeks = getKeywordTrendWeeks();
    const rows = currentKeywordRows || [];

    if (!rows.length || !weeks.length) {{
        if (keywordPoChart) {{
            keywordPoChart.destroy();
            keywordPoChart = null;
        }}
        return;
    }}

    const safeIndex = Math.min(Math.max(0, selectedKeywordIndex), rows.length - 1);
    selectedKeywordIndex = safeIndex;
    const row = rows[safeIndex];
    const labels = weeks.map(week => weekCode(week));
    const data = weeks.map(week => {{
        const metrics = getWeekMetrics(row.metrics, week);
        const position = metrics.position;
        return position === null || position === undefined ? null : Number(position);
    }});

    if (keywordPoChart) keywordPoChart.destroy();
    keywordPoChart = new Chart(canvas.getContext('2d'), {{
        type: 'line',
        data: {{
            labels,
            datasets: [{{
                label: 'Position (Po)',
                data,
                borderColor: '#ff7a00',
                backgroundColor: 'rgba(255,122,0,0.15)',
                tension: 0.25,
                fill: true,
                spanGaps: true,
                pointRadius: 4,
                pointHoverRadius: 6,
            }}],
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ labels: {{ color: '#ddd' }} }},
                title: {{
                    display: true,
                    text: `${{row.keyword}}${{row.category ? ' — ' + row.category : ''}}`,
                    color: '#ff9a3d',
                }},
            }},
            scales: {{
                x: {{ ticks: {{ color: '#bbb' }}, grid: {{ color: 'rgba(255,255,255,0.06)' }} }},
                y: {{
                    reverse: true,
                    ticks: {{ color: '#bbb' }},
                    grid: {{ color: 'rgba(255,255,255,0.06)' }},
                    title: {{ display: true, text: 'Position (lower is better)', color: '#aaa' }},
                }},
            }},
        }},
    }});
}}

function renderCategoryGroups() {{
    const selectedWeek = getSelectedWeek();
    const categoryFilter = document.getElementById('category-filter').value;
    const searchValue = document.getElementById('keyword-search').value.trim().toLowerCase();
    const tabsContainer = document.getElementById('keyword-tabs');
    const panelContainer = document.getElementById('keyword-panel');
    const groups = reportData.categoryGroups || [];

    if (!groups.length) {{
        panelContainer.innerHTML = '<div class="empty-state">داده‌ای یافت نشد.</div>';
        return;
    }}

    if (!groups.some(group => group.key === activeKeywordTab)) {{
        activeKeywordTab = groups[0].key;
    }}

    tabsContainer.innerHTML = groups.map(group => `
        <button
            class="keyword-tab-button ${{group.key === activeKeywordTab ? 'active' : ''}}"
            data-kw-tab="${{group.key}}"
            onclick="openKeywordTab('${{group.key}}')"
        >${{group.title}}</button>
    `).join('');

    const activeGroup = groups.find(group => group.key === activeKeywordTab) || groups[0];
    const filteredRows = (activeGroup.rows || [])
        .map(row => {{
            const metrics = getWeekMetrics(row.metrics, selectedWeek);
            return {{
                category: row.category || '',
                keyword: row.keyword || '',
                impressions: metrics.impressions ?? null,
                position: metrics.position ?? null,
                metrics: row.metrics || {{}},
            }};
        }})
        .filter(row => {{
            const categoryMatch = categoryFilter === 'all' || row.category === categoryFilter;
            const keywordMatch = !searchValue || String(row.keyword).toLowerCase().includes(searchValue);
            return categoryMatch && keywordMatch;
        }});

    if (selectedKeywordIndex >= filteredRows.length) {{
        selectedKeywordIndex = 0;
    }}
    currentKeywordRows = filteredRows;

    const trendSelect = document.getElementById('kw-trend-select');
    if (trendSelect) {{
        trendSelect.innerHTML = filteredRows.map((row, index) => `
            <option value="${{index}}">${{row.keyword}}${{row.category ? ' (' + row.category + ')' : ''}}</option>
        `).join('');
        if (filteredRows.length) {{
            trendSelect.value = String(selectedKeywordIndex);
        }}
    }}

    let totalImp = 0;
    let weightedPos = 0;
    let posWeight = 0;
    filteredRows.forEach(row => {{
        const imp = Number(row.impressions || 0);
        totalImp += imp;
        if (imp > 0 && row.position !== null && row.position !== undefined) {{
            weightedPos += imp * Number(row.position);
            posWeight += imp;
        }}
    }});
    const avgPos = posWeight ? weightedPos / posWeight : null;

    const bodyRows = filteredRows.map((row, index) => `
        <tr class="kw-row${{index === selectedKeywordIndex ? ' selected' : ''}}" onclick="selectKeywordForTrend(${{index}})">
            <td class="text-col">${{row.category}}</td>
            <td class="text-col">${{row.keyword}}</td>
            <td>${{row.impressions === null || row.impressions === undefined ? '-' : formatNumber(row.impressions)}}</td>
            <td>${{formatPosition(row.position)}}</td>
        </tr>
    `).join('');

    panelContainer.innerHTML = `
        <div class="keyword-panel-head">
            <div class="keyword-panel-title">${{activeGroup.title}}</div>
            <div class="keyword-panel-week">${{selectedWeek}}</div>
        </div>
        <div class="table-scroll">
            <table class="sheet-table">
                <thead>
                    <tr>
                        <th class="text-col">Category</th>
                        <th class="text-col">Seed Keyword</th>
                        <th>IMP</th>
                        <th>Po</th>
                    </tr>
                </thead>
                <tbody>
                    ${{bodyRows || '<tr><td colspan="4">داده‌ای برای این فیلتر وجود ندارد.</td></tr>'}}
                    ${{filteredRows.length ? `
                        <tr class="total-row">
                            <td class="text-col" colspan="2">Total / Weighted Average</td>
                            <td>${{formatNumber(totalImp)}}</td>
                            <td>${{formatPosition(avgPos)}}</td>
                        </tr>
                    ` : ''}}
                </tbody>
            </table>
        </div>
        <div class="kw-trend-panel">
            <div class="kw-trend-title">ترند پوزیشن (Po)</div>
            <div class="kw-trend-note">روی هر ردیف کلیک کنید یا از لیست کلیدواژه انتخاب کنید. محور Y معکوس است — پوزیشن پایین‌تر بهتر است.</div>
            <div class="kw-trend-chart-wrap">
                <canvas id="keyword-po-chart"></canvas>
            </div>
        </div>
    `;

    renderKeywordPoTrendChart();
}}

function renderKpiTable(tableId, metricNames, highlightWeek = null) {{
    const table = document.getElementById(tableId);
    const weeks = reportData.weekLabels;
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    thead.innerHTML = `
        <tr>
            <th>Metric</th>
            ${{weeks.map(week => `<th>${{weekCode(week)}}</th><th>Growth</th>`).join('')}}
        </tr>
    `;

    tbody.innerHTML = metricNames.map(metricName => {{
        const cells = [`<td class="metric-name">${{metricName}}</td>`];
        weeks.forEach(week => {{
            const value = metricValue(metricName, week);
            const growth = metricGrowth(metricName, week);
            const isHighlight = highlightWeek && week === highlightWeek;
            const valueText = metricName.toLowerCase().includes('share') || metricName === 'ctr'
                ? formatPercent(value)
                : metricName === 'rank'
                    ? (value === null ? '-' : Number(value).toFixed(1))
                    : formatNumber(value);
            const growthClass = growth > 0 ? 'positive' : growth < 0 ? 'negative' : 'neutral';
            const growthText = growth === null || growth === undefined ? '-' : `${{growth > 0 ? '+' : ''}}${{Number(growth).toFixed(1)}}%`;
            cells.push(`<td style="${{isHighlight ? 'background:rgba(255,122,0,0.12);' : ''}}">${{valueText}}</td>`);
            cells.push(`<td><span class="change-pill ${{growthClass}}">${{growthText}}</span></td>`);
        }});
        return `<tr>${{cells.join('')}}</tr>`;
    }}).join('');
}}

function refreshDashboard() {{
    renderSearchConsoleCards();
    renderScTrendChart();
    renderCategoryGroups();
    renderKpiTable('business-table', reportData.businessMetrics, getScWeek());
    renderKpiTable('kpi-table', Object.keys(reportData.kpiMetrics), getScWeek());

    const selectedWeek = getSelectedWeek();
    const previousWeek = getPreviousWeek(selectedWeek);
    document.getElementById('compare-note').innerHTML =
        `تفکیک کلیدواژه‌ها | هفته: <strong>${{selectedWeek}}</strong> در برابر <strong>${{previousWeek || '-'}}</strong>`;
    document.getElementById('footer-week-note').textContent =
        `SC: ${{getScWeek()}} | Keywords: ${{selectedWeek}}`;
}}

function openTab(tabId) {{
    document.querySelectorAll('.tab-content').forEach(node => node.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(node => node.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    document.querySelector(`[data-tab="${{tabId}}"]`).classList.add('active');
}}

document.querySelectorAll('.tab-button').forEach(button => {{
    button.addEventListener('click', () => openTab(button.dataset.tab));
}});

['sc-week-filter', 'sc-trend-range'].forEach(id => {{
    document.getElementById(id).addEventListener('change', () => {{
        renderSearchConsoleCards();
        renderScTrendChart();
        renderKpiTable('business-table', reportData.businessMetrics, getScWeek());
        renderKpiTable('kpi-table', Object.keys(reportData.kpiMetrics), getScWeek());
        document.getElementById('footer-week-note').textContent =
            `SC: ${{getScWeek()}} | Keywords: ${{getSelectedWeek()}}`;
    }});
}});

['week-filter', 'category-filter'].forEach(id => {{
    document.getElementById(id).addEventListener('change', () => {{
        renderCategoryGroups();
        const selectedWeek = getSelectedWeek();
        const previousWeek = getPreviousWeek(selectedWeek);
        document.getElementById('compare-note').innerHTML =
            `تفکیک کلیدواژه‌ها | هفته: <strong>${{selectedWeek}}</strong> در برابر <strong>${{previousWeek || '-'}}</strong>`;
        document.getElementById('footer-week-note').textContent =
            `SC: ${{getScWeek()}} | Keywords: ${{selectedWeek}}`;
    }});
}});
document.getElementById('keyword-search').addEventListener('input', renderCategoryGroups);

['kw-from-week', 'kw-to-week'].forEach(id => {{
    document.getElementById(id).addEventListener('change', renderKeywordPoTrendChart);
}});
document.getElementById('kw-trend-select').addEventListener('change', event => {{
    selectKeywordForTrend(Number(event.target.value));
}});

populateKeywordTrendFilters();
refreshDashboard();
</script>
</body>
</html>"""


def main():
    context = build_report_context()
    html = render_html(context)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"SEO report generated: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
