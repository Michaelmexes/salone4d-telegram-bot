"""
==========================================
SALONE 4D - Post Formatter
==========================================
Hot numbers ကို သတ်မှတ်ထားတဲ့ Telegram post format အဖြစ် ဖန်တီးပေးတဲ့ module
"""

from datetime import datetime
import config


RANK_EMOJIS = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']


def to_myanmar_digits(text: str) -> str:
    """Arabic digits ကို Myanmar digits (၀-၉) သို့ ပြောင်းသည်"""
    result = ''
    for ch in str(text):
        result += config.MYANMAR_DIGITS.get(ch, ch)
    return result


def format_number_spaced(number: str) -> str:
    """4 digit number ကို '4 ─ 8 ─ 2 ─ 3' ပုံစံ ပြောင်းသည် (Myanmar digits)"""
    digits = [to_myanmar_digits(d) for d in number]
    return ' ─ '.join(digits)


def get_myanmar_date(dt: datetime = None) -> str:
    """ဒီနေ့ ရက်စွဲကို မြန်မာဘာသာ format ဖြင့် ထုတ်ပေးသည်"""
    if dt is None:
        dt = datetime.now()

    day_name   = config.MYANMAR_DAYS.get(dt.strftime('%A'), dt.strftime('%A'))
    day_num    = to_myanmar_digits(str(dt.day).zfill(2))
    month_name = config.MYANMAR_MONTHS.get(dt.month, str(dt.month))
    year       = to_myanmar_digits(str(dt.year))

    return f"{day_name} │ {day_num} {month_name} {year}"


def build_post(hot_numbers: list[dict], dt: datetime = None) -> str:
    """
    Hot numbers list ကိုယူပြီး Telegram post message ဖန်တီးသည်

    Parameters:
        hot_numbers: [{'number': '4823', 'count': 45}, ...]
        dt: datetime object (None = today)

    Returns:
        Formatted message string
    """
    if dt is None:
        dt = datetime.now()

    myanmar_date = get_myanmar_date(dt)
    separator    = '────────────────────'

    # ── Header ──
    box_header = (
        """<pre>╔═══════════════════╗
║   🎯   SALONE4D   🎯  ║
╚═══════════════════╝</pre>"""
    )

    lines = [
        box_header,
        f'📅 {myanmar_date}',
        '',
        '💥 လက်ကီးဂဏန်းများ 💥',
        separator,
        '',
    ]

    # ── Number Rows ──
    for i, item in enumerate(hot_numbers):
        rank_emoji = RANK_EMOJIS[i] if i < len(RANK_EMOJIS) else f'{i+1}.'
        num_spaced = format_number_spaced(item['number'])
        major_mm   = to_myanmar_digits(str(item.get('major_count', 0)))
        minor_mm   = to_myanmar_digits(str(item.get('minor_count', 0)))
        lines.append(f'{rank_emoji} {num_spaced}  │ (ဆုကြီး {major_mm} ကြိမ် / ဆုသေး {minor_mm} ကြိမ်)')

    # ── Footer ──
    lines += [
        '',
        '💡 မှတ်ချက်:',
        '• ဆုကြီး = 1st, 2nd, 3rd Prize',
        '• ဆုသေး = Starter, Consolation',
        '',
        separator,
        'Base on Singapore Pools 4D',
        '📈 2023 ─ 2026 Data အပေါ် အခြေခံ၍ ဖေါ်ပြထားပါသည်။',
        '🍀 ကံကောင်းပါစေ! 🍀',
        getattr(config, 'TELEGRAM_CHANNEL', '@mexes30salone'),
    ]

    return '\n'.join(lines)


if __name__ == '__main__':
    # ── Test ──
    sample_hot = [
        {'number': '4823', 'count': 45},
        {'number': '7156', 'count': 42},
        {'number': '3091', 'count': 39},
        {'number': '6748', 'count': 37},
        {'number': '2365', 'count': 35},
    ]
    msg = build_post(sample_hot)
    print(msg)
