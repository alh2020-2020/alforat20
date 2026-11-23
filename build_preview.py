"""Build a self-contained catalog preview from the initial product seed.

The preview is read-only: the full app, admin and orders require the Python server.
"""
from __future__ import annotations

import ast
import base64
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'


def default_settings() -> dict:
    tree = ast.parse((ROOT / 'app.py').read_text(encoding='utf8'))
    init = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'init_db')
    assignment = next(n for n in init.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'defaults' for t in n.targets))
    defaults = ast.literal_eval(assignment.value)
    defaults['app_url'] = 'https://play.google.com/store/apps/details?id=com.forat.storeapp'
    return defaults


def uri(path: Path) -> str:
    kind = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    if path.suffix == '.svg':
        kind = 'image/svg+xml'
    return f'data:{kind};base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


def build() -> Path:
    html = (STATIC / 'index.html').read_text(encoding='utf8')
    css = (STATIC / 'styles.css').read_text(encoding='utf8') + '\n' + (STATIC / 'catalog.css').read_text(encoding='utf8')
    app_js = (STATIC / 'app.js').read_text(encoding='utf8')
    catalog_js = (STATIC / 'catalog.js').read_text(encoding='utf8')
    assets = {'/static/' + str(p.relative_to(STATIC)): uri(p) for p in (STATIC / 'assets').rglob('*') if p.is_file()}
    for file_path, data_uri in assets.items():
        html = html.replace('"' + file_path + '"', '"' + data_uri + '"')
    html = html.replace('href="/admin"', 'href="#preview-note"')
    html = html.replace('<link rel="manifest" href="/manifest.webmanifest" />', '')
    html = html.replace('<link rel="stylesheet" href="/static/styles.css?v=3" />', '')
    html = html.replace('<link rel="stylesheet" href="/static/catalog.css?v=3" />', '<style>' + css + '''
.preview-note{padding:12px 20px;background:#0b2550;color:#e6f5d9;text-align:center;font-size:14px;line-height:1.7}
.preview-note strong{color:#c5ff62}
</style>''')
    html = html.replace('<script src="/static/app.js?v=3" defer></script>', '')
    html = html.replace('<script src="/static/catalog.js?v=3" defer></script>', '')
    icons = (STATIC / 'assets' / 'icons.svg').read_text(encoding='utf8').replace('<svg ', '<svg style="display:none" aria-hidden="true" ', 1)
    html = html.replace('<body>', '<body>\n' + icons + '\n<div id="preview-note" class="preview-note"><strong>معاينة فورية للكتالوج</strong> — تعديل المنتجات واستقبال الطلبات يعملان عند تشغيل خادم الموقع.</div>', 1)
    seed = json.loads((ROOT / 'data' / 'catalog_seed.json').read_text(encoding='utf8'))
    social = json.loads((ROOT / 'data' / 'social_seed.json').read_text(encoding='utf8'))
    data = {'settings':default_settings(),'products':seed,'videos':[],'social_posts':social,'demo':True}
    bootstrap = '''<script>
window.__assetMap=__ASSET_MAP__;
const originalFetch=window.fetch.bind(window);
window.fetch=(input,options)=>String(input)==='/api/catalog'
  ? Promise.resolve(new Response(JSON.stringify(__STORE_DATA__),{status:200,headers:{'Content-Type':'application/json'}}))
  : originalFetch(input,options);
</script>'''.replace('__ASSET_MAP__',json.dumps(assets,ensure_ascii=False)).replace('__STORE_DATA__',json.dumps(data,ensure_ascii=False))
    html = html.replace('</body>', bootstrap + '\n<script>' + app_js + '</script>\n<script>' + catalog_js + '''
$('#checkout-btn').onclick=()=>toast('هذه معاينة فقط. لتسجيل الطلب شغّل خادم المتجر.');
</script></body>''')
    html = html.replace('/static/assets/icons.svg#','#')
    target = ROOT / 'معاينة_فورية.html'
    target.write_text(html,encoding='utf8')
    return target


if __name__ == '__main__':
    output = build()
    print(f'Built {output.name}: {output.stat().st_size:,} bytes')
