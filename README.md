# MFLASH — Dashboard Cabang (Persediaan Aksesoris LUNA + Penjualan Aksesoris)

Satu aplikasi Streamlit dengan dua tab:

1. **📊 Dashboard Persediaan Aksesoris** — indikator stok produk **LUNA** per
   cabang dengan kode warna 🔴🟡🟢 (berdasarkan jumlah unit stok aktual),
   ringkasan cabang & produk yang paling perlu segera direstock, dan nilai
   persediaan LUNA per cabang.
2. **🧾 Dashboard Penjualan Aksesoris** — satu tab gabungan berisi dua bagian:
   - **Ringkasan Cabang, Produk & Sales**: ranking Seluruh Cabang, Semua
     Produk Aksesoris (terlaris & profit), dan Seluruh Sales.
   - **Revenue, HPP & Katalog LUNA**: revenue & tren bulanan, Top 10 produk
     aksesoris terlaris & profit, omzet + HPP seluruh cabang, katalog
     referensi harga LUNA & potensi profit, serta analisa + proyeksi
     5–10 tahun.

Kedua bagian dalam tab Penjualan Aksesoris memakai **satu berkas data
penjualan yang sama** (satu tombol unggah saja di panel kiri) — dibaca dua
kali secara independen oleh dua modul olah data yang berbeda, jadi tidak
perlu unggah berkas terpisah untuk tiap bagian.

## Isi repo

```
app.py               # aplikasi utama (2 tab)
logic_persediaan.py    # logika indikator stok LUNA per cabang
logic_penjualan.py    # logika olah data penjualan/cabang (umum)
logic_aksesoris.py     # logika olah data revenue penjualan aksesoris
logic_pembelian.py     # TIDAK dipakai app.py lagi — lihat catatan di bawah
requirements.txt      # dependensi untuk Streamlit Cloud
```

> **Catatan:** `logic_pembelian.py` (dashboard porsi pemasok yang lama)
> sudah tidak lagi dipanggil dari `app.py` sejak tab Pembelian diganti
> menjadi tab Persediaan Aksesoris. Berkasnya tetap disertakan kalau-kalau
> Anda masih butuh logikanya nanti — boleh dihapus dari repo kalau memang
> tidak dipakai.

## Cara pakai di GitHub + Streamlit Cloud

1. Buat repo baru, unggah berkas-berkas yang relevan di atas.
2. **Opsional:** taruh berkas data langsung di root repo (sejajar `app.py`)
   supaya termuat otomatis tanpa upload manual tiap buka aplikasi:
   - `Persediaan_Aksesoris_Regional.xlsx` (harus punya sheet
     **"Daftar Barang dan Jasa"**) untuk tab Persediaan Aksesoris.
   - `penjualan.csv.gz` untuk **kedua bagian** di tab Penjualan Aksesoris —
     boleh CSV/gz, atau Excel (`.xlsx`) dengan sheet **"Rincian Faktur Penjualan"**.
   Kalau tidak ada, tersedia tombol unggah manual di panel kiri untuk masing-masing
   (menerima `.csv`, `.gz`, `.xlsx`, `.xls`).
