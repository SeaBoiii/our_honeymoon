# Blender asset build

Run inside Blender 5.x (no runtime downloads or external Python packages):

```python
g = {'PROJECT_ROOT': r'C:/Users/seabo/Documents/GitHub/our_honeymoon'}
exec(open(g['PROJECT_ROOT'] + '/map3d/blender/scripts/run_all.py', encoding='utf-8').read(), g)
```

Individual `build_terrain.py`, `build_vehicles.py`, `build_props.py`, `build_valley.py`, and
`write_manifest.py` can also be executed with that globals dictionary. Each
loads `common.py` itself. The last script requires all 20 exported assets and
their original objects. `run_all.py` stops with the script name on any failure.

The build writes 20 GLBs and measured `manifest.json` into `map3d/assets`, updates
the browser copies in `map3d/web_assets`, and produces
`honeymoon_map.blend`, `previews/terrain.png`, and `previews/props_lineup.png`.
Preview renders use CPU Cycles and separate `HM_Preview_*` scenes. All source
geometry uses material colours, with smooth normals on glazing, airframes and rounded props.
To regenerate the website artwork, execute `render_atlas.py` in Blender with the same
globals, then run `python map3d/tools/build_atlas_art.py` and `sh build_site.sh`.

Every asset owns an `HM_*` collection. Rebuilding clears only that collection's
objects; objects also linked elsewhere are preserved. A conflicting required
object name outside the collection produces an error. Preview copies use
linked mesh data, and remain separate from the exported asset hierarchies.

`data/coastline.json` contains LINZ Topo50 mainland and lake boundaries with lake islands and small road shoulders, plus Natural Earth context. `data/dem_grid.json` supplies the sampled LINZ elevations.
Geography uses the projection and vertical exaggeration in `ASSET_SPEC.md`.

Terrain uses a higher-density South Island constrained Delaunay grid with an Aoraki sample,
lake-edge constraints, lowered beds and independent flat water meshes under
`Lakes`. The coarse `NorthIslandHint` and `StewartIsland` are land children.
The exporter omits terrain normals: the app's three.js r147 GLTFLoader enables
flat shading for missing normals, keeping shared indexed positions/colours
compact at roughly 8.6 MB. All other assets
include normal data. Runtime checks enforce file sizes, required exported node
names, triangle counts, origin placement, height anchors, and no textures.

The helicopter's direct child `Rotor` is in the local XY plane with local Z
as its spin axis; `TailRotor` is in local YZ with local X as its axis. Neither
pivot receives a baked rotation. Isotropic normalization preserves both.

Authoring checks, outside Blender:

```powershell
python -m py_compile map3d/blender/scripts/*.py
python map3d/blender/verify_offline.py
```

PowerShell may require enumerating the `.py` filenames for `py_compile`.
The offline verifier extracts only mathematical functions through AST; it
does not import bpy or pretend to run Blender. Blender 5.3 export API, CDT,
shader export, actual byte sizes, and visual results still require the live
execution. Optional exporter keywords are retried without the specific
rejected keyword. The final GLB validator deliberately stops if a fallback
would compromise the terrain flat-shading/size contract.

The five vehicles use shared representative length, width and height values in
`atlas/vehicle-dimensions.json`. The exported GLBs are in metres. The website
applies one common multiplier and changes the follow camera framing by vehicle.
Run `node map3d/tools/verify_fleet.cjs` to measure the exported vertices.
