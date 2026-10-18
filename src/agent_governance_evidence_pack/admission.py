"""Byte and syntax budgets for local artifact admission; never grants authority."""
import json
import math
from pathlib import Path

MAX_JSON_BYTES = 8 * 1024 * 1024

# Codes match the control plane strict loader family.
INPUT_NON_FINITE_NUMBER = 'input_json_non_finite_number'
INPUT_NOT_UTF8 = 'input_not_utf8'


def _refuse_surrogate(text):
    try:
        text.encode('utf-8')
    except UnicodeEncodeError:
        raise ValueError(f'[{INPUT_NOT_UTF8}] text contains a lone surrogate') from None


def read_bytes(path, limit=MAX_JSON_BYTES):
    with Path(path).open('rb') as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError('artifact byte budget exceeded')
    return value


def loads(value, limit=MAX_JSON_BYTES):
    if isinstance(value, str):
        value = value.encode('utf-8')
    if len(value) > limit:
        raise ValueError('JSON byte budget exceeded')
    depth = nodes = 0
    quoted = escaped = False
    for char in value.decode('utf-8'):
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            nodes += 1
            if depth > 32 or nodes > 100000:
                raise ValueError('JSON structural budget exceeded')
        elif char in ']}':
            depth -= 1
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = item
        return result
    def constant(value):
        raise ValueError(f'[{INPUT_NON_FINITE_NUMBER}] nonfinite JSON value')
    def number(text):
        result = float(text)
        if not math.isfinite(result):
            raise ValueError(f'[{INPUT_NON_FINITE_NUMBER}] number out of range')
        return result
    parsed = json.loads(value, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)
    _scan_text(parsed)
    return parsed


def _scan_text(value):
    stack = [value]
    while stack:
        item = stack.pop()
        if type(item) is str:
            _refuse_surrogate(item)
        elif type(item) is dict:
            for key, child in item.items():
                _refuse_surrogate(key)
                stack.append(child)
        elif type(item) is list:
            stack.extend(item)


def _plain(item):
    """Copy of an already budget-checked value made only of exact builtin types (subclasses cannot override what is checked)."""
    if isinstance(item, str):
        return str.__add__(item, "")
    if isinstance(item, float) and not isinstance(item, bool):
        return float.__add__(item, 0.0)
    if isinstance(item, dict):
        return {_plain(k): _plain(v) for k, v in dict.items(item)}
    if isinstance(item, (list, tuple)):
        values = [_plain(v) for v in (list.__iter__(item) if isinstance(item, list) else tuple.__iter__(item))]
        return tuple(values) if isinstance(item, tuple) else values
    return item


def admit_value(value):
    """Check structural, size and text budgets over every dict/list/str/float (subclasses included) and return builtin copies."""
    stack = [(value, 0)]
    nodes = size = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 100000 or depth > 32:
            raise ValueError('evidence structural budget exceeded')
        if isinstance(item, float) and not isinstance(item, bool) and not math.isfinite(float.__add__(item, 0.0)):
            raise ValueError(f'[{INPUT_NON_FINITE_NUMBER}] nonfinite evidence number')
        if isinstance(item, str):
            item = str.__add__(item, "")
            if len(item) > 1048576:
                raise ValueError('evidence string budget exceeded')
            _refuse_surrogate(item)
            size += len(item.encode('utf-8'))
        elif isinstance(item, dict):
            if dict.__len__(item) > 4096:
                raise ValueError('evidence field budget exceeded')
            stack.extend((v, depth + 1) for pair in dict.items(item) for v in pair)
        elif isinstance(item, (list, tuple)):
            if (list.__len__(item) if isinstance(item, list) else tuple.__len__(item)) > 10000:
                raise ValueError('evidence collection budget exceeded')
            stack.extend((v, depth + 1) for v in (list.__iter__(item) if isinstance(item, list) else tuple.__iter__(item)))
        if size > MAX_JSON_BYTES:
            raise ValueError('evidence byte budget exceeded')
    return _plain(value)
