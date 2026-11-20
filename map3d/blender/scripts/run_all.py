"""Execute this file inside Blender 5.x; no Blender MCP or runtime network.

Console example:
    g={'PROJECT_ROOT':r'C:/Users/seabo/Documents/GitHub/our_honeymoon'}
    exec(open(g['PROJECT_ROOT']+'/map3d/blender/scripts/run_all.py',encoding='utf-8').read(),g)
"""
from pathlib import Path
PROJECT_ROOT=Path(globals().get('PROJECT_ROOT','C:/Users/seabo/Documents/GitHub/our_honeymoon')).resolve()
exec(compile((PROJECT_ROOT/'map3d/blender/scripts/common.py').read_text(encoding='utf-8'),'common.py','exec'),globals())


def run_all():
    # Shared globals are intentional; no reliance on __file__ in Text Editor.
    g={'PROJECT_ROOT':str(PROJECT_ROOT),'__name__':'__main__',
       'RENDER_PREVIEWS':globals().get('RENDER_PREVIEWS',True)}
    scripts=PROJECT_ROOT/'map3d/blender/scripts'
    for filename in ('build_terrain.py','build_vehicles.py','build_props.py','write_manifest.py'):
        path=scripts/filename
        if not path.is_file():
            raise RuntimeError('Missing build script: '+str(path))
        print('[run_all] Starting '+filename)
        try:
            with open(path,encoding='utf-8') as source:
                exec(source.read(),g)
        except Exception as exc:
            raise RuntimeError('Honeymoon build failed in %s: %s' % (filename,exc)) from exc
    print('[run_all] Complete: 19 GLBs, manifest, .blend and two look renders.')


run_all()
