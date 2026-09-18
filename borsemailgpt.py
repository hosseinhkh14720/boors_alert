# -*- coding: utf-8 -*-

import sys
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from datetime import datetime


# =========================================================
# تنظیمات ایمیل
# =========================================================

SENDER_EMAIL = "hosseinkhorasani1@gmail.com"
APP_PASSWORD = "mhunyoyoityuumae"
RECEIVER_EMAIL = "hosseinkhorasani1@gmail.com"


# =========================================================
# TSETMC
# =========================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.tsetmc.com/",
}

BASE = "https://cdn.tsetmc.com/api"


# =========================================================
# سیگنال‌ها
# =========================================================

@dataclass
class Signal:
    key: str
    name: str
    weight: float
    score: float = 0.0
    note: str = ""


def create_signals():

    return [
        Signal("real_money_outflow", "خروج پول حقیقی", 2.0),
        Signal("big_stocks_drop", "افت شدید نمادها", 1.5),
        Signal("money_rotation", "چرخش پول", 1.5),
        Signal("high_value_supply", "ارزش معاملات", 1.0),

        # فعلاً در این نسخه فعال نشده‌اند
        Signal("support_break", "شکست حمایت", 1.0),
        Signal("negative_divergence", "واگرایی منفی RSI/MACD", 1.0),
        Signal("sharp_growth", "رشد شدید", 1.0),
        Signal("resistance_fail", "ضعف در مقاومت", 1.0),
    ]


# =========================================================
# دریافت اطلاعات
# =========================================================

def safe_get(url):

    try:

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if r.status_code == 200:
            return r.json()

        print("HTTP Error:", r.status_code)

        return None

    except Exception as e:

        print("Request Error:", e)

        return None


# =========================================================
# تحلیل بازار
# =========================================================

