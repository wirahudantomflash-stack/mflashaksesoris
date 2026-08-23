# MFlash Dashboard Aksesoris (Persediaan LUNA + Penjualan Aksesoris)

Satu aplikasi Streamlit dengan dua tab:

1. **📊 Dashboard Persediaan Aksesoris** — versi ringkas, mudah dikontrol,
   berisi 4 bagian:
   1. **Nilai Persediaan Aksesoris — LUNA vs Selain LUNA**: perbandingan
      nilai persediaan per cabang, kartu ringkasan, grafik, dan tabel.
   2. **Produk Paling Diminati per Cabang (Wajib Distok)**: Top-N produk
      terlaris per cabang (dari data penjualan), disandingkan dengan stok
      saat ini.
   3. **Kebutuhan Konsumen yang Belum Terpenuhi**: produk favorit yang
      stoknya kosong/rendah — sinyal permintaan yang belum terlayani.
   4. **Analisa Lokasi Cabang MFlash**: peta 18 cabang (lokasi asli dari
      pencarian data lokasi), sebaran per wilayah, disandingkan dengan nilai
      persediaan.
   Ditutup dengan **Peta Stok (heatmap) Cabang × Produk** khusus LUNA —
   **satu-satunya** bagian yang memakai indikator warna 🔴🟡🟢 — dan kotak
   Analisa & Tindak Lanjut.
2. **🧾 Dashboard Penjualan Aksesoris** — satu tab gabungan berisi dua bagian:
   - **Ringkasan Cabang, Produk & Sales**: ranking Seluruh Cabang, Semua
     Produk Aksesoris (terlaris & profit), dan Seluruh Sales.
   - **Revenue, HPP & Katalog LUNA**: revenue & tren bulanan, Top 10 produk
     aksesoris terlaris & profit, omzet + HPP seluruh cabang, katalog
     referensi harga LUNA & potensi profit, **matrix insentif resmi &
     kalkulator THP Sales Retail** (dikalibrasi ke target Rp5-8jt/bulan),
     **target pencapaian penjualan LUNA** (default Rp 2 miliar / 12 bulan
     mulai Agustus 2026), serta analisa + proyeksi 5–10 tahun.

Kedua tab memakai **satu berkas data penjualan yang sama** (satu tombol
unggah saja di panel kiri, bagian "🧾 Data Penjualan") — dibaca ulang secara
independen oleh tab Persediaan (untuk bagian "Produk Paling Diminati") dan
tab Penjualan Aksesoris, jadi tidak perlu unggah berkas terpisah.

## Isi repo

```
app.py               # aplikasi utama (2 tab)
flash_logo.png        # logo Flash — dipakai di judul halaman & sidebar (st.logo)
logic_persediaan.py    # logika indikator stok LUNA per cabang
logic_penjualan.py    # logika olah data penjualan/cabang (umum)
logic_aksesoris.py     # logika olah data revenue penjualan aksesoris
logic_pembelian.py     # TIDAK dipakai app.py lagi — lihat catatan di bawah
requirements.txt      # dependensi untuk Streamlit Cloud
```

> **Penting:** `flash_logo.png` **wajib** ada di root repo, sejajar dengan
> `app.py` — dipanggil lewat `st.set_page_config(page_icon="flash_logo.png")`
> dan `st.logo("flash_logo.png")`. Kalau berkas ini tidak diunggah, aplikasi
> akan gagal jalan (`FileNotFoundError`) karena keduanya dipanggil di baris
> paling awal skrip.

> **Catatan:** `logic_pembelian.py` (dashboard porsi pemasok yang lama)
> sudah tidak lagi dipanggil dari `app.py` sejak tab Pembelian diganti
> menjadi tab Persediaan Aksesoris. Berkasnya tetap disertakan kalau-kalau
> Anda masih butuh logikanya nanti — boleh dihapus dari repo kalau memang
> tidak dipakai.

## Cara pakai di GitHub + Streamlit Cloud

1. Buat repo baru, unggah berkas-berkas yang relevan di atas — **termasuk
   `flash_logo.png`, wajib ada** (lihat catatan di bagian "Isi repo").
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

