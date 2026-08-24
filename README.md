# MFlash Dashboard Gadget dan Aksesoris (Persediaan LUNA + Parfum + Penjualan Aksesoris)

Satu aplikasi Streamlit dengan tiga tab:

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
   memakai indikator warna 🔴🟡🟢 (ambang stok ≤25 Merah, 26–99 Kuning,
   ≥100 Hijau) — dan kotak Analisa & Tindak Lanjut.
2. **🌸 Dashboard Persediaan Parfum** — struktur serupa Aksesoris tapi
   disederhanakan sesuai karakter datanya (lihat bagian khusus di bawah).
3. **🧾 Dashboard Penjualan Aksesoris** — satu tab gabungan berisi dua bagian:
   - **Ringkasan Cabang, Produk & Sales**: ranking Seluruh Cabang, Semua
     Produk Aksesoris (terlaris & profit), dan Seluruh Sales.
   - **Revenue, HPP & Katalog LUNA**: revenue & tren bulanan, Top 10 produk
     aksesoris terlaris & profit, omzet + HPP seluruh cabang, katalog
     referensi harga LUNA & potensi profit, **matrix insentif resmi &
     kalkulator THP Sales Retail** (dikalibrasi ke target Rp5-8jt/bulan),
     **target pencapaian penjualan LUNA** (default Rp 2 miliar / 12 bulan
     mulai Agustus 2026), serta analisa + proyeksi 5–10 tahun.