3. Deploy lewat [share.streamlit.io](https://share.streamlit.io) dengan
   `app.py` sebagai entry point.

## Panel kiri (sidebar)

Sidebar dipakai bersama oleh kedua tab, berisi:
- Unggah data persediaan — untuk tab Persediaan Aksesoris
- Unggah data penjualan — dipakai untuk **kedua bagian** di tab Penjualan
  Aksesoris (Ringkasan Cabang/Produk/Sales, maupun Revenue/HPP/Katalog LUNA)
- **Ambang indikator stok LUNA** — dua kotak angka untuk mengatur batas
  Merah dan batas Kuning (default: Merah ≤ 2 unit, Kuning 3–7 unit, Hijau
  ≥ 8 unit — bisa diubah tanpa ubah kode)

Filter tahun/bulan/cabang untuk tiap bagian ada **di dalam bagian
masing-masing** (bukan di sidebar), supaya filter tidak tertukar.

## Aturan data — Tab Persediaan Aksesoris

- Barang LUNA diidentifikasi dari **nama barang yang mengandung kata
  "LUNA"** (sumber data tidak punya kolom Pemasok/Brand terpisah untuk stok).
- Data difilter ke kategori barang **AKSESORIS** (dua ejaan digabung),
  sesuai kolom `Kategori Barang`.
- **Indikator dari jumlah stok aktual** (`Kts (Semua Gdng)`), bukan
  persentase relatif terhadap cabang lain — supaya konsisten dan tidak
  bergantung pada produk pembanding. Ambang batas default diturunkan dari
  sebaran stok LUNA riil (median 3, kuartil-3 ≈10):
  - 🔴 **Merah**: stok ≤ 2 (kritis, termasuk 0 dan anomali negatif)
  - 🟡 **Kuning**: stok 3–7 (menipis, perlu diawasi)
  - 🟢 **Hijau**: stok ≥ 8 (aman)
  Ambang ini **bisa diubah dari sidebar** kalau standar operasional MFLASH
  berbeda dari saran ini.
- Stok negatif pada sumber data (anomali sistem, biasanya transaksi keluar
  tercatat sebelum stok masuk disesuaikan) otomatis masuk kategori Merah,
  bukan disembunyikan atau di-clip jadi 0.
- **Keterbatasan yang perlu diketahui:** indikator ini murni dari jumlah
  unit fisik, BUKAN "hari persediaan" (days of supply) — karena nama produk
  di data stok vs data penjualan cuma cocok persis sekitar 45% (variasi
  penulisan), sehingga menghitung kecepatan jual per produk per cabang
  belum bisa diandalkan sebagai basis utama. Kalau penamaan produk di kedua
  sumber data dirapikan/distandardisasi di masa depan, pendekatan berbasis
  kecepatan jual bisa jadi peningkatan berikutnya.
- Kode Barang **tidak** dipakai sebagai kunci pembanding antar cabang
  karena penomorannya independen per cabang (kode yang sama bisa merujuk
  ke produk berbeda di cabang lain) — nama barang yang dipakai sebagai
  kunci pengelompokan, setelah dirapikan (strip + uppercase).

## Aturan data — Tab Penjualan Aksesoris (bagian Ringkasan)

- Satu nota = kombinasi `CABANG` + `NO FAKTUR` (bukan nomor faktur saja).
- `HARGA BELI` sudah total per baris — tidak dikalikan `QTY` lagi.
- Baris kembar tidak dibuang.
- `AKSESORIS`/`ACCESORIES` digabung.
- Boleh unggah data **gabungan seluruh cabang** (ada kolom `Cabang`/`CABANG`),
  atau **rincian satu cabang saja** (tanpa kolom cabang) — kalau tidak ada,
  aplikasi meminta nama cabangnya lewat kotak input di dalam tab.
- Menerima format **CSV/gz** maupun **Excel** (`.xlsx`, sheet
  "Rincian Faktur Penjualan").
- Angka ditampilkan gaya Indonesia (`68.838`, `10,3%`, `Rp 4.711.790.000`).

## Aturan data — Tab Penjualan Aksesoris (bagian Revenue, HPP & Katalog LUNA)

- Memakai **berkas yang sama** dengan bagian Ringkasan di atasnya — dibaca
  ulang secara independen (bukan berbagi objek berkas yang sama, supaya
  tidak ada masalah posisi baca habis pada salah satu bagian).
- Kalau berkas yang diunggah adalah **rincian satu cabang saja** (tanpa
  kolom Cabang), Anda cukup mengisi nama cabangnya **sekali** di bagian
  "Ringkasan Cabang, Produk & Sales" — nama itu otomatis dipakai juga di
  bagian Revenue ini, tidak perlu diisi dua kali.
- Sama seperti bagian Ringkasan: nota = `CABANG` + `NO FAKTUR`, `HARGA BELI`
  sudah total per baris, baris kembar tidak dibuang.
- Kolom "Unnamed" dari sumber Excel (baik yang kosong maupun yang cuma
  duplikat kolom utama) otomatis dibuang saat baca berkas.
- Segmen transaksi dikelompokkan otomatis dari `KATEGORI PENJUALAN`:
  **Service** (mengandung kata "SERVICE"), **Penjualan Unit** (mengandung
  kata "PENJUALAN"), sisanya **Lainnya**.
- **Proyeksi 5–10 tahun** dihitung dari rata-rata omzet bulan-bulan yang
  **lengkap saja** (bulan berjalan yang belum penuh dikeluarkan dari
  rata-rata), lalu diekstrapolasi dengan 3 skenario pertumbuhan tahunan
  majemuk (Konservatif 5%, Moderat 12%, Optimis 20% — bisa diubah di
  `logic_aksesoris.py` fungsi `proyeksi_tahunan` kalau perlu skenario lain).
  **Ini estimasi kasar**, bukan model statistik penuh, karena data historis
  yang tersedia baru mencakup kurang dari 1 tahun — dashboard menampilkan
  peringatan ini secara eksplisit ke pengguna.
- **Katalog Referensi Harga LUNA**: pricelist resmi LUNA (85 produk aksesoris
  dengan harga dealer & SRP, dari `NEW_PL_05_JULI_LUNA_2026.pdf`) ditanam
  langsung di `logic_aksesoris.py` sebagai tabel referensi, dipakai untuk
  menghitung **potensi profit per produk** kalau dijual sesuai SRP resmi.
  Margin potensial ini (~30,6% rata-rata) dibandingkan dengan margin AKTUAL
  yang tercapai di data penjualan sebagai bahan evaluasi — bukan diklaim
  sebagai angka yang identik, karena keduanya diukur dari basis berbeda
  (katalog vs skema Up Harga Bundling di Surat Edaran). Katalog bahan/mesin
  cutting (28 item, tanpa SRP resmi) ditampilkan terpisah sebagai referensi
  harga modal saja.
- Kotak analisa menautkan temuan ke konteks lain yang sudah ada (program
  Bundling Aksesoris NexLink & LUNA dari Surat Edaran SE/001/IN-MF/IV/2026)
  supaya rekomendasinya konkret, bukan generik.

## Pengujian

Modul-modul logika sudah diuji memakai data asli Anda:
- **Persediaan** (`logic_persediaan.py`): 23.124 baris persediaan, 18 cabang,
  358 baris item LUNA (87 nama produk unik) — indikator menghasilkan
  134 kombinasi SKU×cabang Merah, 78 Kuning, 123 Hijau (dari total 335,
  karena sebagian baris terduplikasi kode barangnya dalam satu cabang dan
  digabung); termasuk penanganan stok negatif dan kasus tepi filter cabang
  kosong.
- **Penjualan** (rincian satu cabang): 13.989 baris, 5.709 nota unik.
- **Penjualan** (gabungan 17 cabang): 67.954 baris, 54.012 nota unik.
- **Revenue Aksesoris** (gabungan 18 cabang): 72.776 baris, 58.550 nota
  unik, omzet total Rp 4.164.979.227 (margin ~40,8%), Jan–Ags 2026 —
  termasuk simulasi penuh seluruh fungsi dan kasus tepi filter kosong.

**Catatan jujur:** lingkungan tempat saya membuat berkas ini tidak
tersambung internet, sehingga saya tidak bisa memasang paket `streamlit`
dan menjalankan `streamlit run app.py` langsung di sini. Yang sudah saya
uji dan pastikan benar adalah seluruh fungsi olah data di modul
`logic_*.py`, memakai data Excel/CSV asli Anda. `app.py` sendiri hanya
menyusun logika itu ke widget Streamlit standar (`tabs`, `sidebar`,
`columns`, `metric`, `number_input`, `bar_chart`, `dataframe`,
`download_button`, `file_uploader`) — tidak ada fitur eksotis. Saya
sarankan menjalankan sekali secara lokal (`streamlit run app.py`)
sebelum/sesudah deploy, dan beri tahu saya kalau ada error — langsung
saya perbaiki.
