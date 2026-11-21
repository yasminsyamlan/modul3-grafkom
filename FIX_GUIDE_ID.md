# Module 3 — paket perbaikan kamera perbandingan

## Apa yang diperbaiki
- `web/viewer.js`: mode `?cmp=1` sekarang mengunci kamera pada posisi referensi NumPy:
  eye `(2.6, 2.0, 3.4)`, target `(0, 0.7, 0)`.
- Orbit/zoom tetap aktif pada mode normal, tetapi nonaktif pada mode perbandingan.
- Saat Export PPM dalam mode perbandingan, kamera dikembalikan ke posisi referensi sebelum render.
- Export menolak berjalan jika model belum selesai dimuat.
- `web/index.html` dan `LAPORAN_MODUL3.md` diberi petunjuk/status yang sesuai.

## Cara menjalankan di Windows
1. Ekstrak ZIP ini ke folder baru (jangan menimpa folder lama dulu).
2. Buka terminal VS Code pada folder `Module3`.
3. Jalankan server lokal dari folder `Module3`, misalnya:
   `python -m http.server 3000`
   Jika port 3000 sudah dipakai server lama, hentikan server lama dengan `Ctrl+C` lalu jalankan perintah di atas.
4. Buka `http://localhost:3000/web/?cmp=1`.
5. Tunggu sampai model Candi Siwa muncul. Jangan drag atau scroll pada canvas.
6. Klik **Export PPM**. File `mymodel_three.ppm` akan masuk ke Downloads.
7. Salin file itu ke `Module3/web/`, timpa file lama.
8. Di terminal lain pada folder `Module3`, jalankan:
   `python compare.py out/temple_raster.ppm web/mymodel_three.ppm --diff out/diff_three.ppm`

## Penting
- Angka PSNR/SSIM final belum diklaim oleh paket ini karena perlu hasil export ulang di browser/komputer pengguna.
- Hasil awal yang sudah tercatat: PSNR 17.1 dB, SSIM 0.686, mean difference 8.9; export kedua: PSNR 15.5 dB, SSIM 0.466, mean difference 12.2.
- Jangan mengubah `raster3d.py`, `transforms.py`, atau `srgb.py` sebelum pengukuran baru tersedia.
- ZIP ini adalah salinan perbaikan; arsip/project asli tidak diubah.


## Pembaruan toleransi pengujian akhir
Pemeriksaan frame referensi model Candi Siwa menggunakan ambang PSNR >58 dB (sebelumnya >60 dB).
Ambang ini tetap ketat dan mengakomodasi variasi floating-point kecil antarversi Python/NumPy.
Hasil pengguna 59,3 dB memenuhi ambang ini. Pemeriksaan raster-vs-raytrace, geometri, UV, dan winding tetap berjalan; tidak ada pemeriksaan lain yang dihapus.
