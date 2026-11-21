# Laporan Modul 3 — Transformasi 3D, Proyeksi & Real-Time
Subjek: **Candi Siwa, Prambanan** (lanjutan Modul 1 foto + Modul 2 denah `myplan.json`)
Nama / NIM: `________`

> **Cara membaca laporan ini.** Semua angka di bawah dihasilkan oleh kode di repo ini (log lengkap di `out/logs/`).
> Baris bertanda **[ISI SENDIRI]** adalah bagian yang menurut modul harus berupa pekerjaan/penjelasan Anda sendiri
> (hitung tangan, diagnosis dengan kata-kata sendiri, viva, URL, hasil di browser). Saya sengaja tidak mengarangnya.

## 0. Toolchain (Lab 1.1)
| Item | Nilai |
|---|---|
| OS (tempat angka di laporan ini dihasilkan) | Linux (Ubuntu 24) sandbox — **ganti dengan mesin Anda (Windows 11?)** |
| Python / NumPy / Pillow | 3.12.3 / 2.5.4 / 13.0.0 |
| Node | v22.23.5 |
| Browser + Three.js | **[ISI SENDIRI]** `chrome://version` + `three@0.160.0` (dimuat dari jsdelivr oleh `web/index.html`) |
| Tanggal | 20 November 2026 |

Jalankan ulang di mesin Anda: `python --version`, `python -c "import numpy;print(numpy.__version__)"`, lalu salin ke README.

## A1. Model & telusuran satu-vertex (Lab 1)

**Model.** `data/mymodel.obj` dibangkitkan `make_siwa.py` dari denah **Modul 2** (`data/myplan.json` = salinan `myplan.json`):
41 kotak, **984 vertex, 492 segitiga** (≥ 200 ✔), 6 sisi × 4 vertex per kotak dengan **UV per-sisi nyata**
(UV = meter / 8 m per tile → kerapatan texel seragam, nilai UV sampai ±4.25 sehingga texture memakai *repeat/wrap*).
Texture `data/mytexture.ppm` 256×256 prosedural (susunan balok batu + pita relief), deterministik, tanpa lisensi pihak ketiga.
Isi model: teras luar 34 m, platform dalam, badan candi, 6 tingkat atap + finial, 4 tangga (4 anak tangga), 3 relung (Durga/Agastya/Ganesha),
4 stupa sudut. Tinggi hanyalah **estimasi blockout (~43 m)**, bukan survei; ukuran denah mengikuti Modul 2 (alas 34 m = angka terpublikasi).
Skala `S = 1.5/47` sehingga tingginya 1,37 unit → kamera/cahaya/matriks yang sama dengan `raster3d.py`, `raytrace.py`, `web/viewer.js`.

**Telusuran vertex indeks 2** (sudut timur-laut puncak teras luar, plan (34 m, 1,5 m, 34 m)) — `python trace_vertex.py`:

| Space | Nilai |
|---|---|
| object | (0.5425, 0.0479, −0.5425, 1) |
| world `M p`, `M = Ry(35°)·S(1.4)` | (0.1865, 0.0670, −1.0579, 1) |
| view `V(Mp)`, `V = lookAt((2.6,2,3.4)→(0,0.7,0))` | (0.7908, −0.3944, −5.3529, 1) → di depan kamera, jarak 5.353 |
| clip `P V M p`, `P = persp(45°,1,1,14)` | (1.9091, −0.9521, 4.0225, **5.3529**) → `w = −z_eye` ✔ |
| NDC (`/w`) | (0.3567, −0.1779, 0.7515) |
| screen 512×512 | x = 347.30, y = 301.53, depth 0.7515 |

**Telusuran kolom.** `M`: kolom 1 (+x) → (1.1468, 0, −0.803) = sumbu x model diputar 35° dan diperbesar 1,4× di bidang xz;
kolom 2 (+y) → (0, 1.4, 0) tak berputar, hanya diskala; kolom 3 (+z) → (0.803, 0, 1.1468); kolom 4 (origin) → (0,0,0,1) tidak bergeser.
`V`: kolom 4 = (0, −0.6698, −4.6767, 1) = origin world dilihat dari kamera (4.68 di depan, 0.67 di bawah sumbu pandang);
cek `V·(posisi kamera) = (0,0,0,1)` ✔ (`out/logs/trace_vertex.txt`).