> **Catatan:** kontrol ambang indikator stok (batas Merah/Kuning) dan angka
> "Jumlah SKU" **sementara disembunyikan** dari sidebar & tampilan dashboard
> atas permintaan — supaya fokus murni ke kontrol stok menipis tanpa
> distraksi angka tambahan. Ambang tetap dipakai di belakang layar dengan
> nilai (Merah ≤ 25 unit, Kuning 26–99 unit, Hijau ≥ 100 unit), diatur
> lewat variabel `batas_merah`/`batas_kuning` di awal `app.py` kalau perlu
> diubah. Beri tahu saya kapan saja kalau kontrolnya mau dimunculkan lagi.

Filter tahun/bulan/cabang untuk tiap bagian ada **di dalam bagian
masing-masing** (bukan di sidebar), supaya filter tidak tertukar.

## Aturan data — Tab Persediaan Aksesoris

- Barang LUNA diidentifikasi dari **nama barang yang mengandung kata
  "LUNA"** (sumber data tidak punya kolom Pemasok/Brand terpisah untuk stok);
  sisanya masuk kelompok "Selain LUNA".
- Data difilter ke kategori barang **AKSESORIS** (dua ejaan digabung),
  sesuai kolom `Kategori Barang` — berlaku untuk semua bagian di tab ini.
- **Bagian 1 (Nilai Persediaan)**: perbandingan langsung nilai persediaan
  LUNA vs Selain LUNA per cabang (`nilai_persediaan_perbandingan()`), tanpa
  indikator warna — murni angka.
- **Bagian 2 & 3 (Produk Favorit / Kebutuhan Belum Terpenuhi)**: memakai
  data **penjualan** aksesoris (bukan cuma stok) untuk menentukan "paling
  diminati" — ranking dari `QTY` terjual. Ada **dua mode tampilan**
  (`st.radio`) yang bisa dipilih pengguna:
  - **Per Cabang** (`produk_favorit_per_cabang()`): Top-N produk per cabang,
    Top-N bisa diatur lewat slider.
  - **Semua Cabang (Gabungan)** (`produk_favorit_semua_cabang()`): qty
    terjual, potensi omzet & laba dijumlahkan LINTAS CABANG per nama
    barang — untuk melihat produk mana yang paling mendesak dibenahi
    secara jaringan (dasar keputusan pembelian besar ke pemasok), bukan
    per cabang kecil-kecil. Bisa diurutkan dari Qty Terjual / Potensi
    Omzet / Potensi Laba.
  Kedua mode menampilkan 4 hal yang diminta pengguna:
  1. **Rincian nama barang dan jumlah stok** (Stok Saat Ini / Stok Semua
     Cabang tergantung mode).
  2. **Potensi omzet dan laba** — dihitung dari `TOTAL HARGA` dan
     `TOTAL HARGA - HARGA BELI` yang sudah terbukti tercapai secara
     historis untuk produk itu (bukan proyeksi baru, tapi nilai yang
     akan terus terealisasi kalau produknya tetap distok).
  3. **(saran Claude) Estimasi Kebutuhan Restock** — rata-rata terjual per
     bulan (dari jumlah bulan unik pada data) dikurangi stok saat ini,
     dibulatkan ke atas, minimal 0 — supaya bukan cuma tahu "butuh
     restock" tapi juga tahu berapa banyak.
  4. **(saran Claude) Ranking Prioritas Restock Se-Jaringan** — khusus mode
     Semua Cabang: kolom "Jumlah Cabang Stok Kosong/Rendah" menunjukkan di
     berapa cabang produk itu kritis sekaligus, sinyal masalah pasokan
     sistemik (bukan cuma satu cabang).
  Kolom **"Wajib Direstock"** (⚠️ Ya / Tidak) dipakai sebagai flag
  sederhana — **bukan** indikator tri-warna.
  - **Nama produk dicocokkan persis (exact match)** antara data penjualan
    dan data stok — untuk seluruh katalog aksesoris (bukan cuma LUNA),
    tingkat kecocokan ini **97,9%** (diuji dengan data asli), jauh lebih
    baik dari kecocokan produk LUNA saja (~45%, karena variasi penulisan
    nama LUNA lebih beragam antar cabang).
  - **Temuan nyata dari data asli** (bukan bug): **75,2%** dari seluruh
    baris stok aksesoris berstok ≤ 0 di seluruh jaringan pada data yang
    diuji — dan produk-produk terlaris (yang paling sering muncul di daftar
    "Produk Favorit") justru yang paling sering kehabisan stok, karena
    barang laris memang lebih cepat habis. Kotak "Kebutuhan Konsumen Belum
    Terpenuhi" secara khusus menyoroti pola ini, plus kartu **Total Potensi
    Omzet & Laba** kalau semua kebutuhan yang belum terpenuhi ini terjual.
  - Total nilai stok jaringan yang dijumlahkan (`Stok Semua Cabang`)
    di-*clip* minimal 0 — beberapa produk punya anomali stok negatif di
    sebagian cabang (transaksi keluar tercatat sebelum stok masuk
    disesuaikan) yang kalau dibiarkan bisa membuat total jaringan
    kelihatan negatif, padahal secara fisik itu tidak mungkin.
