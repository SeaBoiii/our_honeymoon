# 3D Honeymoon Map — Asset Spec (Codex builds, Claude consumes)

This is the original low-poly brief. The current atlas retains its projection,
vehicle axes and node names. Its updated assets and measurements are in
`assets/manifest.json`. The new Hooker Valley cutaway has a 950 KB budget.

Codex builds every asset in the live Blender session through the Blender MCP and exports glTF binaries (`.glb`) into `map3d/assets/`. Claude writes the three.js web app in `map3d/` that loads these files. Don't write any web code.

## Art direction
- A stylised **low-poly diorama**, like a hand-made tabletop model of the South Island.
- Flat shading, few triangles, clean silhouettes.
- Colour comes from simple Principled BSDF **base colours** or vertex colours. No image textures, so the files stay small and self-contained.
- Palette:
  - Snow: `#F4F7F8`
  - Alpine rock: `#7D8A8F`
  - Tussock gold: `#C9A35A`
  - Pasture green: `#7FA65A`
  - Beech forest: `#3F6B3A`
  - Glacier-lake turquoise: `#3FB8C4`
  - Deep fiord water: `#1E5D73`
  - Road/asphalt: `#3A3F44`
  - Accent red (rental car): `#C8432F`
- Size budget: the terrain is under 6 MB, and each prop or vehicle is under 300 KB.

## Shared coordinate system (critical)
Blender is Z-up, and **1 Blender unit = 10 km**. Project longitude and latitude as follows:

```
X = (lon - 170.5) * 8.008      # east  (+)
Y = (lat + 44.0)  * 11.132     # north (+)   (lat is negative in NZ)
Z = elevation_m / 10000 * 5    # 5x vertical exaggeration (3724 m -> Z ≈ 1.862)
```
- The sea surface is at Z = 0.
- Export with glTF default settings: +Y up. Three.js will see x = east, y = up, z = south.
- Land follows the DEM, clamped to zero at/below sea level; no artificial minimum land height.

## Assets to produce

### 1. `terrain_south_island.glb` (one object named `Terrain`)
- **Coastline:** use a real South Island coastline in lon/lat. Natural Earth or similar public-domain data is fine, or digitise at least 250 points by hand. Include Stewart Island, Banks Peninsula and the Marlborough Sounds roughly. Fiordland's fiords can be simplified, but **Milford Sound must exist as an inlet** at about -44.60, 167.85.
- **Elevation:** bilinear sampling of `blender/data/dem_grid.json` for the South Island and Stewart Island. The LINZ 8 m source is sampled here at 0.025° latitude / 0.035° longitude (roughly 2.8 km), so peaks including Aoraki are smoothed; do not force synthetic summit heights. Null/sea samples are zero.
  - Lower road corridors toward the nearest segment's interpolated real elevation from `web_assets/routes.json` (`elev`, or DEM fallback): full effect within 400 m, smooth falloff to 1.2 km, never raise terrain above the DEM. Insert route vertices at at most 300 m spacing into the CDT.
- **Colours** by real height and slope (`Color` vertex attribute): pasture low, dry eastern tussock above 400 m, western beech below 900 m, steep high rock; late-winter snow above about 1300 m and on moderate slopes above 1100 m. Very steep high slopes remain exposed rock.
- **Lakes:** a separate child mesh named `Lakes`, flat at their real surface elevation, in turquoise. Include Tekapo, Pukaki, Ōhau, Wānaka, Hāwea, Wakatipu, Te Anau and Manapōuri.
  - Preserve recorded surface heights even if the coarse DEM median inside a schematic ring differs; print both for review. Cap beds at least 8 m below the surface. Water meshes remain under the `Lakes` parent for the consumer's water rasterisation.
- **Rivers:** optional, only if cheap.
- **Resolution:** roughly 120k–250k triangles total is fine.
- Also add a low, flat stylised **North Island southern tip** (Wellington area) named `NorthIslandHint`, for context only.

### 2. Vehicles
Each vehicle faces **+Y in Blender** (north, which becomes −Z in three.js), sits with its origin at the bottom centre, and is real-world proportioned at about 4.5 Blender units long. The app scales them.

| File | Root object | Notes |
|---|---|---|
| `car.glb` | `Car` | Compact SUV, accent red, with a ski rack on the roof |
| `coach.glb` | `Coach` | Tour coach, white with a teal stripe and big windows |
| `helicopter.glb` | `Helicopter` | Small tour helicopter. **Main rotor is a separate child object named `Rotor`** with its origin on the mast axis. Tail rotor is a child named `TailRotor`. |
| `boat.glb` | `Boat` | Small fiord cruise boat with 2 decks |
| `plane.glb` | `Plane` | Wide-body twin-jet airliner. Use a generic livery: no airline logos or names. |

### 3. Landmarks
These are props sized so their largest dimension is about 1 unit. Origin is at the bottom centre.

| File | Root object | What |
|---|---|---|
| `church_stone.glb` | `StoneChurch` | Small lakeside stone chapel with a bell tower (generic, Tekapo vibe) |
| `observatory.glb` | `Observatory` | Hilltop telescope dome |
| `lone_tree.glb` | `LoneTree` | A lone willow standing in shallow water on a small base (Wānaka) |
| `hot_tub.glb` | `HotTub` | A cedar hot tub for two, with a deck rail over a cliff edge (Queenstown Onsen) |
| `mosque.glb` | `Mosque` | Small generic mosque with one dome and one minaret |
| `city.glb` | `City` | A cluster of 10–15 low-poly buildings for a small city block (Christchurch) |
| `glowworm_cave.glb` | `Cave` | A rocky cave mouth with a tiny boat and blue-green glow points (an emissive material is OK) |
| `ski_lift.glb` | `SkiLift` | A chairlift with 3 towers and a cable on a snowy slope |
| `glacier_ice.glb` | `GlacierIce` | Blue-white glacier tongue chunk with crevasses |
| `pine_tree.glb` | `PineTree` | One conifer |
| `beech_tree.glb` | `BeechTree` | One rounded native-forest tree |
| `sheep.glb` | `Sheep` | One sheep |
| `pin.glb` | `Pin` | A stylised map pin with a heart cut-out, in accent red |

## Deliverables
1. Every `.glb` above, written to `map3d/assets/`.
2. `map3d/assets/manifest.json`: an array of `{ "file", "root", "triangles", "bbox_min", "bbox_max", "notes" }`, with bbox values in Blender units.
3. Save the working Blender file as `map3d/blender/honeymoon_map.blend`.
4. A look render of the terrain and of a lineup of the props, saved as PNGs in `map3d/blender/previews/`.
