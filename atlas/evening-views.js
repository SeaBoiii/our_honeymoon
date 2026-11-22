/* The local Blender scenes share geometry with the printed evening chapters.
   Load them on first visit; the regional camera remains usable during the load. */
function createEveningViews(canvas, mapControls) {
  const shots = {
    'onsen-sunset': {
      file: 'onsen',
      target: [-0.76, 1.1, 0.44],
      eye: [-1.52, 3.8, 7.8],
    },
    'wanaka-tree': {
      file: 'wanaka',
      target: [-0.52, 0.95, 0.55],
      eye: [0.25, 2.05, 6.8],
    },
  };
  const cache = new Map();
  const world = new THREE.Scene();
  world.add(new THREE.HemisphereLight('#fbe1d6', '#8b8598', 0.95));
  const sun = new THREE.DirectionalLight('#ffb482', 1.22);
  sun.position.set(-6, 3.6, -1.5);
  world.add(sun);
  const fill = new THREE.DirectionalLight('#c4caff', 0.43);
  fill.position.set(3, 5, 4);
  world.add(fill);
  const sky = makeEveningSky();
  sky.visible = true;
  world.add(sky);
  const camera = new THREE.PerspectiveCamera(43, 1, 0.014, 700);
  const orbit = new THREE.OrbitControls(camera, canvas);
  orbit.enabled = false;
  orbit.enablePan = false;
  orbit.minDistance = 2;
  orbit.maxDistance = 14;
  orbit.minPolarAngle = 0.35;
  orbit.maxPolarAngle = Math.PI * 0.482;
  let shown = null,
    active = null;
  let lastRequested;

  function load(shot) {
    if (cache.has(shot.file)) return;
    cache.set(shot.file, null);
    new THREE.GLTFLoader().load(
      '../atlas/' + shot.file + '-evening.glb',
      (asset) => {
        cache.set(shot.file, asset.scene);
      },
      undefined,
      () => cache.delete(shot.file),
    );
  }

  canvas.addEventListener('keydown', (event) => {
    if (!orbit.enabled) return;
    const v = camera.position.clone().sub(orbit.target);
    const s = new THREE.Spherical().setFromVector3(v);
    switch (event.key) {
      case 'ArrowLeft':
        s.theta -= 0.12;
        break;
      case 'ArrowRight':
        s.theta += 0.12;
        break;
      case 'ArrowUp':
        s.phi -= 0.1;
        break;
      case 'ArrowDown':
        s.phi += 0.1;
        break;
      case '+':
      case '=':
        s.radius *= 0.88;
        break;
      case '-':
        s.radius /= 0.88;
        break;
      default:
        return;
    }
    event.preventDefault();
    s.radius = THREE.MathUtils.clamp(
      s.radius,
      orbit.minDistance,
      orbit.maxDistance,
    );
    s.phi = THREE.MathUtils.clamp(
      s.phi,
      orbit.minPolarAngle,
      orbit.maxPolarAngle,
    );
    camera.position.setFromSpherical(s).add(orbit.target);
    orbit.update();
  });
  return function render(renderer, id, playing, dt) {
    const shot = shots[id];
    if (shot && id !== lastRequested) load(shot);
    lastRequested = id;
    const model = shot && cache.get(shot.file);
    if (!model) {
      if (active) {
        orbit.enabled = false;
        mapControls.enabled = true;
        active = null;
        delete canvas.dataset.evening;
      }
      return false;
    }
    const aspect = canvas.clientWidth / canvas.clientHeight;
    if (camera.aspect !== aspect) {
      if (active === id) {
        const scale =
          Math.max(1, 0.76 / aspect) / Math.max(1, 0.76 / camera.aspect);
        camera.position
          .sub(orbit.target)
          .multiplyScalar(scale)
          .add(orbit.target);
      }
      camera.aspect = aspect;
      camera.updateProjectionMatrix();
    }
    if (active !== id) {
      if (shown) world.remove(shown);
      shown = model;
      world.add(model);
      orbit.target.fromArray(shot.target);
      camera.position.fromArray(shot.eye);
      camera.position
        .sub(orbit.target)
        .multiplyScalar(Math.max(1, 0.76 / aspect))
        .add(orbit.target);
      camera.lookAt(orbit.target);
      orbit.enabled = true;
      mapControls.enabled = false;
      active = id;
      canvas.dataset.evening = id;
    }
    if (playing) {
      const offset = camera.position.clone().sub(orbit.target);
      offset.applyAxisAngle(world.up, dt * 0.022);
      camera.position.copy(orbit.target).add(offset);
    }
    orbit.update();
    sky.position.copy(camera.position);
    renderer.render(world, camera);
    return true;
  };
}
