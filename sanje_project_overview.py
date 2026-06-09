from pathlib import Path
import shutil
import webbrowser


BASE_DIR = Path(__file__).parent
OUTPUT_HTML = BASE_DIR / "sanje_project_overview.html"
ASSETS_DIR = BASE_DIR / "assets" / "sanje"
CURSOR_ASSETS = (
    Path.home()
    / ".cursor"
    / "projects"
    / "c-Users-s-aroom-Desktop-marketing-performance"
    / "assets"
)

IMG_APP_HOME = ASSETS_DIR / "app-home.png"
IMG_DESIGN_REF = ASSETS_DIR / "design-ref.png"


PROJECT = {
    "name": "سنجه",
    "tagline": "اپلیکیشن تخمین قیمت و تحلیل بازار خودرو",
    "subtitle": "زیرساخت اندازه‌گیری، اتریبیوشن و آمادگی انتشار",
    "goal": (
        "ایجاد زیرساخت کامل اندازه‌گیری و اتریبیوشن برای اپلیکیشن تخمین قیمت خودرو، "
        "به‌همراه آمادگی انتشار در استورهای داخلی و ساختار گزارش‌دهی مدیریتی"
    ),
    "summary": (
        "پروژه سنجه بر پایه همکاری با تیم فنی و ابزارهای متریکس و متابیس، مسیر اندازه‌گیری را "
        "از طراحی Measurement Plan تا پیاده‌سازی Event Tracking، انتشار در مایکت و کافه‌بازار، "
        "و طراحی ساختار Attribution و داشبوردها تعریف می‌کند. خروجی نهایی، مجموعه‌ای از مستندات، "
        "چک‌لیست‌ها و ساختارهای قابل اجرا برای لانچ است — نه گزارش عملکرد دوره‌ای."
    ),
    "phase_badge": "وضعیت: آماده‌سازی — فعالیت اجرایی آغاز نشده",
}

OBJECTIVES = [
    {"text": "آماده‌سازی زیرساخت اتریبیوشن", "icon": "attribution"},
    {"text": "پیاده‌سازی ایونت‌ها", "icon": "events"},
    {"text": "انتشار اپ در استورها", "icon": "store"},
    {"text": "ایجاد ساختار گزارش‌دهی", "icon": "reporting"},
]

SCOPE = [
    {"text": "جلسات با متریکس", "icon": "meeting"},
    {"text": "طراحی Measurement Plan", "icon": "plan"},
    {"text": "طراحی و پیاده‌سازی Event Tracking", "icon": "tracking"},
    {"text": "انتشار در مایکت و کافه‌بازار", "icon": "publish"},
    {"text": "آماده‌سازی محتوای استورها", "icon": "content"},
    {"text": "طراحی Attribution در متابیس", "icon": "dashboard"},
]

DELIVERABLES = [
    {"text": "Event Tracking Plan", "icon": "doc-events"},
    {"text": "Attribution Structure", "icon": "doc-attribution"},
    {"text": "Store Assets Checklist", "icon": "doc-store"},
    {"text": "Metabase Dashboard Structure", "icon": "doc-metabase"},
    {"text": "Launch Readiness Checklist", "icon": "doc-launch"},
]

DEPENDENCIES = [
    {"text": "همکاری تیم فنی", "icon": "team"},
    {"text": "دسترسی به متریکس", "icon": "metrix"},
    {"text": "دسترسی به متابیس", "icon": "metabase"},
    {"text": "محتوای مورد نیاز استورها", "icon": "assets"},
]

DEPENDENCIES_NOTE = (
    "پیش‌شرط شروع فازهای اجرایی، تأمین موارد فوق توسط ذی‌نفعان مرتبط است. "
    "تا زمان فراهم شدن وابستگی‌ها، خروجی‌ها در قالب مستند و چک‌لیست تعریف می‌شوند."
)

SECTIONS = [
    {"id": "overview", "num": "۰۱", "title": "Project Overview", "icon": "section-overview"},
    {"id": "objectives", "num": "۰۲", "title": "Project Objectives", "icon": "section-objectives"},
    {"id": "scope", "num": "۰۳", "title": "Scope of Work", "icon": "section-scope"},
    {"id": "deliverables", "num": "۰۴", "title": "Deliverables", "icon": "section-deliverables"},
    {"id": "dependencies", "num": "۰۵", "title": "Dependencies & Requirements", "icon": "section-deps"},
]