def analyze():

    signals = create_signals()

    # -----------------------------------------------------
    # Market Overview
    # -----------------------------------------------------

    overview = safe_get(
        f"{BASE}/MarketData/GetMarketOverview/1"
    ) or {}

    overview = (
        overview.get("marketOverview")
        or overview
    )

    # -----------------------------------------------------
    # Client Type
    # -----------------------------------------------------

    client_data = safe_get(
        f"{BASE}/ClientType/GetClientTypeAll"
    ) or {}

    items = (
        client_data.get("clientTypeAllDto")
        or client_data.get("clientTypeAll")
        or []
    )

    # -----------------------------------------------------
    # Market Watch
    # -----------------------------------------------------

    watch_url = (
        f"{BASE}/ClosingPrice/GetMarketWatch?market=0"
        "&paperTypes[0]=1"
        "&paperTypes[1]=2"
        "&paperTypes[2]=3"
        "&paperTypes[3]=4"
        "&paperTypes[4]=5"
        "&paperTypes[5]=6"
        "&paperTypes[6]=7"
        "&paperTypes[7]=8"
        "&paperTypes[8]=9"
        "&withBestLimits=false"
        "&hEven=0"
        "&RefID=0"
    )

    watch_data = safe_get(watch_url) or {}

    rows = (
        watch_data.get("marketwatch")
        or watch_data.get("marketWatch")
        or []
    )

    # =====================================================
    # 1. خروج پول حقیقی
    # =====================================================

    sig = next(
        s for s in signals
        if s.key == "real_money_outflow"
    )

    if items:

        buy_i = sum(
            float(
                i.get("buy_I_Volume")
                or i.get("Buy_I_Volume")
                or 0
            )
            for i in items
        )

        sell_i = sum(
            float(
                i.get("sell_I_Volume")
                or i.get("Sell_I_Volume")
                or 0
            )
            for i in items
        )

        net = buy_i - sell_i

        ratio = abs(net) / max(
            buy_i + sell_i,
            1
        )

        if net < 0:

            if ratio > 0.12:

                sig.score = 1.0
                sig.note = "خروج پول شدید"

            elif ratio > 0.05:

                sig.score = 0.7
                sig.note = "خروج پول متوسط"

            else:

                sig.score = 0.4
                sig.note = "خروج پول ضعیف"

        else:

            sig.score = 0.0
            sig.note = "ورود پول / تعادل"

    else:

        sig.score = 0.3
        sig.note = "داده موجود نیست"

    # =====================================================
    # 2. افت شدید نمادها
    # =====================================================

    sig = next(
        s for s in signals
        if s.key == "big_stocks_drop"
    )

    if rows:

        neg = sum(
            1
            for r in rows
            if float(
                r.get("pcp")
                or r.get("Pcp")
                or 0
            ) < -0.05
        )

        total = len(rows)

        neg_pct = (
            neg / total * 100
            if total
            else 0
        )

        if neg_pct >= 70:

            sig.score = 1.0

        elif neg_pct >= 55:

            sig.score = 0.7

        elif neg_pct >= 40:

            sig.score = 0.4

        else:

            sig.score = 0.1

        sig.note = (
            f"{neg_pct:.0f}% نمادها "
            f"افت شدید دارند"
        )

    else:

        sig.score = 0.3
        sig.note = "داده موجود نیست"

    # =====================================================
    # 3. چرخش پول
    # =====================================================

    sig = next(
        s for s in signals
        if s.key == "money_rotation"
    )

    idx = (
        overview.get("indexChange")
        or overview.get("IndexChange")
    )

    eq = (
        overview.get("indexEqualWeightedChange")
        or overview.get(
            "IndexEqualWeightedChange"
        )
    )

    if idx is not None and eq is not None:

        idx = float(idx)
        eq = float(eq)

        if eq > idx + 0.3:

            sig.score = 0.8

        elif eq > idx:

            sig.score = 0.5

        else:

            sig.score = 0.1

        sig.note = (
            f"کل: {idx:.1f} | "
            f"هم‌وزن: {eq:.1f}"
        )

    else:

        sig.score = 0.3
        sig.note = "داده موجود نیست"

    # =====================================================
    # 4. ارزش معاملات
    # =====================================================

    sig = next(
        s for s in signals
        if s.key == "high_value_supply"
    )

    if rows:

        total_value = sum(
            float(
                r.get("tval")
                or r.get("Tval")
                or 0
            )
            for r in rows
        )

        value_billion = total_value / 1e9

        if value_billion > 8000:

            sig.score = 0.8

        elif value_billion > 4000:

            sig.score = 0.5

        else:

            sig.score = 0.2

        sig.note = (
            f"{value_billion:.0f} میلیارد"
        )

    else:

        sig.score = 0.3
        sig.note = "داده موجود نیست"

    # =====================================================
    # سیگنال‌هایی که هنوز الگوریتمشان اضافه نشده
    # =====================================================

    for key in [
        "support_break",
        "negative_divergence",
        "sharp_growth",
        "resistance_fail"
    ]:

        sig = next(
            s for s in signals
            if s.key == key
        )

        sig.score = 0.0
        sig.note = "در نسخه بعدی فعال می‌شود"

    # =====================================================
    # امتیاز نهایی
    # =====================================================

    total = sum(
        s.score * s.weight
        for s in signals
    )

    # حداکثر واقعی وزن فعلی 6 است
    # برای تبدیل به مقیاس 0 تا 10:
    max_current_weight = 6.0

    total = (
        total / max_current_weight * 10
        if max_current_weight
        else 0
    )

    total = min(
        round(total, 1),
        10.0
    )

    # =====================================================
    # سطح ریسک
    # =====================================================

    if total <= 2:

        level = "عادی"
        icon = "🟢"

    elif total <= 4:

        level = "احتیاط"
        icon = "🟡"

    elif total <= 6:

        level = "احتمال اصلاح"
        icon = "🟠"

    elif total <= 8:

        level = "ریسک ریزش بالا"
        icon = "🔴"

    else:

        level = "هشدار جدی"
        icon = "🚨"

    return {
        "signals": signals,
        "score": total,
        "level": level,
        "icon": icon,
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    }


# =========================================================
# تعیین رنگ وضعیت
# =========================================================

def get_color(score):

    if score <= 2:
        return "#16a34a"

    elif score <= 4:
        return "#eab308"

    elif score <= 6:
        return "#f97316"

    elif score <= 8:
        return "#dc2626"

    else:
        return "#7f1d1d"


# =========================================================
# ساخت ایمیل گرافیکی
# =========================================================

