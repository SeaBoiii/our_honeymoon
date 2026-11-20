# Our Honeymoon — New Zealand's South Island

A 14-day self-drive honeymoon from Singapore to Aotearoa (24 Aug – 7 Sep 2027), planned with Claude Code and Codex. It includes a day-by-day itinerary with halal food and stays, plus an interactive 3D travel vlog of the whole trip.

**Live site:** https://seaboiii.github.io/our_honeymoon/

| Page | What it is |
|---|---|
| [Summary](https://seaboiii.github.io/our_honeymoon/) | Route map, where we sleep, and things to do, food and stays for every day, plus booking plan, halal guide and checklist |
| [3D vlog](https://seaboiii.github.io/our_honeymoon/3d/) | A globe flight from Singapore, then the 14-day loop on real roads. Codex built the 3D assets. |
| [3D vlog, Claude cut](https://seaboiii.github.io/our_honeymoon/claude-cut/) | The same trip with Claude-built terrain, vehicles and landmarks, plus shadows, ripples on the sea and topographic contours |

Deep links open a 3D page at a given day, e.g. `/3d/#day-6` for Milford Sound.
The primary map also opens four orbitable Blender miniatures via `#place-valley`,
`#place-chapel`, `#place-cruise` and `#place-helicopter`. Each connects to its travel day.

## Repository layout

```
honeymoon.html         summary page source
atlas/                 shared web styles, Blender illustrations, fonts and three.js r147
itinerary.md           the day-by-day plan as text
map3d/                 3D vlog (Codex assets)
  index.html             three.js app
  web_assets/            models (GLB wrapped in JSON), road routes, globe texture
  assets/                original GLB exports
  blender/scripts/       Codex's Blender build scripts (run inside Blender)
  blender/data/          coastline, lakes and elevation grid
  tools/                 data pipeline: road routes, elevation, coastline, globe texture, route map
map3d-claude/          3D vlog, Claude cut (same layout; Claude's Blender scripts in blender/)
build_site.sh          assembles the GitHub Pages site into docs/
docs/                  the published site (generated, do not edit by hand)
```

## Rebuilding

```sh
python -I map3d/tools/fetch_routes.py          # road geometry (OSRM / OpenStreetMap)
python -I map3d/tools/fetch_elevation.py       # LINZ 8 m DEM grid + road elevations
python -I map3d/tools/make_coastline.py <land-10m.json> <ne_10m_lakes.geojson>
python -I map3d/tools/fit_coast_to_roads.py    # make sure every road sits on land
python -I map3d/tools/fill_dem_gaps.py
# then run the Blender scripts inside Blender as described in map3d/blender/README.md
python map3d/tools/build_atlas_art.py          # package the atlas plates (Pillow + NumPy)
sh build_site.sh
```

## Data and credits

- Road routes: © OpenStreetMap contributors (ODbL), routed with the OSRM demo server.
- Elevation: LINZ NZ 8 m DEM (CC BY 4.0), via OpenTopoData.
- Coastline, lakes and world map: Natural Earth (public domain), world-atlas.
- 3D rendering: three.js.
- The research, hotel shortlist and halal notes were compiled in Nov 2026. Prices are estimates, and halal status and road conditions must be rechecked before travel.