def ensure_assets():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if not CURSOR_ASSETS.exists():
        return

    mapping = {
        "*171106*": IMG_APP_HOME,
        "*1024*670*": IMG_DESIGN_REF,
        "*171051*": ASSETS_DIR / "logo.png",
    }
    for pattern, dest in mapping.items():
        if dest.exists():
            continue
        matches = list(CURSOR_ASSETS.glob(pattern))
        if not matches:
            continue
        try:
            shutil.copy2(matches[0], dest)
        except OSError:
            pass


def asset_uri(path: Path) -> str:
    if path.exists():
        return path.relative_to(BASE_DIR).as_posix()
    return ""


# Inline SVG icons — teal / blue brand palette
ICONS = {
    "logo": """
    <svg class="logo-mark" viewBox="0 0 48 48" aria-hidden="true">
      <path d="M8 32 L24 8 L28 16 L16 32 Z" fill="#26C6DA"/>
      <path d="M20 40 L40 16 L36 8 L24 32 Z" fill="#2196F3"/>
    </svg>
    """,
    "section-overview": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 17h14M7 13l3-6 4 8 3-5 2 3"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="19" r="2"/></svg>',
    "section-objectives": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "section-scope": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 9h8M8 13h8M8 17h5"/></svg>',
    "section-deliverables": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 4h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="M14 4v6h6"/></svg>',
    "section-deps": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM16 20a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/><path d="M10.5 10.5l3 3"/></svg>',
    "attribution": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 18V6l8 4 8-4v12"/><path d="M12 10v8"/></svg>',
    "events": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 12h4l2-6 4 12 2-6h4"/></svg>',
    "store": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="5" y="8" width="14" height="12" rx="2"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
    "reporting": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 19V5M10 19V11M15 19V8M20 19V14"/></svg>',
    "meeting": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="8" cy="9" r="3"/><circle cx="16" cy="9" r="3"/><path d="M3 19c0-3 3-5 5-5s5 2 5 2M11 19c0-3 3-5 5-5s5 2 5 2"/></svg>',
    "plan": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 4h12v16H6z"/><path d="M9 8h6M9 12h6M9 16h4"/></svg>',
    "tracking": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4l7 7-3 9 9-3 7 7"/></svg>',
    "publish": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M10 18h4"/></svg>',
    "content": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M3 16l4-4 4 4 4-5 6 7"/></svg>',
    "dashboard": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="5" rx="1"/><rect x="13" y="10" width="8" height="11" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/></svg>',
    "doc-events": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 4h10v16H7z"/><path d="M10 8h4M10 12h4M10 16h2"/></svg>',
    "doc-attribution": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 18l4-8 4 5 6-11"/></svg>',
    "doc-store": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 6l2 12h10l2-12"/><path d="M9 6h6"/></svg>',
    "doc-metabase": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/></svg>',
    "doc-launch": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l8 14H4z"/><path d="M12 10v4"/></svg>',
    "team": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2"/><path d="M4 19c0-3 2-5 5-5M14 19c0-2 2-4 4-4"/></svg>',
    "metrix": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="8"/></svg>',
    "metabase": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16v10H4z"/><path d="M8 11h8M8 15h5"/></svg>',
    "assets": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/></svg>',
    "car": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 14h16l-1-5H5z"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>',
    "price": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3v18"/><path d="M7 8c0-3 10-3 10 0s-10 3-10 6 10 3 10 6-10 3-10 0"/></svg>',
}


def icon(name: str, extra_class: str = "") -> str:
    svg = ICONS.get(name, ICONS["car"])
    cls = f"icon-svg {extra_class}".strip()
    return f'<span class="{cls}" aria-hidden="true">{svg}</span>'


def section_heading(num: str, title: str, icon_name: str) -> str:
    return f"""
    <div class="section-head">
        <div class="section-icon-wrap">{icon(icon_name, "section-icon")}</div>
        <div>
            <p class="section-number">{num}</p>
            <h2 class="section-title">{title}</h2>
        </div>
    </div>
    """


def render_icon_list(items, list_class="item-list"):
    rows = []
    for item in items:
        rows.append(
            f'<li><span class="item-icon">{icon(item["icon"])}</span>'
            f'<span class="item-text">{item["text"]}</span></li>'
        )
    return f'<ul class="{list_class}">{"".join(rows)}</ul>'


