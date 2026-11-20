"""Package the Blender atlas plates and derive the paper contours from the LINZ grid."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

root = Path(__file__).resolve().parents[2]
art = root/'atlas'
for name in ('valley','chapel','cruise','helicopter'):
    plate = root/'map3d/preview/plates'/(name+'.png')
    Image.open(plate).save(art/(name+'.webp'), quality=90, method=4)

dem = json.loads((root/'map3d/blender/data/dem_grid.json').read_text(encoding='utf8'))
grid = np.array(dem['elev'], dtype=float).reshape(dem['nlat'], dem['nlon'])
# One patch of the Southern Alps, oriented north-up. Isolines at 120 m.
row = round((-43.7-dem['lat0'])/dem['dlat'])
col = round((170.1-dem['lon0'])/dem['dlon'])
patch = np.nan_to_num(grid[row-12:row+13, col-19:col+20])[::-1]
height = Image.fromarray(patch.astype('float32')).resize((850,540), Image.Resampling.BICUBIC)
bands = np.floor(np.asarray(height)/120)
edges = (bands != np.roll(bands,1,0)) | (bands != np.roll(bands,1,1))
edges[0,:]=False
edges[:,0]=False
alpha = Image.fromarray(edges.astype('uint8')*68).filter(ImageFilter.GaussianBlur(.35))
ink = Image.new('RGBA',height.size,(58,100,87))
ink.putalpha(alpha)
ink.save(art/'contours.png', optimize=True)
