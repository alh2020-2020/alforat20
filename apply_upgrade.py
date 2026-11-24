#!/usr/bin/env python3
"""Run with python apply_upgrade.py /path/to/alforat20. Idempotent, no DB changes."""
from pathlib import Path
import shutil, sys, re
src=Path(__file__).resolve().parent
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
static=root/'static' if (root/'static'/'index.html').is_file() else root
for name in ('index.html','admin.html'):
    if not (static/name).is_file(): raise SystemExit(f'Missing {static/name}; no changes made')
for name in ('furat-v3.css','furat-v3.js'):
    target=static/name
    if (src/name).resolve()!=target.resolve(): shutil.copyfile(src/name,target)
for name in ('index.html','admin.html'):
    f=static/name; data=f.read_text(encoding='utf-8')
    if '/static/furat-v3.css' not in data:
        data=re.sub(r'</head>', '<link rel="stylesheet" href="/static/furat-v3.css?v=3.1"/>\n<script defer src="/static/furat-v3.js?v=3.1"></script>\n</head>',data,count=1,flags=re.I)
        f.write_text(data,encoding='utf-8')
sw=static/'sw.js'
if sw.is_file():
    data=sw.read_text(encoding='utf-8')
    if 'alfurat-shell-v3.1-visual' not in data:
        data=re.sub(r"(const\s+CACHE\s*=\s*)['\"][^'\"]+['\"]",r"\1'alfurat-shell-v3.1-visual'",data,count=1)
        sw.write_text(data,encoding='utf-8')
print('V3 applied: storefront and admin. Review git diff before committing.')