def render_deliverables(items):
    cards = []
    for item in items:
        cards.append(
            f'<div class="deliverable-card">'
            f'<div class="deliverable-icon">{icon(item["icon"])}</div>'
            f'<span>{item["text"]}</span></div>'
        )
    return f'<div class="deliverables-grid">{"".join(cards)}</div>'


def build_html():
    ensure_assets()
    app_home_src = asset_uri(IMG_APP_HOME)
    design_ref_src = asset_uri(IMG_DESIGN_REF)
    logo_png = asset_uri(ASSETS_DIR / "logo.png")

    hero_visual = ""
    if app_home_src:
        hero_visual = f"""
        <div class="hero-visual">
            <img src="{app_home_src}" alt="صفحه اصلی اپلیکیشن سنجه" class="app-shot">
        </div>
        """
    decor_ref = ""
    if design_ref_src:
        decor_ref = f'<img src="{design_ref_src}" alt="" class="decor-ref" aria-hidden="true">'

    logo_img = ""
    if logo_png:
        logo_img = f'<img src="{logo_png}" alt="لوگو سنجه" class="logo-img">'
    else:
        logo_img = icon("logo", "logo-img-svg")

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{PROJECT["name"]} — Project Overview</title>
    <style>
        * {{ box-sizing: border-box; }}

        :root {{
            --navy: #1a2d4a;
            --navy-deep: #0f1c30;
            --teal: #26c6da;
            --blue: #2196f3;
            --green: #2ecc71;
            --text: #ffffff;
            --muted: #b8c5d6;
            --panel: rgba(255,255,255,0.06);
            --line: rgba(255,255,255,0.1);
        }}

        body {{
            margin: 0;
            padding: 0;
            background:
                radial-gradient(circle at 15% 10%, rgba(38,198,218,0.18), transparent 35%),
                radial-gradient(circle at 85% 80%, rgba(33,150,243,0.14), transparent 38%),
                linear-gradient(160deg, #0c1525 0%, #152238 45%, #0a1220 100%);
            color: var(--text);
            font-family: "Segoe UI", Tahoma, Arial, sans-serif;
            line-height: 1.75;
        }}

        .page {{
            width: 95%;
            max-width: 980px;
            margin: 28px auto 48px;
            background: linear-gradient(180deg, rgba(26,45,74,0.35) 0%, rgba(15,28,48,0.9) 100%);
            border: 1px solid var(--line);
            border-radius: 28px;
            overflow: hidden;
            box-shadow: 0 28px 64px rgba(0,0,0,0.45);
            position: relative;
        }}

        .decor-ref {{
            position: absolute;
            left: -40px;
            bottom: 120px;
            width: 220px;
            opacity: 0.07;
            pointer-events: none;
            filter: blur(1px);
        }}

        .hero {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 24px;
            align-items: center;
            padding: 36px 40px 28px;
            background: linear-gradient(135deg, var(--navy-deep) 0%, var(--navy) 55%, #1e3a5f 100%);
            border-bottom: 3px solid transparent;
            border-image: linear-gradient(90deg, var(--teal), var(--blue)) 1;
            position: relative;
            overflow: hidden;
        }}

        .hero::after {{
            content: "";
            position: absolute;
            left: 0;
            bottom: 0;
            width: 100%;
            height: 80px;
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 80'%3E%3Cpath d='M0 60 Q100 20 200 50 T400 40 L400 80 L0 80 Z' fill='none' stroke='%2326C6DA' stroke-width='2' opacity='0.25'/%3E%3C/svg%3E") center bottom / cover no-repeat;
            opacity: 0.6;
            pointer-events: none;
        }}

        .hero-brand {{
            display: flex;
            gap: 18px;
            align-items: center;
            position: relative;
            z-index: 1;
        }}

        .logo-wrap {{
            width: 72px;
            height: 72px;
            border-radius: 20px;
            background: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 12px 28px rgba(0,0,0,0.25);
            flex-shrink: 0;
        }}

        .logo-img {{
            width: 56px;
            height: 56px;
            object-fit: contain;
            border-radius: 14px;
        }}

        .logo-mark {{ width: 44px; height: 44px; }}

        .hero h1 {{
            margin: 0;
            font-size: 36px;
            font-weight: 700;
        }}

        .hero-tagline {{
            margin: 4px 0 0;
            font-size: 14px;
            color: var(--teal);
            font-weight: 600;
        }}

        .hero-subtitle {{
            margin: 8px 0 0;
            color: var(--muted);
            font-size: 15px;
            max-width: 420px;
        }}

        .hero-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }}

        .badge {{
            padding: 8px 14px;
            font-size: 12px;
            border-radius: 999px;
            border: 1px solid rgba(38,198,218,0.45);
            background: rgba(38,198,218,0.12);
            color: #a8ecf7;
        }}

        .badge.phase {{
            border-color: rgba(33,150,243,0.4);
            background: rgba(33,150,243,0.12);
            color: #b3d9ff;
        }}

        .hero-visual {{
            position: relative;
            z-index: 1;
        }}

        .app-shot {{
            width: 200px;
            border-radius: 22px;
            border: 3px solid rgba(255,255,255,0.15);
            box-shadow: 0 20px 40px rgba(0,0,0,0.35);
        }}

        .cover-label {{
            margin: 0 0 6px;
            font-size: 11px;
            letter-spacing: 0.1em;
            color: rgba(255,255,255,0.55);
        }}

        .body {{ padding: 12px 40px 36px; position: relative; z-index: 1; }}

        section {{
            padding: 26px 0;
            border-bottom: 1px solid var(--line);
        }}

        section:last-child {{ border-bottom: none; }}

        .section-head {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 18px;
        }}

        .section-icon-wrap {{
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(38,198,218,0.2), rgba(33,150,243,0.2));
            border: 1px solid rgba(255,255,255,0.12);
            color: var(--teal);
        }}

        .section-number {{
            margin: 0;
            font-size: 11px;
            font-weight: 700;
            color: var(--teal);
            letter-spacing: 0.08em;
        }}

        .section-title {{
            margin: 2px 0 0;
            font-size: 21px;
            font-weight: 700;
        }}

        .panel {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 20px 22px;
            backdrop-filter: blur(8px);
        }}

        .overview-grid {{ display: grid; gap: 16px; }}

        .overview-item {{
            display: grid;
            grid-template-columns: 36px 120px 1fr;
            gap: 12px 16px;
            align-items: start;
        }}

        .overview-item .row-icon {{
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(38,198,218,0.15);
            color: var(--teal);
        }}

        .overview-item dt {{
            margin: 0;
            font-size: 13px;
            font-weight: 700;
            color: var(--muted);
            padding-top: 6px;
        }}

        .overview-item dd {{
            margin: 0;
            font-size: 15px;
            padding-top: 4px;
        }}

        .overview-item dd.lead {{
            color: var(--muted);
            line-height: 1.85;
        }}

        .icon-svg {{
            display: inline-flex;
            width: 22px;
            height: 22px;
            align-items: center;
            justify-content: center;
        }}

        .icon-svg svg {{ width: 100%; height: 100%; }}

        .section-icon {{ width: 26px; height: 26px; }}

        .item-list {{
            margin: 0;
            padding: 0;
            list-style: none;
        }}

        .item-list li {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 0;
            border-bottom: 1px solid var(--line);
            font-size: 15px;
        }}

        .item-list li:last-child {{ border-bottom: none; }}

        .item-icon {{
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            background: linear-gradient(135deg, rgba(38,198,218,0.18), rgba(33,150,243,0.12));
            color: var(--teal);
            border: 1px solid rgba(255,255,255,0.08);
        }}

        .item-text {{ flex: 1; }}

        .deliverables-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }}

        .deliverable-card {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 18px;
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 16px;
            font-size: 14px;
            font-weight: 600;
            backdrop-filter: blur(6px);
        }}

        .deliverable-icon {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--teal), var(--blue));
            color: #fff;
            flex-shrink: 0;
        }}

        .deliverable-icon .icon-svg {{ width: 24px; height: 24px; }}

        .requirements-note {{
            margin-top: 16px;
            padding: 16px 20px;
            font-size: 13px;
            color: var(--muted);
            background: rgba(33,150,243,0.1);
            border-right: 4px solid var(--blue);
            border-radius: 12px;
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }}

        .requirements-note .note-icon {{
            color: var(--blue);
            flex-shrink: 0;
            margin-top: 2px;
        }}

        .footer {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
            padding: 20px 40px 28px;
            font-size: 12px;
            color: rgba(255,255,255,0.45);
            border-top: 1px solid var(--line);
            background: rgba(0,0,0,0.15);
        }}

        .footer-brand {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: rgba(255,255,255,0.6);
        }}

        .footer-brand .icon-svg {{ width: 18px; height: 18px; color: var(--teal); }}

        @media (max-width: 720px) {{
            .hero {{
                grid-template-columns: 1fr;
                text-align: center;
            }}
            .hero-brand {{ flex-direction: column; }}
            .hero-visual {{ display: flex; justify-content: center; }}
            .hero-subtitle {{ max-width: none; }}
            .hero-badges {{ justify-content: center; }}
            .body, .hero, .footer {{ padding-left: 24px; padding-right: 24px; }}
            .overview-item {{ grid-template-columns: 36px 1fr; }}
            .overview-item dt {{ grid-column: 2; padding-top: 0; }}
            .overview-item dd {{ grid-column: 2; }}
            .deliverables-grid {{ grid-template-columns: 1fr; }}
            .app-shot {{ width: 170px; }}
        }}
    </style>
