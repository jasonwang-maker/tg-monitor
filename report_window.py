import os
from datetime import datetime, timedelta, timezone


TZ_UTC8 = timezone(timedelta(hours=8))
REPORT_HOUR_UTC8 = int(os.environ.get("REPORT_HOUR_UTC8", "10"))


def get_report_window(now=None):
    """Return the fixed daily report window in UTC+8."""
    now = now or datetime.now(TZ_UTC8)
    report_end = now.replace(
        hour=REPORT_HOUR_UTC8,
        minute=0,
        second=0,
        microsecond=0,
    )
    if now < report_end:
        report_end -= timedelta(days=1)

    report_start = report_end.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) - timedelta(days=1)
    return report_start, report_end


def get_report_date_label(now=None):
    report_start, _ = get_report_window(now)
    return report_start.strftime("%Y-%m-%d")
