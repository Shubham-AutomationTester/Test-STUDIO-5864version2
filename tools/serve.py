#!/usr/bin/env python3
"""Serve the retained static QA site with real, repeated HTTP response headers.

Based on the v1 fixture server. Standard library only; synthetic QA data only.
Not a production application server. No uploads, command execution, or public logs.
"""
import argparse
import json
import mimetypes
import os
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit, quote

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (ROOT / 'docs').resolve()
LOCK = threading.Lock()
VERSION = '2.0.0'


def configuration():
    config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
    rules = json.loads((ROOT / 'qa/http-headers.json').read_text(encoding='utf-8'))
    for path, pairs in rules.items():
        if not path.startswith('/'):
            raise ValueError('Header paths must be site-relative absolute paths.')
        for name, value in pairs:
            if not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name):
                raise ValueError('Invalid header name in configured fixture.')
            if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
                raise ValueError('Control characters are forbidden in header values.')
            value.encode('latin-1')
    return config, rules


class Handler(BaseHTTPRequestHandler):
    server_version = 'Studio5864FixtureServer/2.0'
    sys_version = ''
    protocol_version = 'HTTP/1.1'

    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.serve(head=False)

    def do_HEAD(self):
        self.serve(head=True)

    def unsupported(self):
        self.respond(405, b'Only GET and HEAD are supported.\n',
                     'text/plain; charset=utf-8', [['Allow', 'GET, HEAD']], self.command == 'HEAD')

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = unsupported

    def serve(self, head):
        try:
            parsed = urlsplit(self.path)
            raw_path = unquote(parsed.path, errors='strict')
            if (not raw_path.startswith('/') or raw_path.startswith('//') or
                '\\' in raw_path or any(ord(ch) < 32 or ord(ch) == 127 for ch in raw_path)):
                raise ValueError('Invalid path')
            if any(part in ('.', '..') for part in raw_path.split('/')):
                self.respond(403, b'Forbidden path.\n', 'text/plain; charset=utf-8', [], head)
                return
            config, rules = configuration()
            prefix = config.get('base_path', '').rstrip('/')
            if raw_path == '/healthz':
                body = json.dumps({'status':'ok','site_version':VERSION,
                    'headers_served_by':'Python origin server',
                    'bot_meta_name':config['bot_meta_name'],
                    'crawl_execution':'Not run'}).encode('utf-8')
                self.respond(200, body, 'application/json; charset=utf-8', [], head)
                return
            local_path = raw_path
            status = 200
            redirect = None
            if prefix and raw_path == '/':
                status = 302
                redirect = prefix + '/'
            elif prefix and raw_path != '/robots.txt':
                if raw_path == prefix:
                    status = 301
                    redirect = prefix + '/'
                elif raw_path.startswith(prefix + '/'):
                    local_path = raw_path[len(prefix):]
                else:
                    status = 404
            content = b''
            content_type = 'text/html; charset=utf-8'
            pairs = []
            if status == 200:
                candidate = (PUBLIC / local_path.lstrip('/')).resolve()
                if not candidate.is_relative_to(PUBLIC):
                    status = 403
                elif any(part.startswith('.') for part in Path(local_path).parts if part not in ('/', '')):
                    status = 404
                else:
                    if candidate.is_dir():
                        if not local_path.endswith('/'):
                            status = 301
                            redirect = quote(raw_path + '/', safe='/')
                            if parsed.query:
                                redirect += '?' + quote(parsed.query, safe='=&;%:+,/?@')
                        else:
                            candidate = candidate / 'index.html'
                    if status == 200:
                        if not candidate.is_file():
                            status = 404
                        else:
                            content = candidate.read_bytes()
                            content_type = mimetypes.guess_type(str(candidate))[0] or 'application/octet-stream'
                            if content_type.startswith('text/') or content_type in ('application/javascript','application/json'):
                                content_type += '; charset=utf-8'
                            pairs = list(rules.get(local_path, []))
            if status in (403, 404):
                content = (PUBLIC / '404.html').read_bytes()
            if redirect:
                pairs.append(['Location', redirect])
            self.respond(status, content, content_type, pairs, head)
        except (ValueError, UnicodeError):
            self.respond(400, b'Invalid request path or fixture configuration.\n',
                         'text/plain; charset=utf-8', [], head)
        except OSError:
            self.respond(500, b'Fixture unavailable; inspect the deployment build.\n',
                         'text/plain; charset=utf-8', [], head)

    def respond(self, status, content, content_type, pairs, head):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.send_header('X-QA-Fixture-Version', VERSION)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Connection', 'close')
        self.close_connection = True
        for name, value in pairs:
            # One send_header call per pair. NEVER turn this list into a dict:
            # doing so would overwrite repeated X-Robots-Tag instances.
            self.send_header(name, value)
        self.end_headers()
        try:
            if not head and content:
                self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass
        event = {'event':'qa.fixture.request','timestamp':datetime.now(timezone.utc).isoformat(),
                 'method':self.command,'path':self.path,'status':status,
                 'user_agent':self.headers.get('User-Agent',''),
                 'x_robots_tag':[v for n,v in pairs if n.lower()=='x-robots-tag'],
                 'note':'Fixture access only; NOT a SearchStax pipeline outcome.'}
        line = json.dumps(event)
        with LOCK:
            if self.server.log_path:
                with self.server.log_path.open('a',encoding='utf-8') as output:
                    output.write(line + '\n')
            if not self.server.quiet and self.path != '/healthz':
                print(line, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT','8000')))
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--log', default='', help='Optional local JSONL path; default is stdout only.')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535.')
    if not (PUBLIC / 'index.html').is_file():
        parser.error('Missing static site; run python3 tools/build.py.')
    config, rules = configuration()
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    server.daemon_threads = True
    server.log_path = Path(args.log).resolve() if args.log else None
    if server.log_path:
        server.log_path.parent.mkdir(parents=True, exist_ok=True)
    server.quiet = args.quiet
    print(json.dumps({'event':'qa.fixture.started','version':VERSION,'bind':args.bind,
        'port':args.port,'header_paths':len(rules),'bot_meta_name':config['bot_meta_name']}),flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