**Hitung tangan `Mp` dan `V(Mp)`** — **[ISI SENDIRI]** Kerjakan di kertas lalu cocokkan ke ≥3 desimal. Langkah pemeriksaan:
`c=cos35°=0.819152, s=sin35°=0.573576`; `x_w = 1.4(c·x + s·z) = 1.4·0.5426·(0.8192−0.5736)=0.1865`;
`z_w = 1.4(−s·x + c·z) = 1.4·0.5426·(−0.5736−0.8192) = −1.0579`; `y_w = 1.4·0.0479 = 0.0670`.
Lalu `x_v = 0.7944·0.1865 + (−0.6075)(−1.0579) = 0.7908` dst.

**Bacaan wajib (Lab 1.5)** — **[ISI SENDIRI, ½ halaman]** pilih satu (WebGLRenderer Three.js / learnopengl "Coordinate Systems") dan tulis *satu hal yang
berbeda dari `transforms.py` dan alasannya.* Titik awal yang benar secara teknis: Three.js memakai matriks **column-major** yang disimpan sebagai
array datar, serta `modelViewMatrix` dihitung di CPU lalu dikalikan `projectionMatrix` di vertex shader (`gl_Position = projectionMatrix * modelViewMatrix * position`), sementara `project()` kita mengalikan `P@V@M` sekali di NumPy.

### Refleksi kasus (Lab 1.6)
Sumber: Nathan Reed, *Depth Precision Visualized*, blog pribadi 3 Juli 2015 (terbit ulang di NVIDIA Developer Blog sebagai *Visualizing Depth Precision*, `reedbeta.com/blog/depth-precision-visualized`); reverse-Z diberi asal-usul pada Lapidous & Jiao, SIGGRAPH '99, dan dipopulerkan ulang sekitar 2012 (Persson, Pettineo, Kemen) menurut tulisan Reed.

**(a) Peremukan 1/z dengan angka saya** (`python depth_budget.py`). Depth tersimpan `d = a/z + b`. Dengan **near = 1, far = 14** (kamera saya),
**53,8 %** seluruh kode depth habis di **1 meter pertama** setelah near dan 60,9 % di 10 % pertama jarak near–far. Pada buffer int24 selisih terkecil yang masih terbedakan
adalah 1,2·10⁻⁷ m pada jarak 1,5 m tetapi 1,1·10⁻⁵ m pada jarak 13,9 m (≈ 85× lebih kasar). Untuk pembanding gaya Reed (near 0,01; far 1000): **99,0 %** kode di meter pertama, dan di jarak 990 m selisih terkecil ≈ **5,8 m**.
Karena near saya 1 (bukan 0,01), scene saya tidak z-fight; `broken_scene.py --bug zfight` memakai near = 10⁻³ untuk memunculkannya.

**(b) Tabel empat konvensi** (OpenGL vs Direct3D). **[VERIFIKASI SENDIRI dengan sumber yang Anda kutip]**
| Konvensi | OpenGL | Direct3D | Yang dipatok `transforms.py` |
|---|---|---|---|
| Handedness (world/view) | right-handed, kamera menghadap −z | left-handed, +z masuk layar | right-handed, −z |
| Matriks/vektor | column-vector, `M @ p`; memori column-major | row-vector, `p @ M`; secara historis row-major | column-vector, `M @ p` |
| Rentang NDC z | [−1, 1] | [0, 1] | [−1, 1] |
| Origin UV / citra | (0,0) kiri-bawah | (0,0) kiri-atas | OBJ kiri-bawah, dibalik **sekali** di `load_obj(flip_v=True)` |

**(c) Scene uji yang membongkar bug.** Presisi depth: dua quad coplanar besar yang jauh (near kecil) → pita berkelap-kelip, itulah `broken_scene.py --bug zfight`.
Handedness terbalik: model **asimetris** + teks/tanda arah. *Candi Siwa saya cocok:* ketiga relung (Durga di utara, Agastya di selatan, Ganesha di barat) ada, tetapi **tidak ada relung di timur** (sisi tangga masuk). Jika dunia tercermin, relung berpindah sisi dan tangga masuk berpindah ke barat — terlihat langsung.