def create_html(report):

    score = report["score"]
    level = report["level"]
    icon = report["icon"]
    color = get_color(score)

    signals_html = ""

    for s in report["signals"]:

        percentage = min(
            s.score / 1.0 * 100,
            100
        )

        if s.score >= 0.8:
            signal_icon = "🔴"

        elif s.score >= 0.5:
            signal_icon = "🟠"

        elif s.score >= 0.3:
            signal_icon = "🟡"

        else:
            signal_icon = "🟢"

        signals_html += f"""
        <tr>
            <td style="
                padding:12px;
                border-bottom:1px solid #eeeeee;
                font-weight:bold;
            ">
                {signal_icon} {s.name}
            </td>

            <td style="
                padding:12px;
                border-bottom:1px solid #eeeeee;
                text-align:center;
            ">
                {s.score:.1f}
            </td>

            <td style="
                padding:12px;
                border-bottom:1px solid #eeeeee;
                color:#555555;
            ">
                {s.note}
            </td>
        </tr>
        """

    # -----------------------------------------------------
    # عوامل مهم
    # -----------------------------------------------------

    important = sorted(
        report["signals"],
        key=lambda x: x.score,
        reverse=True
    )

    important_text = ""

    for s in important[:3]:

        if s.score >= 0.5:

            important_text += f"""
            <li style="margin-bottom:8px;">
                <b>{s.name}</b>:
                {s.note}
            </li>
            """

    if not important_text:

        important_text = """
        <li>در حال حاضر عامل هشدار بسیار قوی شناسایی نشده است.</li>
        """

    # -----------------------------------------------------
    # راهنمای شاخص‌ها
    # -----------------------------------------------------

    guide = """
    <div style="
        background:#f8fafc;
        padding:20px;
        border-radius:12px;
        margin-top:25px;
    ">

        <h2 style="margin-top:0;">
            📚 راهنمای خواندن گزارش
        </h2>

        <p>
        <b>🔴 خروج پول حقیقی:</b>
        اگر فروش حقیقی‌ها از خرید آنها بیشتر باشد،
        خروج پول حقیقی داریم. شدت بیشتر خروج،
        امتیاز ریسک بیشتری ایجاد می‌کند.
        </p>

        <p>
        <b>📉 افت شدید نمادها:</b>
        درصد نمادهایی را نشان می‌دهد که افت قابل‌توجه
        داشته‌اند. افزایش گسترده فشار فروش می‌تواند
        نشانه افزایش ریسک بازار باشد.
        </p>

        <p>
        <b>🔄 چرخش پول:</b>
        رفتار شاخص کل و شاخص هم‌وزن را با یکدیگر
        مقایسه می‌کند تا مشخص شود حرکت بازار تا چه
        اندازه‌ای در نمادهای بزرگ متمرکز شده است.
        </p>

        <p>
        <b>💰 ارزش معاملات:</b>
        میزان فعالیت معاملاتی بازار را نشان می‌دهد.
        ارزش معاملات بالا به‌تنهایی سیگنال مثبت یا
        منفی قطعی نیست و باید همراه سایر عوامل بررسی شود.
        </p>

        <p>
        <b>📐 شکست حمایت:</b>
        در نسخه بعدی، شکست حمایت‌های مهم شاخص
        بررسی خواهد شد. شکست حمایت می‌تواند نشانه
        افزایش فشار فروش باشد.
        </p>

        <p>
        <b>📊 RSI و MACD:</b>
        برای بررسی مومنتوم و قدرت روند استفاده می‌شوند.
        واگرایی منفی می‌تواند نشانه تضعیف روند باشد،
        اما به‌تنهایی به معنی قطعی بودن ریزش نیست.
        </p>

        <p>
        <b>🚀 رشد شدید:</b>
        رشد سریع شاخص در مدت کوتاه می‌تواند احتمال
        استراحت یا اصلاح را افزایش دهد؛ اما به‌تنهایی
        سیگنال فروش محسوب نمی‌شود.
        </p>

        <p>
        <b>🚧 مقاومت:</b>
        بررسی می‌کند شاخص در محدوده‌های مقاومتی مهم
        با افزایش عرضه یا ضعف مواجه شده است یا خیر.
        </p>

    </div>
    """

    # -----------------------------------------------------
    # HTML اصلی
    # -----------------------------------------------------

    html = f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:0;
        background:#f1f5f9;
        font-family:Arial,Tahoma,sans-serif;
        direction:rtl;
    ">

    <div style="
        max-width:700px;
        margin:25px auto;
        background:white;
        border-radius:16px;
        overflow:hidden;
        box-shadow:0 4px 20px rgba(0,0,0,0.08);
    ">

        <!-- Header -->

        <div style="
            background:{color};
            color:white;
            padding:25px;
            text-align:center;
        ">

            <div style="
                font-size:28px;
                font-weight:bold;
            ">
                {icon} هشدار بازار بورس تهران
            </div>

            <div style="
                margin-top:8px;
                font-size:14px;
            ">
                آخرین بررسی: {report["time"]}
            </div>

        </div>


        <!-- Score -->

        <div style="
            padding:25px;
            text-align:center;
        ">

            <div style="
                color:#64748b;
                font-size:16px;
            ">
                امتیاز ریسک بازار
            </div>

            <div style="
                font-size:52px;
                font-weight:bold;
                color:{color};
                margin:10px;
            ">
                {score:.1f}
                <span style="
                    font-size:20px;
                    color:#64748b;
                ">
                    / 10
                </span>
            </div>

            <div style="
                font-size:22px;
                font-weight:bold;
                color:{color};
            ">
                {icon} {level}
            </div>

            <!-- Risk bar -->

            <div style="
                margin:25px 0 5px 0;
                background:#e5e7eb;
                height:18px;
                border-radius:20px;
                overflow:hidden;
            ">

                <div style="
                    width:{score * 10}%;
                    height:18px;
                    background:{color};
                    border-radius:20px;
                ">
                </div>

            </div>

            <div style="
                display:flex;
                justify-content:space-between;
                color:#64748b;
                font-size:12px;
            ">

                <span>عادی</span>
                <span>احتیاط</span>
                <span>اصلاح</span>
                <span>ریسک بالا</span>
                <span>هشدار</span>

            </div>

        </div>


        <!-- Important factors -->

        <div style="
            margin:0 25px;
            padding:20px;
            background:#fff7ed;
            border-radius:12px;
        ">

            <h2 style="margin-top:0;">
                ⚠️ مهم‌ترین عوامل فعلی
            </h2>

            <ul style="
                margin-bottom:0;
                padding-right:20px;
            ">

                {important_text}

            </ul>

        </div>


        <!-- Table -->

        <div style="
            padding:25px;
        ">

            <h2>
                📊 جزئیات سیگنال‌ها
            </h2>

            <table style="
                width:100%;
                border-collapse:collapse;
                font-size:14px;
            ">

                <tr style="
                    background:#f8fafc;
                ">

                    <th style="padding:12px;">
                        سیگنال
                    </th>

                    <th style="padding:12px;">
                        امتیاز
                    </th>

                    <th style="padding:12px;">
                        وضعیت
                    </th>

                </tr>

                {signals_html}

            </table>

        </div>


        <!-- Guide -->

        <div style="padding:0 25px 25px 25px;">

            {guide}

        </div>


        <!-- Footer -->

        <div style="
            background:#f8fafc;
            padding:20px;
            text-align:center;
            color:#64748b;
            font-size:12px;
        ">

            این سیستم ابزار هشدار و تحلیل کمی است.
            امتیاز بالا به معنی قطعی بودن ریزش بازار نیست.
            تصمیم‌گیری باید با درنظر گرفتن سایر اطلاعات
            و شرایط بازار انجام شود.

        </div>

    </div>

    </body>
    </html>
    """

    return html


# =========================================================
# ارسال ایمیل
# =========================================================

def send_email(report):

    html_body = create_html(report)

    msg = MIMEMultipart("alternative")

    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg["Subject"] = (
        f"{report['icon']} بورس تهران | "
        f"{report['level']} | "
        f"{report['score']:.1f}/10"
    )

    # نسخه متنی برای ایمیل‌هایی که HTML را پشتیبانی نمی‌کنند
    plain_text = (
        f"هشدار بورس تهران\n\n"
        f"امتیاز ریسک: {report['score']:.1f}/10\n"
        f"وضعیت: {report['level']}\n"
        f"زمان: {report['time']}\n"
    )

    msg.attach(
        MIMEText(
            plain_text,
            "plain",
            "utf-8"
        )
    )

    msg.attach(
        MIMEText(
            html_body,
            "html",
            "utf-8"
        )
    )

    try:

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        )

        server.starttls()

        server.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        server.send_message(msg)

        server.quit()

        print("Email sent successfully")

        return True

    except Exception as e:

        print(
            "Email error:",
            e
        )

        return False


# =========================================================
# Main
# =========================================================

def main():

    print(
        "Starting Tehran Stock Market Alert..."
    )

    report = analyze()

    print(
        f"\nRisk Score: "
        f"{report['score']:.1f}/10"
    )

    print(
        f"Level: "
        f"{report['level']}"
    )

    print(
        "\nSending graphical email..."
    )

    send_email(report)


if __name__ == "__main__":

    main()