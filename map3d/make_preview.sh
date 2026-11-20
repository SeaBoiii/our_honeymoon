#!/bin/sh
# Wraps index.html in the same skeleton the Artifact host adds, for local testing.
cd "$(dirname "$0")"
mkdir -p preview/assets
{ printf '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font:14px system-ui}[hidden]{display:none!important}</style></head><body>\n'; cat index.html; printf '\n</body></html>\n'; } > preview/index.html
mkdir -p preview/web_assets && cp -f web_assets/* preview/web_assets/ 2>/dev/null || true
echo "preview built"