**(d) Satu perubahan yang menangkap pembalikan handedness otomatis:** `t_mymodel` di `tests.py` sudah menegaskan **492/492 segitiga CCW-outward**; cermin membalik winding semua segitiga sehingga test gagal. Tambahan yang saya usulkan: asersi bahwa vertex tangga timur (plan x = 34 m) setelah `M` dan `V` jatuh di sisi kanan layar bila kamera berada di timur-selatan.

**Catatan penting dari bacaan Reed yang menyentuh repo ini:** Reed menunjukkan bahwa **reverse-Z tidak membantu pada rentang NDC z [−1, 1] gaya OpenGL**, karena pemetaan awal ke [−1,1] sudah menghancurkan presisi float di separuh jauh.
`transforms.perspective` kita memakai [−1,1], jadi untuk Lab ekstensi *reverse-Z* di `raster3d.py` Anda harus **pindah ke depth [0,1]** (seperti `gl.clipControl` / Direct3D), bukan sekadar membalik near/far.

## A2. Pipeline from-scratch & kecocokan referensi (Lab 2.1)
- **E1–E5 (angka, dari `tests.py`):** (2,3,4) → (3,3,−3) → (2,2); urutan terbalik → (5,3,−3); dualitas kamera +x ≡ model −x identik;
  `z=−n → −1`, `z=−f → +1`, `z=−3 → 0.5`; `u` perspective-correct di tengah = **0.1** (naif 0.5); depth barycentric = **0.625**.
- **`python tests.py` → `ALL CHECKS PASSED` (14 ok)** — 13 bawaan + 1 baru `t_mymodel` (≥200 segitiga, UV nyata, 492/492 CCW-outward, raster≈raytrace, frame referensi sendiri `ref/mymodel_ref.ppm`).
- **Candi Siwa vs ray tracer** (512×512, `out/logs`): **PSNR 56,5 dB, SSIM 1,000, mean|diff| 0,0, max|diff| 45.** Residual = beberapa pixel tepi siluet dan sambungan mortar antar balok (aturan tepi/top-left rasteriser vs sinar), bukan bagian dalam.
  (Pada model cadangan `pusaka_model.obj`: 76,9 dB; pada model saya lebih rendah karena 492 segitiga dengan banyak tepi tajam dan tekstur mortar kontras tinggi — *bukan* bug transformasi, karena diff hanya 22 pixel dari 16.384 di 128×128.)
- **Frame vs `ref/temple_ref.ppm`:** referensi itu milik **model cadangan**; `tests.py` mencocokkannya byte-identik. Untuk model saya referensinya `ref/mymodel_ref.ppm` (dibangkitkan test pertama; *commit file ini*).
- Gambar: `report/fig_three_renders.png` (raster | raytrace | selisih ×6).

## A3. Diagnosis & perbaikan (Lab 2.2)
Jalankan `python broken_scene.py --bug <nama>` dan **tulis diagnosis Anda dulu dengan kata sendiri** sebelum membaca perbaikannya. Angka bukti di model **saya**:

| Bug | Bukti (dari keluaran) | Satu perubahan | SSIM sebelum→sesudah | Pitfall §12 |
|---|---|---|---|---|
| inside-out | render menampilkan dinding dalam; selisih depth rata-rata 0,027 NDC; 8865 vs 8636 fragmen | winding dibalik kembali (atau matikan culling) | **0,979** (halus!) | 12.6 |
| z-fighting | pita campur-warna; **2852 pixel** salah vs referensi float; hanya **184** setelah `near=1` | `near` 10⁻³ → 1,0 | **0,779** (PSNR 16,7 dB) | 12.2 |
| stretched | baris matriks model: (2.52, 0, 0.8) / (0, 0.7, 0) vs benar (1.15, 0, 0.8) / (0, 1.4, 0) | tulis rantai `T·R·S` benar, buang skala non-uniform | **0,503** (PSNR 12,9 dB) | 12.1 |

