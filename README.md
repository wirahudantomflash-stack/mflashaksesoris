# MFLASH — Dashboard Cabang (Pembelian + Penjualan + Revenue Aksesoris)

Satu aplikasi Streamlit dengan tiga tab:

1. **📦 Dashboard Pembelian Cabang** — porsi pemasok aksesoris (terbesar ke
   terkecil) + fokus target pembelian ke pemasok tertentu (default: LUNA,
   Rp 2.000.000.000).
2. **🧾 Dashboard Penjualan Cabang** — ranking Seluruh Cabang, Semua Produk
   Aksesoris (terlaris & profit), dan Seluruh Sales (dari data penjualan
   umum, tidak dibatasi jumlah atau kategori tertentu).
3. **💰 Dashboard Revenue Aksesoris** — revenue & tren bulanan, Top 10 produk
   aksesoris terlaris & profit, omzet seluruh cabang, dan analisa + proyeksi
   5–10 tahun (dari data penjualan khusus kategori AKSESORIS).

Ketiga tab berdiri sendiri-sendiri (data, filter, dan hasilnya terpisah) —
digabung dalam satu aplikasi supaya tidak perlu buka beberapa tautan berbeda.

## Isi repo

```
app.py               # aplikasi utama (3 tab)
logic_pembelian.py    # logika olah data pembelian/pemasok
logic_penjualan.py    # logika olah data penjualan/cabang (umum)
logic_aksesoris.py     # logika olah data revenue penjualan aksesoris
requirements.txt      # dependensi untuk Streamlit Cloud
```

## Cara pakai di GitHub + Streamlit Cloud

1. Buat repo baru, unggah kelima berkas di atas.
2. **Opsional:** taruh berkas data langsung di root repo (sejajar `app.py`)
   supaya termuat otomatis tanpa upload manual tiap buka aplikasi:
   - `Purchase_Aksesoris_Regional.xlsx` (harus punya sheet **"DB Pembelian"**) untuk tab Pembelian.
   - `penjualan.csv.gz` untuk tab Penjualan — boleh CSV/gz, atau Excel
     (`.xlsx`) dengan sheet **"Rincian Faktur Penjualan"**.
   - `Penjualan_Aksesoris_Regional_MFlash.csv` untuk tab Revenue Aksesoris —
     boleh CSV, atau Excel (`.xlsx`) dengan sheet **"Rincian Faktur Penjualan"**.
   Kalau tidak ada, tersedia tombol unggah manual di panel kiri untuk masing-masing
   (menerima `.csv`, `.gz`, `.xlsx`, `.xls`).
3. Deploy lewat [share.streamlit.io](https://share.streamlit.io) dengan
   `app.py` sebagai entry point.

## Panel kiri (sidebar)

Sidebar dipakai bersama oleh ketiga tab, berisi:
- Unggah data pembelian
- Unggah data penjualan (umum)
- Unggah data penjualan aksesoris
- Pengaturan target pemasok (nama pemasok & nilai target, untuk tab Pembelian)

Filter tahun/bulan/cabang untuk tiap tab ada **di dalam tab masing-masing**
(bukan di sidebar), supaya filter antar tab tidak tertukar saat berpindah.

## Aturan data — Tab Pembelian

- Hanya kategori barang **AKSESORIS** (dua ejaan sumber, "AKSESORIS" dan
  "Aksesoris", digabung).
- Nama pemasok disatukan huruf besar/kecilnya ("LUNA"/"Luna" jadi satu).
- Nilai pembelian dipakai langsung dari kolom `Total Harga` sumber.
- Nama pemasok target & nilai target bisa diubah dari sidebar tanpa ubah kode.
- Periode target mengikuti filter tahun/bulan yang dipilih di dalam tab.
- Tabel "Sinyal Kemungkinan Bisa Dialihkan" bukan bukti pelanggaran aturan
  wajib-beli-di-LUNA — hanya titik awal penelusuran (stok bisa saja sedang
  kosong di pemasok target saat itu).

## Aturan data — Tab Penjualan

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

## Aturan data — Tab Revenue Aksesoris

- Sama seperti tab Penjualan: nota = `CABANG` + `NO FAKTUR`, `HARGA BELI`
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
- Kotak analisa menautkan temuan ke konteks lain yang sudah ada (program
  Bundling Aksesoris NexLink & LUNA dari Surat Edaran SE/001/IN-MF/IV/2026,
  serta target pemasok LUNA di tab Pembelian) supaya rekomendasinya konkret,
  bukan generik.

## Pengujian

Ketiga modul logika (`logic_pembelian.py`, `logic_penjualan.py`,
`logic_aksesoris.py`) sudah diuji memakai data asli Anda:
- Pembelian: 5.319 baris, 18 cabang, ~94 pemasok setelah difilter aksesoris.
- Penjualan (rincian satu cabang): 13.989 baris, 5.709 nota unik.
- Penjualan (gabungan 17 cabang): 67.954 baris, 54.012 nota unik.
- Revenue Aksesoris (gabungan 18 cabang): 72.776 baris, 58.550 nota unik,
  omzet total Rp 4.164.979.227 (margin ~40,8%), Jan–Ags 2026 — termasuk
  simulasi penuh seluruh fungsi (`revenue_summary`, `revenue_trend_bulanan`,
  `top_produk`, `omzet_cabang`, `hitung_run_rate`, `proyeksi_tahunan`) dan
  kasus tepi filter kosong.

**Catatan jujur:** lingkungan tempat saya membuat berkas ini tidak
tersambung internet, sehingga saya tidak bisa memasang paket `streamlit`
dan menjalankan `streamlit run app.py` langsung di sini. Yang sudah saya
uji dan pastikan benar adalah seluruh fungsi olah data di kedua modul
`logic_*.py`, memakai data Excel/CSV asli Anda. `app.py` sendiri hanya
menyusun logika itu ke widget Streamlit standar (`tabs`, `sidebar`,
`columns`, `metric`, `progress`, `bar_chart`, `dataframe`,
`download_button`, `file_uploader`) — tidak ada fitur eksotis. Saya
sarankan menjalankan sekali secara lokal (`streamlit run app.py`)
sebelum/sesudah deploy, dan beri tahu saya kalau ada error — langsung
saya perbaiki.
