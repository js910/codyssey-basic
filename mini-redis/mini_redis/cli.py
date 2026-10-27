"""실행: python main.py. 표준 입력 파이프도 지원한다."""
import json
import re
import shlex
import sys
from .store import Store

INTEGER_ERROR = '(error) ERR value is not an integer or out of range'
OOM = "(error) OOM command not allowed when used_memory > 'maxmemory'"

def parse_integer(value):
    """부호 있는 64비트 정수만 허용한다."""
    if re.fullmatch(r'[+-]?[0-9]+', value) is None:
        raise ValueError()
    number = int(value)
    if number < -(2 ** 63) or number > 2 ** 63 - 1:
        raise ValueError()
    return number

def quoted(value):
    return json.dumps(value, ensure_ascii=False)

class CLI:
    def __init__(self, store=None):
        self.store = store if store is not None else Store()

    def execute(self, line):
        """한 명령을 실행하고 출력 문자열을 반환한다. 종료는 None."""
        try:
            args = shlex.split(line)
        except ValueError:
            return '(error) ERR invalid quoting'
        if not args:
            return ''
        name = args[0]
        cmd = name.upper()
        if cmd in ('EXIT', 'QUIT') and len(args) == 1:
            return None
        # 필요 인자 수
        command_specs = (
            ('SET', 3),
            ('GET', 2),
            ('DEL', 2),
            ('EXISTS', 2),
            ('DBSIZE', 1),
            ('KEYS', 1),
            ('CONFIG', 4),
            ('INFO', 2),
            ('EXPIRE', 3),
            ('TTL', 2),
        )
        for command, expected_count in command_specs:
            if cmd == command:
                if len(args) != expected_count:
                    return "(error) ERR wrong number of arguments for '{}' command".format(name)
                break
        else:
            return "(error) ERR unknown command '{}'".format(name)
        db = self.store
        db.purge_expired()
        if cmd == 'SET':
            return 'OK' if db.set(args[1], args[2]) else OOM
        if cmd == 'GET':
            value = db.get(args[1])
            return '(nil)' if value is None else quoted(value)
        if cmd == 'DEL':
            result = db.delete(args[1])
        elif cmd == 'EXISTS':
            result = db.exists(args[1])
        elif cmd == 'DBSIZE':
            result = db.data.size()
        elif cmd == 'KEYS':
            rows = ['{}. {}'.format(i, quoted(key)) for i, key in enumerate(db.data.keys(), 1)]
            return '\n'.join(rows) if rows else '(empty array)'
        elif cmd == 'INFO':
            if args[1].lower() != 'memory':
                return '(error) ERR unsupported INFO section'
            return 'used_memory:{}\nmaxmemory:{}\nevicted_keys:{}'.format(db.used_memory, db.maxmemory, db.evicted_keys)
        elif cmd == 'CONFIG':
            if args[1].upper() != 'SET' or args[2].lower() != 'maxmemory':
                return '(error) ERR unsupported CONFIG option'
            try:
                amount = parse_integer(args[3])
                if amount < 0:
                    raise ValueError()
            except ValueError:
                return INTEGER_ERROR
            db.maxmemory = amount
            return 'OK'
        elif cmd == 'EXPIRE':
            try:
                seconds = parse_integer(args[2])
            except ValueError:
                return INTEGER_ERROR
            result = db.expire(args[1], seconds)
        else:
            result = db.ttl(args[1])
        return '(integer) {}'.format(result)

def main():
    cli = CLI()
    while True:
        try:
            line = input('mini-redis> ' if sys.stdin.isatty() else '')
        except (EOFError, KeyboardInterrupt):
            break
        output = cli.execute(line)
        if output is None:
            break
        if output:
            print(output)