Gambar: `report/fig_bug_inside-out.png`, `fig_bug_zfight.png`, `fig_bug_stretched.png`.
- **Catatan jujur 1:** pada model saya SSIM inside-out hanya 0,979, jauh lebih "halus" daripada kasus cadangan (≈0,79), karena candi saya konveks berundak dan tekstur seragam — mata sulit melihatnya. *Citra depth* yang membongkarnya: selisih depth rata-rata ≠ 0. Pelajaran: SSIM tinggi tidak membuktikan bebas bug.
- **Catatan jujur 2:** bug `stretched` di `broken_scene.py` sebenarnya menyuntikkan skala non-uniform `diag(2.2, 0.5, 1)`; membalik urutan `S·R` murni dengan **skala seragam** menghasilkan gambar identik. Urutan baru berbahaya bila ada translasi (`T·R ≠ R·T`, E1: (3,3,−3) vs (5,3,−3)) atau skala non-uniform. Tulis ini di diagnosis Anda.
- **Histogram depth untuk z-fighting:** **[ISI SENDIRI]** — `broken_scene.py` mencetak hitungan pixel, tetapi belum membuat histogram. Tambahkan 5 baris `np.histogram` dari depth `bad` vs `fixed` dan tempel gambarnya.

## A4. Raster vs ray-trace (Lab 3.3)
**Prediksi tertulis (ditulis di `bench.py` SEBELUM dijalankan):** `t_raster / t_raytrace ≈ 0,2` pada 256×256; shadow/reflection lebih baik di **ray tracing**.
**Terukur (`out/logs/bench.txt`, 492 segitiga):**
| Resolusi | raster ms | raytrace ms | RT + shadow ms | raster/RT |
|---|---:|---:|---:|---:|
| 64×64 | 54 | 92 | 1619 | 0,58 |
| 128×128 | 44 | 309 | 2081 | 0,14 |
| 256×256 | 50 | 1641 | 3965 | **0,03** |

**Rekonsiliasi.** Prediksi 0,2 meleset ≈ 7× (raster lebih cepat dari dugaan). Alasan: biaya rasteriser NumPy hampir **konstan terhadap jumlah pixel** (dominan overhead per-segitiga ≈ 492 loop; bounding box kecil), sedangkan ray tracer tanpa BVH
adalah **O(pixel × segitiga)** — naik 4× per kali resolusi dua kali lipat (92→309→1641 ms). Shadow ray menambah satu lintasan segitiga penuh lagi (≈ 2,4× di 256²). Hard shadow menggelapkan 643 pixel (1,0 % frame): `report/fig_shadow.png`.
**Keputusan.** *Viewer real-time:* **rasterisation** (GPU, frame time datar terhadap resolusi, 60 fps; shadow lewat shadow map).
*Beauty shot marketing:* **ray/path tracing** (shadow, refleksi, GI fisik; waktu per-frame tidak penting).
**Keterbatasan (≥2, satu baris):** (1) pada 10⁶+ segitiga tanpa BVH ray tracer tidak layak — dengan BVH/RT core pilihan **berbalik** ke RT untuk viewer; (2) bila butuh refleksi/GI dinamis dan GPU punya RT core (DXR/OptiX), hibrid raster+RT menggantikan raster murni; (3) target 4K/120 fps menghukum RT lebih berat daripada raster.
**WebGL vs NumPy (pengukuran awal, sebelum kamera dikunci).** Export pertama menghasilkan PSNR **17,1 dB**, SSIM **0,686**, mean |diff| **8,9**, max |diff| **203** pada 512×512. Export ulang setelah interaksi/refresh menghasilkan 15,5 dB, SSIM 0,466, mean |diff| 12,2, max 204. Ini menunjukkan export sebelumnya tidak reproducible; angka tersebut belum boleh dianggap hasil final. Perbaikan di `web/viewer.js` mengunci kamera referensi pada `?cmp=1` dan menonaktifkan orbit/zoom dalam mode perbandingan. **[JALANKAN ULANG setelah memakai versi perbaikan; masukkan angka final yang benar-benar terukur.]**

