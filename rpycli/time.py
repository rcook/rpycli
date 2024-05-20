from datetime import timedelta


def parse_duration(s):
    if s == "N/A":
        return None

    match tuple(map(float, s.split(":"))):
        case (hours, minutes, seconds):
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        case (minutes, seconds):
            return timedelta(minutes=minutes, seconds=seconds)
        case (seconds,):
            return timedelta(seconds=seconds)
