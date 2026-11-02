"""Validate local synthetic CSV/JSON imports without modifying them."""
import argparse
import csv
import io
import json
import math
from pathlib import Path
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 10000


def parse_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('Non-finite constant')
    return json.loads(text, object_pairs_hook=unique, parse_constant=reject)


def read_text(path):
    with Path(path).open('rb') as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('File exceeds 2 MiB')
    return raw.decode('utf-8-sig')


def validate_schema(schema):
    if not isinstance(schema, dict) or set(schema) != {'version', 'fields'} or type(schema['version']) is not int or schema['version'] != 1:
        raise ValueError('Expected version 1 and fields')
    fields = schema['fields']
    if not isinstance(fields, dict) or not 1 <= len(fields) <= 100:
        raise ValueError('Expected 1–100 fields')
    for name, rule in fields.items():
        if not isinstance(name, str) or not 1 <= len(name) <= 128:
            raise ValueError('Invalid field name')
        if not isinstance(rule, dict) or set(rule) != {'type', 'required'}:
            raise ValueError('Expected type and required')
        if not isinstance(rule['type'], str) or rule['type'] not in {'string', 'integer', 'number', 'boolean'} or type(rule['required']) is not bool:
            raise ValueError('Invalid type or required flag')
    return schema


def load_rows(text, format):
    if format == 'json':
        rows = parse_json(text)
        if not isinstance(rows, list):
            raise ValueError('Expected JSON array')
    elif format == 'csv':
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        header = next(reader, None)
        if not header or any(not h for h in header) or len(set(header)) != len(header):
            raise ValueError('Expected distinct nonempty CSV headers')
        rows = []
        for values in reader:
            if len(values) != len(header):
                raise ValueError('CSV width mismatch')
            rows.append(dict(zip(header, values)))
            if len(rows) > MAX_ROWS:
                raise ValueError('Too many rows')
    else:
        raise ValueError('Unsupported format')
    if len(rows) > MAX_ROWS or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Expected at most 10000 object rows')
    return rows


def matches(value, kind, format):
    if format == 'csv' and kind != 'string':
        if value != value.strip():
            return False
        try:
            value = parse_json(value)
        except (ValueError, RecursionError):
            return False
    if kind == 'string':
        return isinstance(value, str)
    if kind == 'integer':
        return type(value) is int
    if kind == 'number':
        return type(value) is int or (type(value) is float and math.isfinite(value))
    return type(value) is bool


def check(rows, schema, format):
    validate_schema(schema)
    errors, error_count, invalid_rows = [], 0, 0
    for number, row in enumerate(rows, 1):
        row_errors = []
        for name, rule in schema['fields'].items():
            missing = name not in row or row[name] is None or (format == 'csv' and row[name] == '')
            if missing:
                if rule['required']:
                    row_errors.append({'row': number, 'field': name, 'code': 'required'})
            elif not matches(row[name], rule['type'], format):
                row_errors.append({'row': number, 'field': name, 'code': 'type', 'expected': rule['type']})
        invalid_rows += bool(row_errors)
        error_count += len(row_errors)
        errors.extend(row_errors[:max(0, 1000-len(errors))])
    return {'version': 1, 'valid': not error_count, 'rows': len(rows), 'invalid_rows': invalid_rows,
            'error_count': error_count, 'errors': errors, 'errors_truncated': error_count > len(errors)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schema')
    parser.add_argument('input')
    parser.add_argument('--format', required=True, choices=['csv', 'json'])
    args = parser.parse_args(argv)
    try:
        schema = validate_schema(parse_json(read_text(args.schema)))
        result = check(load_rows(read_text(args.input), args.format), schema, args.format)
    except (ValueError, OSError, RecursionError, csv.Error):
        print(json.dumps({'error': 'Invalid schema/input, unsupported encoding, size limit, or unreadable file'}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