## A5. Texture & sampling (Lab 2.3, 2.4)
- `python perspective_demo.py`: `u` titik tengah **naif 0,50 vs perspective-correct 0,10**; SSIM(naif, benar) = **0,631**, PSNR 9,9 dB; `report/fig_perspective.png` (naif "berenang").
- **Mipmap** (piramida 4 level 256→32, box gamma-correct), kamera jauh 128×128 vs kebenaran 4×4 supersample (`python mip_eval.py`):
  | Texture | Tanpa mip | Dengan mip |
  |---|---|---|
  | `mytexture.ppm` (milik saya) | 36,72 dB / SSIM 0,9624 / flicker 0,054 | 36,95 dB / 0,9644 / 0,032 |
  | `relief.ppm` (frekuensi tinggi) | 34,41 dB / 0,9215 / flicker **0,300** | **37,41 dB / 0,9639 / 0,027** |
  Jujur: pada texture saya efeknya **kecil** (garis mortar hanya 2 px; energi frekuensi tinggi 93→90) — tidak ada aliasing besar untuk dihilangkan. Pada texture frekuensi tinggi (`relief.ppm`) mip menaikkan PSNR 3 dB dan menurunkan flicker ≈ 11×. Pakai gambar `report/fig_mip_siwa_tex.png` dan laporkan kedua angka itu apa adanya.

## Lab 2.5 — perbaikan berbasis pitfall (`python fixes.py`)
Ketiganya dikerjakan: **back-face culling** membuang **260 / 492 (53 %)** segitiga, gambar identik, waktu 95 → 64 ms;
**presisi depth** (tabel int24 / float32 / reverse-Z di near 0,01 far 1000: selisih terkecil pada 100 m = 5,96·10⁻² / 5,96·10⁻² / 7,28·10⁻⁶ m);
**matriks normal** `M⁻ᵀ`: dengan `scale(3,1,1)` `n'·t' = 8,0` (tidak tegak lurus) vs `0,0` memakai `M⁻ᵀ`.

## A6. Reproducibility & viva
- **Transkrip clone-bersih (simulasi lokal):** `out/logs/clean_copy_transcript.txt` — salinan bersih tanpa `data/*.obj|ppm` → `make_model.py` → `make_siwa.py` → `tests.py` **ALL CHECKS PASSED** → raster/raytrace/compare 56,3 dB. Model dan referensi dibangkitkan **identik byte** (hash md5 sama). Baris Verified: `Python 3.12.3 NumPy 2.5.4 on 2026-11-20`. *Ini bukan clone dari GitHub; ulangi dengan `git clone` di mesin Anda (`bash repro.sh`).*
- **URL GitHub Pages:** **[ISI SENDIRI]** `https://<user>.github.io/<repo>/` (workflow `.github/workflows/pages.yml` sudah disiapkan).
- **Siap viva:** jalankan `python tests.py`; orbit viewer; jelaskan satu commit; jawab "mengapa urutan/handedness/near ini?" (urutan `P·V·M` kanan-ke-kiri karena column-vector; right-handed −z karena konvensi OpenGL/Three.js; near = 1 karena near kecil menghabiskan presisi 1/z) dan "bagaimana jika target Direct3D / canvas 4K?" (transpose + `p@M`, balik handedness, NDC z [0,1], origin UV atas-kiri; 4K = 16× pixel → raster tetap, RT perlu BVH/RT core).

## Belum dikerjakan (tidak bisa dilakukan di sandbox ini)
1. **Menjalankan viewer Three.js di browser + Export PPM + `compare.py` vs NumPy (Lab 3.1–3.2).** Sandbox tidak punya `three` maupun jaringan, jadi `web/viewer.js` hanya lolos pemeriksaan sintaks (`node --check`), **belum diuji render**.
   Langkah Anda: `npx serve .` → buka `http://localhost:3000/web/?cmp=1` → *Export PPM* → simpan `web/mymodel_three.ppm` → `python compare.py out/temple_raster.ppm web/mymodel_three.ppm`. Target ≈ 30 dB, residual di tepi. Jika interior jauh lebih gelap/terang, curigai skala cahaya (`× π` di r155+), `outputColorSpace`, atau texture `flipY`.
2. **Publikasi GitHub Pages dan URL-nya**, serta clone bersih sungguhan.
3. **Hitung tangan, diagnosis dengan kata sendiri, bacaan WebGLRenderer/learnopengl, refleksi ½ halaman Lab 3.6, histogram depth z-fighting, viva.**
4. Toolchain & tanggal mesin **Anda** (bukan sandbox).
5. *Studi Pendahuluan* (≥ 4 halaman, Q1–Q5) tidak termasuk pekerjaan ini.
