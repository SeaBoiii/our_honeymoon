# Our Honeymoon — New Zealand's South Island

A 14-day self-drive honeymoon from Singapore to Aotearoa (24 Aug – 7 Sep 2027), planned with Claude Code and Codex. It includes a day-by-day itinerary with halal food and stays, plus an interactive 3D travel vlog of the whole trip.

**Live site:** https://seaboiii.github.io/our_honeymoon/

| Page | What it is |
|---|---|
| [Summary](https://seaboiii.github.io/our_honeymoon/) | Route map, where we sleep, and things to do, food and stays for every day, plus booking plan, halal guide and checklist |
| [Budget](https://seaboiii.github.io/our_honeymoon/budget/) | Combined airfare and budget, two spending forecasts, and prices for eight activities. Edits stay in the visitor’s browser. |
| [3D vlog](https://seaboiii.github.io/our_honeymoon/3d/) | Day-by-day visits to the South Island landmarks, with short travel scenes. |
| [3D vlog, Claude cut](https://seaboiii.github.io/our_honeymoon/claude-cut/) | The same trip with its own terrain treatment and the same detailed vehicles and landmarks, plus shadows, ripples on the sea and topographic contours |

The written journal opens at the day index. Five illustrated chapters feature Lake Tekapo, the Wānaka tree, Milford Sound, the Shotover Onsen and Franz Josef. Select a pin on the island map to visit its written itinerary. Places visited on several days offer a choice of dates.

Open a day at `/3d/#day-6` or go straight to an activity such as `/3d/#scene-mount-john`. Both editions pause at the selected activity and link back to its written day. The Wānaka tree and Onsen stops load orbitable Blender illustrations on demand. On phones, Play and Days stay beside the progress slider. More opens the activity picker, playback settings and links.
The primary map opens a common-scale vehicle lineup at `#place-fleet`, the SUV at `#place-suv` and the merino at `#place-merino`. Ten landmarks are available in the same orbit viewer. Open `#leg-te-anau` to board the lake cruise or `#leg-onsen-glenorchy` to follow the lakeside drive.

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

The 3D itinerary opens at the destinations. Each map’s **Full driving tour** link opens the 39-leg version at the selected day. Direct road and cruise links still open the complete leg. The original driving edition is also preserved at [archive/full-driving-tour](https://github.com/SeaBoiii/our_honeymoon/tree/archive/full-driving-tour).

## Rebuilding

```sh
python -I map3d/tools/fetch_routes.py          # road geometry (OSRM / OpenStreetMap)
python -I map3d/tools/fetch_elevation.py       # LINZ 8 m DEM grid + road elevations
python map3d/tools/prepare_shorelines.py <topo50-geojson-directory>  # uses Shapely 2
python map3d/tools/prepare_settlements.py       # offline town streets and footprints (Shapely, mapbox-vector-tile, curl)
python map3d/tools/prepare_shotover.py          # Shotover River centreline near Arthurs Point (Shapely)
cp map3d/web_assets/routes.json map3d-claude/web_assets/routes.json
python map3d/tools/verify_surface_routes.py     # Node and Shapely 2: every curved road and cruise
python -I map3d/tools/fill_dem_gaps.py
# then run the Blender scripts inside Blender as described in map3d/blender/README.md
node map3d/tools/verify_road_contact.cjs       # check pavement and vehicle contact against both terrain meshes
node map3d/tools/verify_fleet.cjs              # check every exported vehicle against its metre dimensions
python map3d/tools/build_atlas_art.py          # package the atlas plates (Pillow + NumPy)
blender -b --factory-startup --python-exit-code 1 -P map3d/blender/scripts/render_postcards.py
sh build_site.sh
# With docs served locally and playwright-core on the Node module path:
ATLAS_URL=http://127.0.0.1:8796 node map3d/tools/verify_playback.cjs
ATLAS_URL=http://127.0.0.1:8796 node map3d/tools/verify_journal.cjs
ATLAS_URL=http://127.0.0.1:8796 node map3d/tools/verify_budget.cjs
ATLAS_URL=http://127.0.0.1:8796 node map3d/tools/verify_activity_scenes.cjs
```

## Data and credits

- Road routes: © OpenStreetMap contributors (ODbL), routed with the OSRM demo server.
- Town streets and building footprints use © OpenStreetMap contributors under the ODbL, via [OpenFreeMap](https://openfreemap.org/) and [OpenMapTiles](https://openmaptiles.org/). The Blender roadside library can be rebuilt with `map3d/blender/scripts/build_roadside.py`. Rural planting and buildings are illustrative.
- The illustrated Christchurch approach uses runway endpoints from [Christchurch Airport, Appendix B](https://www.christchurchairport.co.nz/globalassets/about-us/sustainability/noise/noise-contours/2023-updated-christchurch-international-airport-noise-contours.pdf).
- Elevation: LINZ NZ 8 m DEM (CC BY 4.0), via OpenTopoData.
- The regional map follows the Shotover River centreline near Arthurs Point. Its channel width and the close-up evening landscapes are illustrative. [New Zealand Rivers and Names](https://services3.arcgis.com/fp1tibNcN9mbExhG/arcgis/rest/services/NZ_Rivers_and_Names_WFL1/FeatureServer/0)
- South Island coastline and eight lakes: [LINZ Topo50 mainland](https://data.linz.govt.nz/layer/50288-nz-island-polygons-topo-150k/) and [lake polygons](https://data.linz.govt.nz/layer/50293-nz-lake-polygons-topo-150k/), CC BY 4.0. Outer island context and world map: Natural Earth (public domain), world-atlas.
- Roads follow OpenStreetMap/OSRM centrelines with local corner rounding and distance-based speed. The Te Anau cruise links the town waterfront and the western cave landing. Milford and Akaroa turn in their channels. Each tour applies one common scale to the five regional vehicles. The itinerary uses 2.5 times the original vehicle scale and illustrative landmark spans in metres. The full driving tour keeps the original presentation. The source GLBs use the representative metre dimensions in `atlas/vehicle-dimensions.json`.
- 3D rendering: three.js.
- The research, hotel shortlist and halal notes were compiled in Nov 2026. Prices are estimates, and halal status and road conditions must be rechecked before travel.