- **Bagian 4 (Analisa Lokasi)**: 18 titik lokasi cabang MFlash dicari
  langsung berdasarkan nama cabang (bukan perkiraan/koordinat acak) —
  alamat, koordinat, dan rating asli, ditanam di
  `logic_persediaan.py` (`data_lokasi_cabang()`). Peta pakai `st.map()`
  bawaan Streamlit. Sebaran per wilayah (`ringkasan_wilayah()`)
  mengelompokkan 18 cabang ke 8 wilayah administratif (Jakarta Timur
  terpadat dengan 4 cabang: Cilangkap, Condet, Klender, Radjiman).
- **Peta Stok (heatmap) Cabang × Produk — SATU-SATUNYA bagian yang memakai
  indikator warna 🔴🟡🟢** (sesuai permintaan eksplisit): khusus produk LUNA
  (87 nama produk, masih kebaca dalam satu grid; tidak dipasang untuk
  Selain LUNA karena 12.634 nama produk akan membuat grid tidak kebaca).
  Ambang: 🔴 Merah stok ≤ 25, 🟡 Kuning 26–99, 🟢 Hijau ≥ 100 (nilai tetap
  di kode, lihat catatan di bagian "Panel kiri"). Sel abu-abu "-" berarti produk
  tidak tercatat sama sekali di cabang tsb (bukan berarti stoknya 0).
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

## Matrix Insentif & Kalkulator THP Sales Retail

Dipindahkan dari simulasi generik ke **transkrip matrix insentif resmi
perusahaan** (2 lembar referensi):

- **Matrix Insentif Pekanan — Retail (Ideal) v2**: 29 baris (Sales Retail 11
  tier, Store Manager 9 tier, Regional Manager 9 tier), masing-masing dari
  Omzet/Pekan → **Omzet/Bulan** (×4 minggu, bukan 4,33 — persis matrix
  resmi) → Estimasi GP (asumsi **30%**) → Insentif/Pekan (Sales Retail 5%
  dari GP, Store Manager 2%, Regional Manager 1%) → **Insentif/Bulan**
  (×4 minggu). Ditanam persis di `logic_aksesoris.py`
  (`matrix_insentif_pekanan()`), sudah diverifikasi cocok 100% dengan
  angka pada gambar referensi untuk seluruh 29 baris, termasuk kolom
  Omzet/Bulan dan Insentif/Bulan.
- **Matrix Insentif Per Item** (v3): 6 tier berdasarkan rentang
  harga jual (Rp50rb–100rb, >100rb–250rb, >250rb–500rb, >500rb–750rb,
  >750rb–1jt, >1jt), asumsi Gross Profit **30% konsisten** dari harga acuan
  di semua tingkat, insentif TETAP per unit terjual = **50% dari GP**
  secara konsisten (Rp7.500/Rp15.000/Rp37.500/Rp75.000/Rp112.500/
  Rp150.000). Ditanam di `matrix_insentif_per_item()`.
  - **Pengecualian — produk HYDROGEL**: insentif TETAP
    **Rp10.000/pcs** (`INSENTIF_HYDROGEL_PER_PCS`), berapa pun harga
    jualnya — tidak mengikuti tingkat harga pada matrix di atas. Diaktifkan
    lewat opsi terpisah "Sertakan Insentif Hydrogel" di kalkulator (tidak
    otomatis, karena kalkulator tidak membaca nama produk dari data
    penjualan asli — estimasi jumlah hydrogel terjual/hari diisi manual).
