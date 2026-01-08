from zoneinfo import ZoneInfo


EKB_TZ = ZoneInfo("Asia/Yekaterinburg")

def get_timezone(time_zone) -> ZoneInfo:
    return ZoneInfo(time_zone)