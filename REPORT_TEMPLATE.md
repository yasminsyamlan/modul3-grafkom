# Laporan Modul 3 — Transformasi 3D, Proyeksi & Real-Time
Nama / NIM: ______   Toolchain (OS, Python, NumPy, Node, browser, Three.js, tanggal): ______

## A1. Model & telusuran satu-vertex
- Model: `mymodel.obj` (≥200 segitiga, UV nyata). Vertex dipilih: ______
- Tabel: object → world → view → clip → NDC → screen (angka tiap space; `worked_example.py`).
- Telusuran-kolom M dan V: +x → ___, +y → ___, +z → ___, origin → ___
- Hitung tangan Mp dan V(Mp) vs `worked_example.py` (≥3 desimal): ______

## A2. Pipeline from-scratch
- E1–E4 (angka): (2,3,4)→(3,3,−3)→(2,2); dualitas identik; z=−n→−1, z=−f→+1; u = 0.1
- Frame vs `ref/temple_ref.ppm` (PSNR/SSIM): ___ ; vs raytrace: ___ ; residual: ___

## A3. Diagnosis & perbaikan (tulis diagnosis SEBELUM melihat perbaikan)
| Bug | Diagnosis | Bukti | Satu perubahan | SSIM sebelum/sesudah | Pitfall §12 |
|---|---|---|---|---|---|
| inside-out | | | | | 12.6 |
| z-fighting | | histogram depth | | | 12.2 |
| stretched | | matriks tercetak | | | 12.1 |

## A4. Raster vs ray-trace
- Prediksi (`bench.py` PRED): ___ ; terukur: ___ ; rekonsiliasi: ___
- Pilihan viewer real-time: ___ (alasan) ; beauty shot: ___ (alasan)
- Kondisi pilihan berbalik (≥2, satu baris): ______

## A5. Texture & sampling
- u naif 0.5 vs perspective-correct 0.1; `perspective_demo.py` (SSIM ___)
- Mipmap `mipmap.py`: HF energy ___ → ___ ; perubahan antar-frame ___ → ___

## A6. Reproducibility & viva
- Transkrip `repro.sh`; URL GitHub Pages: ______
- Siap jawab: mengapa urutan / handedness / near ini? Bagaimana jika Direct3D / canvas 4K?
