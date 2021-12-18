#! /usr/bin/env python3

import cgi, json, sys
from argparse import ArgumentParser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from traceback import print_exc
from urllib.parse import parse_qs


APP_DIR      = Path(__file__).parent.resolve()
DOCUMENT_DIR = APP_DIR / 'root'
DIC_DIR      = (list(APP_DIR.glob('**/aq_dic_large')) +
                list(APP_DIR.glob('**/aq_dic')))[0]
CONFIG_PATH  = APP_DIR / 'config.json'
SYNTHE_ARGS  = { 'type', 'bas', 'spd', 'vol', 'pit', 'acc', 'lmd', 'fsc' }

try:
    CONFIG = json.loads(CONFIG_PATH.read_text())
except:
    CONFIG = {}


sys.path.insert(0, str(next(APP_DIR.glob('ext/build/lib.*'))))
import aqtk

class RequestHandler(SimpleHTTPRequestHandler):
    kanji2koe = None

    def __init__(self, request, client_address, server):
        super(RequestHandler, self).__init__(request, client_address, server,
                                             directory=str(DOCUMENT_DIR))

    def do_GET(self):
        path = self.path.partition('?')[0].partition('#')[0]
        if path == 'check_licenses':
            self.handle_check_licenses()
        else:
            super(RequestHandler, self).do_GET()

    def do_POST(self):
        path = self.path.partition('?')[0].partition('#')[0]
        if path == '/talk':
            self.handle_talk()
        else:
            self.send_error(404)

    def success_response(self, body, content_type, headers={}):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(200, 'OK')
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def handle_check_licenses(self):
        body = json.dumps({ k:bool(v) for k, v in CONFIG.items() })
        self.success_response(body, 'application/json; charset=UTF-8')

    def handle_talk(self):
        try:
            mime, mime_opts = cgi.parse_header(self.headers['Content-Type'])
            if mime.lower() == 'multipart/form-data':
                mime_opts = { k:v.encode('utf-8') for k, v in mime_opts.items() }
                # Workaround for older python.
                mime_opts['CONTENT-LENGTH'] = self.headers['Content-Length']
                values = cgi.parse_multipart(self.rfile, mime_opts)
            else:
                body   = self.rfile.read(int(self.headers['Content-Length']))
                values = parse_qs(body.decode('utf-8', errors='ignore'))
            values = { k:v[0] for k, v in values.items() }

            text = values.pop('text')
            if not int(values.pop('native', 0)):
                text = self.kanji2koe.convert(text)
            wav = aqtk.synthe(text, **{ k:int(v) for k, v in values.items() if v })
        except:
            print_exc()
            text = self.kanji2koe.convert('このぶんしょうは、しゃべれません')
            wav = aqtk.synthe(text)

        fname = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        headers = { 'Content-Disposition': 'attachment; filename="yukkuri-%s.wav"' % fname }
        self.success_response(wav, 'audio/wav', headers)


def main():
    if CONFIG.get('usr_key'):
        aqtk.set_license_key('aquestalk_usr', CONFIG['usr_key'])
    if CONFIG.get('dev_key'):
        aqtk.set_license_key('aquestalk_dev', CONFIG['dev_key'])
    if CONFIG.get('k2k_key'):
        aqtk.set_license_key('kanji2koe_dev', CONFIG['k2k_key'])
    RequestHandler.kanji2koe = aqtk.AqKanji2Koe(str(DIC_DIR))

    parser = ArgumentParser(description='Yukkuri voice server')
    parser.add_argument('-b', '--bind', type=str, default='127.0.0.1', help='IP address to listen')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port number')
    args = parser.parse_args()
    httpd = HTTPServer((args.bind, args.port), RequestHandler)
    httpd.serve_forever()


if __name__ == '__main__':
  main()