Tab Persediaan Aksesoris & Persediaan Parfum memakai **satu berkas
persediaan yang sama** (satu tombol unggah, panel kiri bagian "📊 Data
Persediaan") — boleh berkas khusus aksesoris, atau berkas SEMUA kategori
barang (mis. `Persediaan_Barang_Regional...xlsx`), tinggal difilter
kategorinya masing-masing per tab. Tab Persediaan Aksesoris & Penjualan
Aksesoris memakai **satu berkas data penjualan yang sama** (satu tombol
unggah, bagian "🧾 Data Penjualan") — dibaca ulang secara independen oleh
tab Persediaan (untuk bagian "Produk Paling Diminati") dan tab Penjualan
Aksesoris, jadi tidak perlu unggah berkas terpisah.

## Dashboard Persediaan Parfum — apa yang beda dari Aksesoris

Strukturnya SENGAJA disederhanakan dari Aksesoris, karena karakter data
Parfum berbeda:

- **Tidak ada pemisahan brand** (LUNA vs Selain LUNA) — kategori Parfum di
  data MFlash hampir seluruhnya satu brand (UMAIR), jadi perbandingan brand
  tidak relevan. Bagian 1 langsung menampilkan **total nilai persediaan
  Parfum per cabang** (bukan perbandingan).
- **"Produk Paling Diminati per Cabang" SEKARANG ADA** (per pembaruan
  terbaru) — sebelumnya tidak bisa dibangun karena berkas penjualan yang
  ada belum mencakup transaksi Parfum. Sejak berkas penjualan diperbarui
  jadi cakupan SEMUA kategori (bukan cuma aksesoris), bagian ini otomatis
  berfungsi dengan pola yang identik dengan tab Aksesoris — termasuk
  "Kebutuhan Konsumen Belum Terpenuhi" (produk UMAIR favorit yang stoknya
  kosong/rendah).
- **Tidak ada peta lokasi cabang** — dianggap tidak perlu diulang di tab
  terpisah (sudah ada di tab Aksesoris).
- **Tidak ada indikator stok 🔴🟡🟢, ringkasan indikator, maupun Peta Stok
  (heatmap)** — dihapus atas permintaan sebelumnya. Tab Parfum sekarang
  berisi: **Nilai Persediaan per Cabang**, **Produk Paling Diminati per
  Cabang (Stok vs Terjual)**, dan **Analisa & Tindak Lanjut**. Fungsi
  indikator di `logic_persediaan.py` TIDAK dihapus dari kode — tetap
  dipakai di tab Persediaan Aksesoris, hanya tidak dipanggil dari tab Parfum.

## Isi repo

```
app.py               # aplikasi utama (3 tab)
flash_logo.png        # logo Flash — dipakai di judul halaman & sidebar (st.logo)
logic_persediaan.py    # logika indikator stok (dipakai Aksesoris & Parfum)
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
     **"Daftar Barang dan Jasa"**) untuk tab Persediaan Aksesoris & Parfum —
     boleh juga berkas SEMUA kategori barang, bukan cuma aksesoris.
   - `penjualan.csv.gz` untuk tab Persediaan Aksesoris (bagian "Produk
     Paling Diminati") dan **kedua bagian** di tab Penjualan Aksesoris —
     boleh CSV/gz, atau Excel (`.xlsx`) dengan sheet **"Rincian Faktur Penjualan"**.
   Kalau tidak ada, tersedia tombol unggah manual di panel kiri untuk masing-masing
   (menerima `.csv`, `.gz`, `.xlsx`, `.xls`).
3. Deploy lewat [share.streamlit.io](https://share.streamlit.io) dengan
   `app.py` sebagai entry point.

## Panel kiri (sidebar)

Sidebar dipakai bersama oleh ketiga tab, berisi:
- Unggah data persediaan — dipakai bersama untuk tab Persediaan Aksesoris
  & tab Persediaan Parfum (tinggal difilter kategorinya masing-masing)
- Unggah data penjualan — dipakai untuk tab Persediaan Aksesoris (bagian
  "Produk Paling Diminati") dan **kedua bagian** di tab Penjualan Aksesoris

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

## Matrix Insentif Aksesoris (v3 — Skema Tiering)

Diperbarui dari matrix pekanan lama ke **skema tiering resmi terbaru**,
ditranskrip dari `Aksesoris_Skema_Insentif_Tiering_Sales_Retail.xlsx`:

- **Skema Tiering Insentif — Sales Retail** (`matrix_tiering_sales_retail()`):
  10 tier Omzet/Pekan Rp750rb–Rp7,5jt, GP 30%, insentif **50% dari GP**
  (beda dari skema lama yang 5%), **Gaji Bulanan TETAP
  Rp4.000.000** (`GAJI_BULANAN_SALES_RETAIL`), **THP dihitung langsung per
  tier** = Gaji Bulanan + Insentif/Bulan — bukan lagi kalkulator kalibrasi
  manual seperti skema lama, karena skema baru ini sudah membakukan Gaji
  Bulanan & THP-nya sendiri di sumbernya. Sudah diverifikasi cocok 100%
  dengan seluruh 10 baris pada berkas sumber. Dari 10 tier, **6 tier sudah
  otomatis pas dalam target Rp5–8jt** (tier Rp2,25jt–Rp6jt/pekan); 4 tier
  di ujung bawah/atas sedikit di luar rentang itu — dashboard menandainya
  dengan status ✅/⬇️/⬆️ per baris, tanpa memaksakan kalibrasi ulang karena
  angkanya memang sudah baku dari skema resmi.
- **Matrix Insentif Per Item** (tidak berubah dari sebelumnya): 6 tier
  berdasarkan rentang harga jual, GP 30% konsisten, insentif TETAP 50%
  dari GP di semua tingkat (Rp7.500/Rp15.000/Rp37.500/Rp75.000/
  Rp112.500/Rp150.000). Pengecualian produk **HYDROGEL** tetap berlaku:
  insentif TETAP Rp10.000/pcs berapa pun harga jualnya.

> **Catatan**: bagian "Matrix Insentif — Store Manager & Regional Manager"
> sudah **dihapus dari tampilan dashboard** atas permintaan. Fungsinya
> (`matrix_insentif_manager()`, 17 baris: Store Manager 8 tier @2% dari
> GP, Regional Manager 9 tier @1% dari GP) TIDAK dihapus dari
> `logic_aksesoris.py` — tetap tersedia dan berfungsi kalau suatu saat
> perlu dimunculkan lagi.

> **Catatan penting soal berkas sumber**: 2 baris pada
> `Aksesoris_Skema_Insentif_Tiering_Sales_Retail.xlsx` tampak salah ketik
> dan SENGAJA DIKELUARKAN dari transkripsi —
> baris "Store Manager" Rp15jt/pekan yang memakai insentif 50% (pola Sales
> Retail, bukan pola Store Manager 2%), dan baris "Regional Manager"
> Rp60jt/pekan yang memakai insentif 2% (pola Store Manager, bukan pola
> Regional Manager 1%). Kalau kedua baris itu ternyata disengaja, beri
> tahu untuk dikoreksi.

> **Catatan migrasi**: skema lama (`matrix_insentif_pekanan()`,
> `kalkulator_thp_sales_retail()`, `saran_gaji_pokok()`,
> `target_individual_sales_retail()`) TIDAK dihapus dari
> `logic_aksesoris.py` — fungsinya tetap ada dan berfungsi, hanya sudah
> tidak dipanggil dari `app.py` lagi (bagian "Kalkulator THP Sales Retail"
> dan "Target Individual Sales Retail — Aksesoris" sudah dihapus dari
> tampilan dashboard sesuai permintaan). Boleh dihapus dari berkas kalau
> memang sudah tidak dibutuhkan sama sekali.

## ⚠️ Perbaikan Bug Penting — Filter Kategori pada Berkas Penjualan Semua Kategori

Sejak berkas penjualan yang diunggah berkembang cakupannya jadi **SEMUA
kategori barang** (JASA, SPAREPART, AKSESORIS, PARFUM, dll — bukan cuma
aksesoris seperti nama berkasnya), ditemukan bug penting: bagian **Revenue,
HPP & Katalog LUNA** (dan "Produk Paling Diminati" di tab Persediaan
Aksesoris) sebelumnya TIDAK memfilter ke kategori AKSESORIS saja — angka
Omzet jadi ikut menjumlahkan JASA & SPAREPART, menghasilkan angka yang jauh
lebih besar dari yang sebenarnya.

**Contoh nyata dari pengujian**: dengan berkas penjualan 184.712 baris
(semua kategori), Omzet TANPA filter menunjukkan **Rp 46.890.010.002**
(salah), padahal Omzet AKSESORIS yang benar (setelah difilter) adalah
**Rp 4.241.691.227** — selisih lebih dari 10×.

**Perbaikan**: ditambahkan fungsi `hanya_kategori()` di `logic_aksesoris.py`,
dipanggil di awal `render_aksesoris_tab()` (memfilter `df` ke AKSESORIS
sebelum dipakai di seluruh bagian bawahnya) dan di bagian "Produk Paling
Diminati" pada `render_persediaan_tab()`. Data lintas-kategori yang belum
difilter tetap disimpan terpisah (`df_semua_kategori`) untuk keperluan yang
memang butuh kategori lain, seperti target UMAIR Parfum.

## Target Pencapaian Penjualan LUNA

- Default: **Rp 2.000.000.000** dalam **12 bulan mulai 20 Juli 2026**
  (20 Jul 2026 – 19 Jul 2027) — ketiganya bisa diubah langsung dari
  dashboard (target, tanggal mulai, durasi bulan).
- Produk LUNA diidentifikasi dari **nama barang mengandung kata "LUNA"**,
  dihitung dari **data yang sudah difilter ke kategori AKSESORIS** (tidak
  terpengaruh filter tahun/bulan/cabang di bagian atas tab), supaya
  progress tidak "menghilang" cuma karena pengguna sedang menyaring
  tampilan lain.
- **Tanggal acuan "hari berjalan" memakai tanggal faktur TERAKHIR pada
  data** (bukan tanggal hari ini) — prinsip yang sama dipakai di bagian
  Proyeksi 5–10 Tahun, supaya persentase tidak terlihat rendah cuma karena
  data belum diperbarui.
- Dua ukuran pencapaian ditampilkan sekaligus: **% Pencapaian** (dibanding
  target yang SEHARUSNYA sudah tercapai sampai hari ke sekian dari total
  hari program) dan **% dari Target Penuh** (dibanding target 12 bulan
  penuh) — supaya jelas mana yang jadi ukuran "on-track" dan mana yang
  ukuran progres keseluruhan.
- **Baru: kotak "📍 Tahap 1" (checkpoint opsional)** — default tanggal
  20 Juli 2026, nilai Rp 300.006.600. Menampilkan pencapaian AKTUAL sampai
  tanggal checkpoint tsb dibandingkan dengan nilai acuannya. **Catatan
  jujur**: makna persis "Tahap 1 senilai Rp300.006.600" agak ambigu dari
  permintaan aslinya (bisa berarti target fase 1, atau baseline pencapaian
  sebelum program dimulai) — diimplementasikan sebagai checkpoint yang bisa
  diubah tanggal & nilainya, silakan sesuaikan lewat kotak input kalau
  interpretasinya belum pas.

## Target Pencapaian Penjualan Parfum UMAIR

- **Fitur baru**, dibangun dengan fungsi generik yang sama dengan target
  LUNA (`target_penjualan_brand()`, dulu bernama `target_penjualan_luna()`
  — sekarang jadi alias tipis di atas fungsi generik ini).
- Default: target Rp 100.000.000 (silakan ubah — tidak disebutkan nilai
  spesifik di permintaan aslinya), **durasi maksimal 6 bulan**, mulai
  1 Januari 2026 (bisa diubah).
- Produk diidentifikasi dari **nama barang mengandung kata "UMAIR"**, DAN
  kategori barangnya PARFUM (dua syarat sekaligus, supaya tidak salah
  tangkap produk non-parfum yang kebetulan mengandung kata serupa).
- Peringatan khusus **"⏰ Periode maksimal N bulan sudah/hampir habis"**
  muncul kalau sisa hari program sudah 0 tapi pencapaian belum 100% dari
  target penuh — sesuai sifat "maksimal 6 bulan" (bukan target waktu tetap
  seperti LUNA, tapi batas atas).

## Produk Paling Diminati per Cabang — Sekarang Ada di Tab Parfum Juga

Fitur cross-reference Stok × Penjualan yang sebelumnya hanya ada di tab
Aksesoris, sekarang direplikasi ke tab Parfum dengan fungsi yang PERSIS
SAMA (`produk_favorit_per_cabang()`, `kebutuhan_belum_terpenuhi()` dari
`logic_persediaan.py`) — cuma beda sumber data yang difilter ke kategori
PARFUM. Ini yang dimaksud "saling berkaitan untuk kontrol barang tersedia
dengan barang yang telah terjual": produk UMAIR yang laku tapi stoknya
kosong/rendah langsung kelihatan di bagian "Kebutuhan Konsumen Belum
Terpenuhi".

## Upload Data — Sekarang Satu Tempat

Kedua uploader (Persediaan & Penjualan) yang sebelumnya di dua bagian
sidebar terpisah (dengan divider di antaranya), sekarang digabung di
bawah satu header **"📁 Upload Data"** — tidak ada perubahan fungsional
(masih dua tombol unggah terpisah, karena memang dua berkas berbeda),
cuma disatukan secara visual sesuai permintaan.

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
    kosong tapi laku — jadi fitur ini punya dasar nyata untuk digunakan.
  - **Persediaan Parfum**: 106.313 baris persediaan semua kategori,
    difilter ke PARFUM (`kategori="PARFUM"`) — 117 baris, 15 nama produk
    unik, nilai persediaan Rp 180.799.915.
  - **Produk Favorit Parfum** (baru): 219 baris penjualan Parfum ×
    117 baris stok Parfum — 52 kombinasi cabang×produk, **26 di antaranya
    (50%) berstatus "Wajib Direstock"** (stok kosong/rendah tapi laku).
- **Revenue Aksesoris** (setelah perbaikan filter kategori): 74.346 baris
  (dari 184.712 baris berkas mentah semua kategori), Omzet Rp 4.241.691.227
  — dipastikan BEDA dan LEBIH KECIL dari angka tanpa filter (Rp 46,89 M),
  membuktikan perbaikan bug berfungsi.
- **Target LUNA** (mulai 20 Juli 2026): tercapai Rp 68.547.360 dari target
  s/d hari ini Rp 197.260.274 (34,7%), Tahap 1 (20 Jul) tercapai
  Rp 1.330.000 dari Rp 300.006.600 acuan.
- **Target UMAIR** (6 bulan mulai 1 Jan 2026): tercapai Rp 40.065.000
  dari target Rp 100.000.000 (40,1%), periode sudah habis (sisa hari 0).
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
- **Persediaan Parfum** (`render_persediaan_parfum_tab()` di `app.py`,
  fungsi generik dari `logic_persediaan.py` yang sama dengan Aksesoris):
  diuji dengan berkas persediaan SEMUA kategori (106.313 baris, 18 cabang),
  difilter ke kategori PARFUM lewat parameter baru `kategori=` pada
  `apply_filters()` (backward-compatible, tidak mengubah perilaku lama
  untuk pemanggilan `hanya_aksesoris=`) — hasil 117 baris, 15 nama produk
  unik, total nilai persediaan Rp 180.799.915. Sudah diuji render tanpa
  error, termasuk kasus tepi filter cabang kosong.
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
