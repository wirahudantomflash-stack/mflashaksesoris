# MFLASH — Dashboard Cabang (Pembelian + Penjualan)

Satu aplikasi Streamlit dengan dua tab:

1. **📦 Dashboard Pembelian Cabang** — porsi pemasok aksesoris (terbesar ke
   terkecil) + fokus target pembelian ke pemasok tertentu (default: LUNA,
   Rp 2.000.000.000).
2. **🧾 Dashboard Penjualan Cabang** — Top 3 Cabang, Top 10 Produk Terlaris,
   Top 5 Sales Retail.

Kedua tab berdiri sendiri-sendiri (data, filter, dan hasilnya terpisah) —
digabung dalam satu aplikasi supaya tidak perlu buka dua tautan berbeda.

## Isi repo

```
app.py               # aplikasi utama (2 tab)
logic_pembelian.py    # logika olah data pembelian/pemasok
logic_penjualan.py    # logika olah data penjualan/cabang
requirements.txt      # dependensi untuk Streamlit Cloud
```

## Cara pakai di GitHub + Streamlit Cloud

1. Buat repo baru, unggah keempat berkas di atas.
2. **Opsional:** taruh berkas data langsung di root repo (sejajar `app.py`)
   supaya termuat otomatis tanpa upload manual tiap buka aplikasi:
   - `Purchase_Aksesoris_Regional.xlsx` (harus punya sheet **"DB Pembelian"**) untuk tab Pembelian.
   - `penjualan.csv.gz` untuk tab Penjualan — boleh CSV/gz, atau Excel
     (`.xlsx`) dengan sheet **"Rincian Faktur Penjualan"**.
   Kalau tidak ada, tersedia tombol unggah manual di panel kiri untuk masing-masing
   (menerima `.csv`, `.gz`, `.xlsx`, `.xls`).
3. Deploy lewat [share.streamlit.io](https://share.streamlit.io) dengan
   `app.py` sebagai entry point.

## Panel kiri (sidebar)

Sidebar dipakai bersama oleh kedua tab, berisi:
- Unggah data pembelian
- Unggah data penjualan
- Pengaturan target pemasok (nama pemasok & nilai target, untuk tab Pembelian)

Filter tahun/bulan/cabang untuk tiap tab ada **di dalam tab masing-masing**
(bukan di sidebar), supaya tidak tertukar antara filter pembelian dan
penjualan saat berpindah tab.

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

## Pengujian

Kedua modul logika (`logic_pembelian.py`, `logic_penjualan.py`) sudah diuji
bersamaan (tanpa konflik nama) memakai data asli Anda:
- Pembelian: 5.319 baris, 18 cabang, ~94 pemasok setelah difilter aksesoris.
- Penjualan (rincian satu cabang): 13.989 baris, 5.709 nota unik.
- Penjualan (gabungan 17 cabang): 67.954 baris, 54.012 nota unik — kolom
  cabang otomatis terdeteksi (baik ditulis "Cabang" maupun "CABANG"), tidak
  perlu diminta nama cabang manual.

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
