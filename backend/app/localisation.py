"""Request-scoped language, safe for concurrent visitors and worker threads."""
import json
import re
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

request_language: ContextVar[str] = ContextVar('request_language', default='en')


@lru_cache
def chinese_messages() -> dict[str, str]:
    return json.loads((Path(__file__).parent / 'locales/zh.json').read_text(encoding='utf-8'))


def tr(message: str, **values) -> str:
    translated = chinese_messages().get(message, message) if request_language.get() == 'zh' else message
    return translated.format(**values) if values else translated


def localise_error_detail(detail):
    if isinstance(detail, str):
        if detail.startswith('Value error, '): return 'Value error, ' + tr(detail[13:])
        if request_language.get() == 'zh':
            short = re.fullmatch(r'String should have at least (\d+) characters', detail)
            long = re.fullmatch(r'String should have at most (\d+) characters', detail)
            if short: return f'请填写至少 {short[1]} 个字符'
            if long: return f'内容不能超过 {long[1]} 个字符'
            if detail == 'Field required': return '请填写必填信息'
        return tr(detail)
    if isinstance(detail, list):
        return [{**item, 'msg': localise_error_detail(item.get('msg', ''))} if isinstance(item, dict) else item for item in detail]
    return detail
