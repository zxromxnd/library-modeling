from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import mimetypes

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/'model'
DIST = ROOT/'node_modules/mermaid/dist'
PAGE = '''<!doctype html><html lang="uk"><meta charset="utf-8"><title>ER бібліотеки — перевірка рендера</title>
<style>body{font:16px Arial;margin:24px;background:white;color:#18202a}button{padding:10px 16px}#diagram svg{max-width:100%;height:auto}#status{margin:12px 0}</style>
<h1>ER-модель бібліотеки</h1><button id="save" disabled>Зберегти SVG</button><p id="status">Побудова діаграми…</p><div id="diagram"></div>
<script type="module">
import mermaid from '/dist/mermaid.esm.min.mjs';
try {
const source=await (await fetch('/source')).text();
const config=await (await fetch('/config')).json();
mermaid.initialize({...config,startOnLoad:false});
const {svg}=await mermaid.render('library-er',source);
document.querySelector('#diagram').innerHTML=svg;
document.querySelector('#status').textContent='Mermaid 12.0.0: діаграму побудовано з library-er.mmd.';
const button=document.querySelector('#save'); button.disabled=false;
button.onclick=async()=>{const response=await fetch('/save',{method:'POST',headers:{'Content-Type':'image/svg+xml'},body:svg});document.querySelector('#status').textContent=await response.text();};
} catch(error){document.querySelector('#status').textContent=String(error);}
</script></html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            data=PAGE.encode(); mime='text/html; charset=utf-8'
        elif self.path in ['/source','/config']:
            p=MODEL/('library-er.mmd' if self.path=='/source' else 'mermaid-config.json')
            data=p.read_bytes(); mime='text/plain; charset=utf-8' if self.path=='/source' else 'application/json'
        elif self.path.startswith('/dist/'):
            p=(DIST/self.path[6:]).resolve()
            if not p.is_relative_to(DIST.resolve()) or not p.is_file():
                self.send_error(404); return
            data=p.read_bytes(); mime='text/javascript' if p.suffix in ['.js','.mjs'] else (mimetypes.guess_type(p)[0] or 'application/octet-stream')
        else:
            self.send_error(404); return
        self.send_response(200); self.send_header('Content-Type',mime); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        if self.path!='/save': self.send_error(404); return
        size=int(self.headers.get('Content-Length','0'))
        if not 0<size<5000000: self.send_error(400); return
        data=self.rfile.read(size)
        if not data.lstrip().startswith(b'<svg'): self.send_error(400); return
        (MODEL/'library-er.svg').write_bytes(data)
        self.send_response(200); self.send_header('Content-Type','text/plain; charset=utf-8'); self.end_headers()
        self.wfile.write('SVG збережено у model/library-er.svg.'.encode())
    def log_message(self,*args): pass

ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