- **Kalkulator THP Sales Retail**: Total THP = **Gaji Pokok** + **Insentif
  %GP Bulanan** (langsung dari kolom "Insentif / Bulan" RESMI pada matrix
  pekanan — bukan lagi estimasi Insentif/Pekan × minggu/bulan yang bisa
  menyimpang dari referensi) + opsional **Insentif Per Item Bulanan**
  (estimasi jumlah item terjual/hari per tingkat harga × Insentif/Item ×
  hari kerja/bulan — otomatis menyesuaikan jumlah kolom input kalau jumlah
  tier matrix per-item berubah, tidak di-*hardcode* ke 4 atau 6) + opsional
  **Insentif Hydrogel Bulanan** (estimasi jumlah hydrogel terjual/hari ×
  Rp10.000 × hari kerja/bulan — komponen terpisah dari Insentif Per Item
  karena hydrogel dikecualikan dari aturan tingkat harga umum).
  - Fungsi `saran_gaji_pokok()` memberi **titik awal** Gaji Pokok supaya
    tier **Minimum** pas mencapai THP Minimum (default Rp 5jt) — bukan
    jawaban final, karena tier **Maksimum** belum tentu otomatis pas di
    THP Maksimum (default Rp 8jt): itu tergantung seberapa besar asumsi
    volume item terjual yang diinput.
  - Kolom **"Status Target"** (✅ dalam target / ⬇️ di bawah / ⬆️ di atas)
    ditampilkan per tier, supaya jelas terlihat kalau kalibrasi Gaji Pokok
    atau asumsi item/hari masih perlu disesuaikan.
  - **Konteks bisnis yang perlu diketahui**: kalau target Store Manager
    Rp 60 juta/bulan omzet AKSESORIS dibagi rata ke 4 Sales Retail per
    toko, rata-rata kontribusi tiap Sales Retail adalah Rp 15 juta/bulan =
    **Rp 3,75 juta/pekan** — ini di BAWAH tier Minimum pada matrix Sales
    Retail (Rp 5 juta/pekan). Kemungkinan basis "Omzet Individu" pada
    matrix pekanan dimaksudkan untuk omzet keseluruhan (bukan aksesoris
    saja); kalau memang murni dari aksesoris, target per-Sales-Retail
    belum menyentuh tier insentif terendah sekalipun pada matrix ini.
  - **Diuji dengan matrix per-item v2** (insentif jauh lebih besar dari v1):
    asumsi 1 item/hari di ke-6 tingkat harga saja sudah menghasilkan
    **Rp 13.780.000/bulan** dari insentif per item — jauh melampaui target
    Rp 8jt bahkan dengan Gaji Pokok Rp 0 (`saran_gaji_pokok()` otomatis
    berhenti di 0, tidak negatif). Ini bukan bug — dashboard dengan sengaja
    TIDAK memaksakan asumsi 1 item/hari di semua tingkat harga sebagai
    default yang "benar", karena kenyataannya jarang toko aksesoris laku
    1 unit/hari di tingkat harga >Rp1 juta. Turunkan asumsi item/hari di
    tingkat harga tinggi supaya Total THP mendekati rentang target.

## Target Pencapaian Penjualan LUNA

- Default: **Rp 2.000.000.000** dalam **12 bulan mulai Agustus 2026**
  (1 Agu 2026 – 31 Jul 2027) — ketiganya bisa diubah langsung dari
  dashboard (target, tanggal mulai, durasi bulan).
- Produk LUNA diidentifikasi dari **nama barang mengandung kata "LUNA"**,
  dihitung dari **seluruh data penjualan** (tidak terpengaruh filter
  tahun/bulan/cabang di bagian atas tab), supaya progress tidak
  "menghilang" cuma karena pengguna sedang menyaring tampilan lain.
