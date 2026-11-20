#!/bin/sh
# Assemble the GitHub Pages site in docs/ from the page sources.
#   docs/             summary page (honeymoon.html)
#   docs/3d/          3D travel vlog, Codex-built assets (map3d/)
#   docs/claude-cut/  3D travel vlog, Claude-built assets (map3d-claude/)
# The page sources are written as claude.ai artifacts (no <html>/<head> skeleton, links
# between artifacts), so this wraps each page and rewrites those links to relative paths.
set -e
cd "$(dirname "$0")"
SUMMARY='https://claude.ai/artifact/U9TV22y5gkKzKZtULwJ8xp'
CODEX3D='https://claude.ai/artifact/ByqvjSzbFcSGSWeyZomBoV'
CLAUDE3D='https://claude.ai/artifact/Rt9SjT2ckTEaW6AEVvWGua'

wrap() { # $1 source page, $2 output, $3 path prefix back to the summary
  {
    printf '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    printf '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    printf '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui}img{max-width:100%%}[hidden]{display:none!important}</style>\n'
    sed -e "s#$CODEX3D\##${3}3d/\##g" -e "s#$CODEX3D#${3}3d/#g" \
        -e "s#$CLAUDE3D\##${3}claude-cut/\##g" -e "s#$CLAUDE3D#${3}claude-cut/#g" \
        -e "s#$SUMMARY#${3}#g" \
        -e 's# target="_blank" rel="noopener"##g' "$1"
    printf '\n</html>\n'
  } > "$2"
}

rm -rf docs
mkdir -p docs/3d/web_assets docs/claude-cut/web_assets
wrap honeymoon.html docs/index.html ''
wrap map3d/index.html docs/3d/index.html '../'
wrap map3d-claude/index.html docs/claude-cut/index.html '../'
cp map3d/web_assets/* docs/3d/web_assets/
cp map3d-claude/web_assets/* docs/claude-cut/web_assets/
touch docs/.nojekyll
# no artifact links may survive
if grep -rl 'claude.ai/artifact' docs/*.html docs/*/index.html; then echo 'artifact link left in site' >&2; exit 1; fi
echo "site built: $(du -sh docs | cut -f1)"
