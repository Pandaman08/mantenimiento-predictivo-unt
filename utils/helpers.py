from datetime import datetime
import re


def format_date(value, fmt: str = '%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    return value.strftime(fmt)


def clean_column_name(name):
    if name is None:
        return ''
    clean = re.sub(r'[^0-9a-zA-Z_\s]', '', str(name)).strip().lower()
    return re.sub(r'\s+', '_', clean)


def normalize_text(value):
    if value is None:
        return ''
    return str(value).strip()