- **Tanggal acuan "hari berjalan" memakai tanggal faktur TERAKHIR pada
  data** (bukan tanggal hari ini) — prinsip yang sama dipakai di bagian
  Proyeksi 5–10 Tahun, supaya persentase tidak terlihat rendah cuma karena
  data belum diperbarui.
- Dua ukuran pencapaian ditampilkan sekaligus: **% Pencapaian** (dibanding
  target yang SEHARUSNYA sudah tercapai sampai hari ke sekian dari total
  hari program) dan **% dari Target Penuh** (dibanding target 12 bulan
  penuh) — supaya jelas mana yang jadi ukuran "on-track" dan mana yang
  ukuran progres keseluruhan.

## Pengujian

Modul-modul logika sudah diuji memakai data asli Anda:
- **Persediaan** (`logic_persediaan.py`): 23.124 baris persediaan, 18 cabang.
  - **Nilai Persediaan**: LUNA Rp 268.940.246 vs Selain LUNA Rp 984.757.586
    (porsi LUNA rata-rata bervariasi per cabang, tertinggi di Ceger 54,5%,
    terendah di Jatiwaringin 2,8%) — diuji lengkap dengan kasus tepi filter
    cabang kosong.
  - **Produk Favorit & Kebutuhan Belum Terpenuhi**: diuji dengan cross-
    reference data penjualan (72.776 baris) × data stok — kecocokan nama
    produk 97,9%, ditemukan pola nyata 75,2% baris stok aksesoris berstok
    ≤ 0, dan produk terlaris justru paling sering termasuk di dalamnya
    (diverifikasi manual, bukan bug pencocokan nama). Kedua mode tampilan
    (Per Cabang: 90 baris; Semua Cabang Gabungan: diuji dengan 3 pilihan
    urutan — Qty Terjual, Potensi Omzet, Potensi Laba, masing-masing 10
    baris) sudah diuji lengkap dengan potensi omzet/laba dan estimasi
    kebutuhan restock. Bug duplikasi kolom, kesalahan huruf besar/kecil
    nama cabang saat digabung dengan data lokasi, dan total stok jaringan
    yang sempat negatif (anomali stok, sudah di-*clip* ke 0) ditemukan dan
    diperbaiki sebelum dikirim.
  - **Analisa Lokasi**: 18 titik lokasi cabang (dicari langsung, bukan
    perkiraan) berhasil dipetakan ke 8 wilayah administratif Jabodetabek +
    Karawang; digabung dengan data nilai persediaan tanpa baris yang hilang
    (0 kombinasi Cabang tidak cocok).
  - Termasuk kasus tepi filter cabang kosong, data penjualan belum
    diunggah, dan berkas penjualan rincian satu cabang tanpa nama cabang
    terisi.
- **Penjualan** (rincian satu cabang): 13.989 baris, 5.709 nota unik.
- **Penjualan** (gabungan 17 cabang): 67.954 baris, 54.012 nota unik.
- **Revenue Aksesoris** (gabungan 18 cabang): 72.776 baris, 58.550 nota
  unik, omzet total Rp 4.164.979.227 (margin ~40,8%), Jan–Ags 2026 —
  termasuk simulasi penuh seluruh fungsi dan kasus tepi filter kosong.
- **Matrix Insentif & Kalkulator THP**: `matrix_insentif_pekanan()` (29
  baris) dan `matrix_insentif_per_item()` (4 baris) diverifikasi cocok
  100% dengan angka pada gambar referensi resmi. `saran_gaji_pokok()` dan
  `kalkulator_thp_sales_retail()` diuji dengan beberapa skenario asumsi
  volume item terjual/hari, termasuk kasus tanpa insentif per item, dan
  kasus kalibrasi yang mendorong tier atas melewati target (terdeteksi
  benar sebagai status "di atas target").
- **Target LUNA**: diuji dengan target Rp 2 M / 12 bulan mulai Agustus 2026
  — hari ke-19 dari 365 hari program, tercapai Rp 33.754.860 (32,4% dari
  target-sampai-hari-ini, 1,7% dari target penuh), 1.198 transaksi LUNA
  tercatat; termasuk kasus tepi target Rp 0 dan program yang belum dimulai.

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
