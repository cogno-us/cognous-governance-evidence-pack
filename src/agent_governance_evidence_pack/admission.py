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


def admit_value(value):
    stack = [(value, 0)]
    nodes = size = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 100000 or depth > 32:
            raise ValueError('evidence structural budget exceeded')
        if type(item) is float and not math.isfinite(item):
            raise ValueError(f'[{INPUT_NON_FINITE_NUMBER}] nonfinite evidence number')
        if type(item) is str:
            if len(item) > 1048576:
                raise ValueError('evidence string budget exceeded')
            _refuse_surrogate(item)
            size += len(item.encode('utf-8'))
        elif type(item) is dict:
            if len(item) > 4096:
                raise ValueError('evidence field budget exceeded')
            stack.extend((v, depth + 1) for pair in item.items() for v in pair)
        elif type(item) in (list, tuple):
            if len(item) > 10000:
                raise ValueError('evidence collection budget exceeded')
            stack.extend((v, depth + 1) for v in item)
        if size > MAX_JSON_BYTES:
            raise ValueError('evidence byte budget exceeded')
    return value
