import calendar
from datetime import datetime
from typing import Union
from my_colors import get_yl, get_bl, get_ok


def f_w(day_num: int):
    return (day_num + 1) % 7


def printnn(s: str):
    print(s, end='')


def get_padded(n: Union[int, float], target: int = 3):
    padding = ''.join(' ' for _ in range(target - len(str(n))))
    return f"{padding}{n}"


def format_days(days: list[tuple[datetime, float]]) -> list[float]:
    ret: list[float] = []

    for i in range(1, calendar.monthrange(days[0][0].year, days[0][0].month)[1] + 1):
        if len(days) > 0 and i == days[0][0].day:
            ret.append(days[0][1])
            del days[0]
        else:
            ret.append(0)

    return ret


WEEK_DAYS_MARGIN = ' ' * 2
WEEK_DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'total']
WEEK_DAY_SIZE = ' ' * 2
HOURS_CNT_SIZE = ' ' * 4
MARGIN = ' ' * 2
BLANK = WEEK_DAY_SIZE + HOURS_CNT_SIZE + MARGIN


def print_calendar(first_day: datetime, days: list[tuple[datetime, float]], week_max: int):
    days = format_days(days)

    print(get_yl(WEEK_DAYS_MARGIN + f'{HOURS_CNT_SIZE}{MARGIN}'.join(WEEK_DAYS)))
    for i in range(f_w(first_day.weekday())):
        printnn(BLANK)
    w_total = 0
    for i in range(1, len(days) + 1):
        w_total += days[i - 1]
        printnn(f'{get_bl(get_padded(i, 2))}')
        if days[i - 1]:
            printnn(f':{get_padded(round(days[i - 1], 1))}{MARGIN}')
        else:
            printnn(f'{HOURS_CNT_SIZE}{MARGIN}')
        if not (i + f_w(first_day.weekday())) % 7 or i == len(days):
            if i == len(days):
                for _ in range(7 - (i + f_w(first_day.weekday())) % 7):
                    printnn(BLANK)

            printnn(f'{WEEK_DAY_SIZE}{get_ok(get_padded(round(w_total, 1)), w_total <= week_max)}')
            w_total = 0
            print()