</head>
<body>

<div class="page">
    {decor_ref}

    <header class="hero">
        <div>
            <div class="hero-brand">
                <div class="logo-wrap">{logo_img}</div>
                <div>
                    <p class="cover-label">پروپوزال اجرایی · PROJECT OVERVIEW</p>
                    <h1>{PROJECT["name"]}</h1>
                    <p class="hero-tagline">{PROJECT["tagline"]}</p>
                    <p class="hero-subtitle">{PROJECT["subtitle"]}</p>
                </div>
            </div>
            <div class="hero-badges">
                <span class="badge">پیش‌آغاز پروژه</span>
                <span class="badge phase">{PROJECT["phase_badge"]}</span>
            </div>
        </div>
        {hero_visual}
    </header>

    <main class="body">

        <section id="overview">
            {section_heading("۰۱", "Project Overview", "section-overview")}
            <div class="panel">
                <dl class="overview-grid">
                    <div class="overview-item">
                        <div class="row-icon">{icon("car")}</div>
                        <dt>نام پروژه</dt>
                        <dd>{PROJECT["name"]} — {PROJECT["tagline"]}</dd>
                    </div>
                    <div class="overview-item">
                        <div class="row-icon">{icon("price")}</div>
                        <dt>هدف پروژه</dt>
                        <dd>{PROJECT["goal"]}</dd>
                    </div>
                    <div class="overview-item">
                        <div class="row-icon">{icon("reporting")}</div>
                        <dt>شرح کوتاه</dt>
                        <dd class="lead">{PROJECT["summary"]}</dd>
                    </div>
                </dl>
            </div>
        </section>

        <section id="objectives">
            {section_heading("۰۲", "Project Objectives", "section-objectives")}
            <div class="panel">
                {render_icon_list(OBJECTIVES)}
            </div>
        </section>

        <section id="scope">
            {section_heading("۰۳", "Scope of Work", "section-scope")}
            <div class="panel">
                {render_icon_list(SCOPE)}
            </div>
        </section>

        <section id="deliverables">
            {section_heading("۰۴", "Deliverables", "section-deliverables")}
            {render_deliverables(DELIVERABLES)}
        </section>

        <section id="dependencies">
            {section_heading("۰۵", "Dependencies & Requirements", "section-deps")}
            <div class="panel">
                {render_icon_list(DEPENDENCIES)}
            </div>
            <div class="requirements-note">
                <span class="note-icon">{icon("section-deps")}</span>
                <span>{DEPENDENCIES_NOTE}</span>
            </div>
        </section>

    </main>

    <footer class="footer">
        <span class="footer-brand">{icon("logo", "footer-logo")} {PROJECT["name"]} — Project Overview</span>
        <span>سند پیش‌آغاز · بدون گزارش وضعیت یا عملکرد</span>
    </footer>

</div>

</body>
</html>
"""


html = build_html()
OUTPUT_HTML.write_text(html, encoding="utf-8")

print(f"Sanje project overview created: {OUTPUT_HTML}")
print(f"Assets: {ASSETS_DIR}")
webbrowser.open(OUTPUT_HTML.as_uri())
