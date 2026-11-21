/* Module 3 -- real-time textured temple in Three.js.
 *
 * Camera, model matrix, light and colour management are set to MATCH
 * raster3d.py / raytrace.py so `compare.py` is meaningful.
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";

const W = 512, H = 512;
const Q = new URLSearchParams(location.search);
const CMP = Q.get("cmp") === "1";            // ?cmp=1 : no mipmaps -> closest to raster3d.py (compare.py)
// data/ lives next to the repo root when served locally (/web/) and next to index.html on GitHub Pages
const DATA = location.pathname.includes("/web/") ? "../data/" : "./data/";
const canvas = document.getElementById("c");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;      // match srgb.py output encode

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);

// --- camera: exactly raster3d.render() defaults ---
const camera = new THREE.PerspectiveCamera(45, W / H, 1.0, 14.0);
camera.position.set(2.6, 2.0, 3.4);
const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 0.7, 0);
// In comparison mode, keep the camera identical to raster3d.py.
// Interactive orbit/zoom is available only in the normal viewer.
controls.enabled = !CMP;
controls.update();

// --- lights: ambient 0.15 + one directional along (0.4, 0.9, 0.6) ---
// Three.js r155+ uses physically-based light units: a Lambert surface returns albedo/PI * I * cos,
// so lights are multiplied by PI to match raster3d.py's  ambient + (1-ambient)*max(0, N.L).
scene.add(new THREE.AmbientLight(0xffffff, 0.15 * Math.PI));
const sun = new THREE.DirectionalLight(0xffffff, 0.85 * Math.PI);
sun.position.set(0.4, 0.9, 0.6);
scene.add(sun);

// --- parse a binary P6 PPM into a DataTexture (Three.js has no PPM loader) ---
async function loadPPMTexture(url) {
  const buf = new Uint8Array(await (await fetch(url)).arrayBuffer());
  let p = 0;
  const tok = () => {
    while (/\s/.test(String.fromCharCode(buf[p]))) p++;
    let s = "";
    while (!/\s/.test(String.fromCharCode(buf[p]))) s += String.fromCharCode(buf[p++]);
    return s;
  };
  if (tok() !== "P6") throw new Error("not a P6 PPM");
  const w = +tok(), h = +tok();
  tok(); p++;                                  // maxval + one whitespace
  const rgba = new Uint8Array(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    rgba[i * 4] = buf[p + i * 3];
    rgba[i * 4 + 1] = buf[p + i * 3 + 1];
    rgba[i * 4 + 2] = buf[p + i * 3 + 2];
    rgba[i * 4 + 3] = 255;
  }
  const tex = new THREE.DataTexture(rgba, w, h, THREE.RGBAFormat);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.flipY = true;                            // OBJ vt origin is bottom-left
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;   // my UVs run past 1 (metres / 8 m per tile)
  if (!CMP) {                                      // real-time default: trilinear mipmaps (Lab 2.4)
    tex.generateMipmaps = true;
    tex.minFilter = THREE.LinearMipmapLinearFilter;
  } else {
    tex.generateMipmaps = false;
    tex.minFilter = THREE.LinearFilter;
  }
  tex.magFilter = THREE.LinearFilter;
  tex.anisotropy = CMP ? 1 : 8;
  tex.needsUpdate = true;
  return tex;
}

let mesh;
Promise.all([
  new OBJLoader().loadAsync(DATA + "mymodel.obj"),
  loadPPMTexture(DATA + "mytexture.ppm"),
]).then(([obj, tex]) => {
  const mat = new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide });
  obj.traverse((c) => { if (c.isMesh) c.material = mat; });
  obj.scale.set(1.4, 1.4, 1.4);
  obj.rotation.y = THREE.MathUtils.degToRad(35);   // rot_y(35) in transforms.py
  mesh = obj;
  scene.add(obj);
  document.body.dataset.ready = "1";
  document.getElementById("tris").textContent = String(
    (() => { let n = 0; obj.traverse((c) => { if (c.isMesh) n += c.geometry.attributes.position.count / 3; }); return n; })());
}).catch((e) => {
  document.getElementById("wrap").insertAdjacentHTML("beforeend",
    `<p style="color:#f66">Could not load model/texture: ${e}. Serve the repo
     root (<code>npx serve .</code>) and open <code>/web/</code>.</p>`);
});

function animate() {
  requestAnimationFrame(animate);
  if (!CMP) controls.update();
  renderer.render(scene, camera);
}
animate();

document.getElementById("wire").addEventListener("click", () => {
  mesh?.traverse((c) => { if (c.isMesh) c.material.wireframe = !c.material.wireframe; });
});

document.getElementById("export").addEventListener("click", () => {
  if (!mesh) {
    alert("Model is still loading. Wait until the Candi Siwa model appears, then export again.");
    return;
  }
  // Always export the reference camera in comparison mode, regardless of prior UI state.
  if (CMP) {
    camera.position.set(2.6, 2.0, 3.4);
    controls.target.set(0, 0.7, 0);
    controls.update();
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);
  }
  renderer.render(scene, camera);
  const gl = renderer.getContext();
  const px = new Uint8Array(W * H * 4);
  gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px);
  const body = new Uint8Array(W * H * 3);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const s = ((H - 1 - y) * W + x) * 4, d = (y * W + x) * 3;
      body[d] = px[s]; body[d + 1] = px[s + 1]; body[d + 2] = px[s + 2];
    }
  const header = new TextEncoder().encode(`P6\n${W} ${H}\n255\n`);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([header, body]));
  a.download = "mymodel_three.ppm";
  a.click();
});
