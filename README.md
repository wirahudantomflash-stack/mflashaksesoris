# MFlash Dashboard Gadget dan Aksesoris (Persediaan LUNA + Parfum + Penjualan Aksesoris)

**Satu halaman panjang** (bukan tab terpisah — digabung sesuai permintaan),
berisi tiga dashboard berurutan dari atas ke bawah:

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
3. **🧾 Dashboard Penjualan Aksesoris** — berisi dua bagian:
   - **Ringkasan Cabang, Produk & Sales**: ranking Seluruh Cabang, Semua
     Produk Aksesoris (terlaris & profit), dan Seluruh Sales.
   - **Revenue, HPP & Katalog LUNA**: revenue & tren bulanan, Top 10 produk
     aksesoris terlaris & profit, omzet + HPP seluruh cabang, katalog
     referensi harga LUNA & potensi profit, **matrix insentif resmi &
     kalkulator THP Sales Retail** (dikalibrasi ke target Rp5-8jt/bulan),
     **target pencapaian penjualan LUNA** (default Rp 2 miliar / 12 bulan
     mulai 20 Agustus 2026) & **target penjualan Parfum UMAIR** (maksimal
     6 bulan), serta analisa + proyeksi 5–10 tahun.

Ketiga dashboard memakai **satu tempat unggah data** di sidebar ("📁 Upload
Data" — dua tombol: Persediaan & Penjualan) yang dipakai bersama oleh
semuanya, tinggal difilter kategorinya masing-masing per bagian. Karena
ini SATU HALAMAN (bukan tab), semua bagian langsung ter-render begitu data
diunggah — tinggal scroll untuk berpindah antar dashboard, tidak perlu klik
tab.

## 📌 Ringkasan Eksekutif (paling atas halaman)

Bagian ringkas gaya kartu di paling atas halaman, sebelum ketiga dashboard
detail — untuk gambaran cepat tanpa perlu scroll jauh:

- 3 kartu metrik (Omzet Aksesoris LUNA, Selain LUNA, Parfum) + jumlah pcs
  terjual + **Margin (%)** sebagai delta (Laba/Omzet dari kelompok yang sama)
- **Baru**: 3 kartu **Nilai Stok** per kelompok (LUNA/Selain LUNA/Parfum) —
  sumber sama dengan bagian "Nilai Persediaan" di dashboard detailnya
- Grafik batang Omzet per kelompok, dan Kontribusi Cabang (terendah→tertinggi)
- Breakdown bundling LUNA pada transaksi Service (3 metrik: pakai LUNA /
  brand lain / tanpa aksesoris)
- Progress bar target LUNA dan target UMAIR

**Penting**: bagian ini TIDAK menghitung ulang dari nol — memanggil fungsi
yang PERSIS SAMA (`omzet_per_kelompok()`, `kontribusi_cabang_gabungan()`,
`analisa_bundling_brand()`, `target_penjualan_luna()`,
`target_penjualan_brand()`) yang juga dipakai di bagian detail Dashboard
Penjualan Aksesoris — jadi angkanya dijamin selalu konsisten, tidak bisa
"berbeda" dari detailnya. Fungsi `render_ringkasan_eksekutif()` di `app.py`,
dipanggil pertama kali sebelum ketiga dashboard lainnya.

**Diuji dengan data asli** — hasilnya identik dengan angka yang sudah
diverifikasi di bagian "Analisa Mendalam" sebelumnya (LUNA Rp223,5jt,
Selain LUNA Rp4,02M, Parfum Rp45,9jt, bundling 13,1%/65,1%/21,7%, target
LUNA 34,7%, target UMAIR 40,1%) — termasuk kasus tepi data Persediaan belum
diunggah (bagian stok dilewati dengan pesan info, bukan error) dan berkas
Penjualan rincian satu cabang tanpa nama cabang terisi (`MissingCabangColumn`
tertangani dengan pesan yang mengarahkan ke bagian pengisian nama cabang).

**Temuan dari kartu Margin & Nilai Stok yang baru ditambahkan**: LUNA
punya margin tertinggi (56,0%), disusul Selain LUNA (40,1%), Parfum
paling rendah (17,7%) — Nilai Stok: LUNA Rp285,1jt, Selain LUNA Rp934,0jt,
Parfum Rp180,8jt.

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

Sidebar dipakai bersama oleh SELURUH bagian di halaman, berisi:
- Unggah data persediaan — dipakai bersama untuk bagian Persediaan Aksesoris
  & bagian Persediaan Parfum (tinggal difilter kategorinya masing-masing)
- Unggah data penjualan — dipakai untuk bagian Persediaan Aksesoris/Parfum
  ("Produk Paling Diminati") dan **kedua bagian** di bagian Penjualan Aksesoris

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

- Default: **Rp 2.000.000.000** dalam **12 bulan mulai 20 Agustus 2026**
  (20 Jul 2026 – 19 Jul 2027) — ketiganya bisa diubah langsung dari
  dashboard (target, tanggal mulai, durasi bulan).
- **Baru: pemilih Periode Samurai** (checkbox "Gunakan Periode Samurai") —
  saat aktif, pengguna tinggal pilih salah satu dari 6 periode kuartalan
  (Samurai 39–44, Jul 2026–Des 2027) lewat dropdown, dan tanggal mulai +
  durasi otomatis terisi (3 bulan per periode) — tidak perlu isi tanggal
  manual. Matikan checkbox untuk kembali ke mode tanggal manual + durasi
  bebas (mis. untuk periode 12 bulan lintas kuartal seperti sebelumnya).
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

> **Perubahan dari versi sebelumnya**: kotak checkpoint "📍 Tahap 1"
> generik (yang dulu ada di sini, mengevaluasi pencapaian PERSIS di satu
> tanggal saja) **dihapus** dan digantikan bagian
> "📍 Monitoring Pencapaian Cabang — Tahap 1" di bawah, yang lebih akurat
> secara konsep — lihat penjelasannya di bagian tersendiri.

### 📋 Monitoring Pencapaian per Cabang

Tabel dengan **9 kolom persis sesuai spesifikasi**: Cabang, Target, Result,
Expected, % Actual, % Expected, GAP, Target Kejar Per Hari, Sisa Hari.

- Fungsi `target_brand_per_cabang()` di `logic_aksesoris.py` — generik
  (bisa dipakai untuk brand apa saja lewat parameter `keyword`, tidak
  cuma LUNA), mengikuti periode yang sama dengan ringkasan jaringan di
  atasnya (Samurai atau manual).
- **Target dibagi RATA** ke seluruh cabang secara default (Target Total ÷
  jumlah cabang) — parameter `target_per_cabang` (dict) tersedia di fungsi
  kalau nanti perlu distribusi tidak rata per cabang, belum diekspos ke UI
  untuk tabel ini (tapi SUDAH dipakai untuk tabel Tahap 1 di bawah).
- **Result dihitung OTOMATIS** dari data penjualan LUNA aktual per cabang
  pada periode terpilih — bukan input manual seperti versi Excel
  sebelumnya, jadi selalu real-time mengikuti data yang diunggah.
- **GAP** = Result − Expected (positif = di atas target seharusnya,
  negatif = di bawah/tertinggal).
- Tabel diurutkan dari **% Actual TERENDAH** (cabang paling tertinggal di
  atas).
- **Baru: baris rekapan "TOTAL JARINGAN"** di paling bawah (fungsi
  `tambah_baris_total()`) — kolom Rp dijumlahkan langsung, tapi kolom %
  DIHITUNG ULANG dari rasio total (Result total ÷ Target total), BUKAN
  dijumlah atau dirata-rata mentah, supaya tetap akurat secara matematis
  (rata-rata dari beberapa persentase tidak selalu sama dengan persentase
  dari totalnya). "Sisa Hari" di baris total diambil dari baris pertama
  (sama untuk semua cabang dalam satu periode).
- **Baru: warna indikator berbasis AMBANG BATAS** (bukan gradasi kontinu
  seperti sebelumnya) — fungsi `warna_indikator_pencapaian()`: 🔴 Merah
  jika % Actual < 85%, 🟡 Kuning jika 85–99%, 🟢 Hijau jika ≥ 100%.

**Diuji dengan data asli** (Samurai 39, Target Rp2M dibagi 18 cabang =
Rp111,1jt/cabang): cabang paling tertinggal **Warbong** (0,8% actual),
paling unggul **Radjiman** (22,5% actual), baris TOTAL JARINGAN terverifikasi
Target = Rp 2.000.000.000 (sum benar) dan % Actual = 5,2% (dihitung dari
rasio total, cocok dengan Result total ÷ Target total). Termasuk kasus
tepi: periode masa depan tanpa data (Result=0 di semua cabang, bukan
error), dan data kosong total (tabel kosong dengan aman).

### 📍 Monitoring Pencapaian Cabang — Bertahap, menuju Rp 2 Miliar

Bagian khusus untuk milestone bertahap (Tahap 1, 2, 3, dst) menuju target
jaringan LUNA total **Rp 2.000.000.000** — Tahap 1 adalah tahap PERTAMA
dari rangkaian ini (target tetap Rp 300.006.600, **dengan distribusi TIDAK
RATA per cabang**). Kolom tiap tahap: Cabang, Target, Result, % Actual, GAP
(lebih ringkas dari tabel "Monitoring Pencapaian per Cabang" di atasnya —
tanpa Expected/Target Kejar Per Hari/Sisa Hari, karena tiap tahap adalah
milestone kumulatif dengan tanggal evaluasi fleksibel, bukan program
dengan tanggal akhir & laju harian tetap).

- **`TARGET_TAHAP1_LUNA_PER_CABANG`** di `logic_aksesoris.py`: dict 18
  cabang dengan nilai spesifik (Klender Rp16.690.500, Bintara
  Rp16.892.100, 16 cabang lain masing-masing Rp16.651.500) — **dijamin
  totalnya persis Rp 300.006.600**, diverifikasi baris per baris.
- **Koreksi konsep #1**: tanggal 20 Agustus 2026 adalah tanggal produk
  LUNA **mulai didistribusikan** ke seluruh cabang (bukan tanggal
  checkpoint tunggal untuk dievaluasi). Versi SEBELUMNYA salah — mengevaluasi
  pencapaian PERSIS di tanggal 20 Agustus itu sendiri, sehingga hasilnya
  sangat kecil (cuma Rp 1.330.000, karena cuma menangkap transaksi HARI
  ITU saja). Sekarang fungsi `monitoring_tahap_per_cabang()` menghitung
  **KUMULATIF sejak 20 Agustus sampai tanggal evaluasi**.
- **Koreksi konsep #2 — pengecualian Hydrogel**: target Rp 300.006.600
  ini khusus untuk LUNA **SELAIN varian Hydrogel** (LUNA Hydrogel punya
  skema/target tersendiri, terpisah dari Tahap 1 ini). Parameter
  `keyword_kecuali="HYDROGEL"` pada `monitoring_tahap_per_cabang()` —
  nama barang yang mengandung "LUNA" DAN "HYDROGEL" sekaligus (mis.
  "LUNA HYDROGEL MATERIAL CLEAR") dikeluarkan dari Result. Parameter
  bersifat opsional & backward-compatible (default `None` = tidak
  mengecualikan apa pun). **Dampak nyata**: koreksi ini mengubah urutan
  cabang secara signifikan — Radjiman yang SEBELUM koreksi terlihat
  memimpin (96,2%, ternyata sebagian besar dari penjualan Hydrogel, bukan
  LUNA reguler) turun jadi cuma 5,4% setelah dikoreksi; Cilangkap yang
  sekarang benar-benar memimpin (54,3%). Semua tahap (bukan cuma Tahap 1)
  memakai pengecualian ini secara konsisten.
- **Tanggal Mulai Tahap 1 sekarang BISA DIISI SENDIRI** (default 20 Agustus
  2026, tanggal barang masuk/drop produk — direvisi dari perkiraan awal
  20 Juli) — diubah dari versi sebelumnya yang terkunci,
  karena transaksi riil di tiap cabang bisa mulai beberapa hari setelah
  tanggal drop (mis. 20–26 Agustus 2026, tergantung kapan cabang mulai
  menjual). Date picker terpisah di atas tabel, mempengaruhi seluruh
  perhitungan Tahap 1. Peringatan otomatis muncul kalau Tanggal Mulai
  diset SETELAH Tanggal Evaluasi (Result akan 0 untuk semua cabang).
  Tahap berikutnya tetap punya tanggal mulai sendiri-sendiri (diatur saat
  menambahkan).
- **Tanggal Evaluasi fleksibel, dipakai bersama SELURUH tahap** — default
  otomatis memakai **tanggal faktur TERAKHIR pada data** (bukan tanggal
  hari ini), tapi bisa diubah manual lewat satu date picker di atas
  (berlaku untuk Tahap 1 maupun tahap tambahan sekaligus, supaya semua
  tahap dievaluasi "sampai tanggal yang sama").
- Baris **TOTAL JARINGAN** dan **warna indikator ambang batas** (sama
  seperti tabel utama: 🔴<85% · 🟡85–99% · 🟢≥100%) diterapkan di SETIAP
  tahap, memakai fungsi generik yang sama (`tambah_baris_total()`,
  `warna_indikator_pencapaian()`).

**➕ Tahap Berikutnya (BARU) — sistem dinamis, bukan terbatas Tahap 1 saja**

- Kotak angka "Jumlah tahap tambahan" (0–6) — menambah *expander* baru
  per tahap (Tahap 2, Tahap 3, dst).
- Tiap tahap tambahan punya input sendiri: **Nama Tahap** (bisa diganti,
  mis. "Tahap 2 - Q4 2026"), **Tanggal Mulai** (bebas, tidak harus 20 Agustus),
  **Target Total (Rp)**.
- **Target per cabang untuk tahap tambahan bisa diedit langsung**
  (`st.data_editor`) — default dibagi rata (Target Total ÷ 18 cabang),
  tapi bisa disesuaikan tidak rata seperti Tahap 1 kalau perlu.
- Setiap tahap tambahan otomatis dapat tabel monitoring + rincian produk
  yang sama persis dengan Tahap 1 (fungsi `_render_tahap_block()` di
  `app.py` — satu fungsi dipakai ulang untuk semua tahap, supaya
  konsisten & tidak duplikasi kode).

**📊 Ringkasan Kumulatif Seluruh Tahap (BARU)**

- 4 kartu metrik: **Target Kumulatif** (jumlah target SEMUA tahap yang
  didefinisikan), **Result Kumulatif**, **% Pencapaian Kumulatif**, dan
  **Sisa Ruang Target** (Rp 2.000.000.000 dikurangi Target Kumulatif).
- Progress bar visual terhadap batas Rp 2 Miliar.
- **Peringatan otomatis** kalau Target Kumulatif seluruh tahap sudah
  MELEBIHI Rp 2.000.000.000 — supaya tidak kebablasan saat menambah
  tahap baru.

**🔍 Rincian Produk per Cabang (BARU)** — di setiap blok tahap:

- Dropdown pilih SATU cabang (dari 18 cabang) → tabel rincian **jenis
  barang LUNA (selain Hydrogel) apa saja yang terjual dan berapa
  kuantitasnya**, diurutkan dari omzet terbesar, memakai fungsi baru
  `detail_produk_brand_cabang()` di `logic_aksesoris.py`.
- Contoh hasil nyata (Cilangkap, Tahap 1): 5 jenis produk — LUNA DATA
  CABLE TYPE-C CB-2E terlaris (229 pcs, Rp4.609.000), diikuti LUNA DATA
  CABLE MICRO CB-2E (166 pcs), dst — total 430 pcs dari 5 jenis produk.
- Cabang tanpa penjualan pada periode tsb (mis. Karawang) menampilkan
  pesan info yang jelas, bukan tabel kosong yang membingungkan.

**Diuji dengan data asli**: simulasi 3 tahap sekaligus (Tahap 1 asli +
2 tahap tambahan contoh Rp300jt & Rp500jt) — Target Kumulatif terhitung
benar Rp1.100.006.600 (55% dari batas Rp2M), Result Kumulatif
Rp59.534.860, sisa ruang Rp899.993.400 — semua angka terverifikasi manual.
Peringatan "melebihi Rp2M" juga diuji terpicu dengan benar saat target
kumulatif disimulasikan melebihi batas. Tidak ada bentrok kunci widget
sampai 6 tahap tambahan sekaligus (38 kunci unik diverifikasi).

**Diuji: Tanggal Mulai Tahap 1 yang bisa diisi sendiri** — mulai 20 Agustus
menghasilkan Result Rp21.016.500, mulai 26 Agustus menghasilkan
Rp3.000.000 (selisih Rp18.016.500, sesuai penjualan tanggal 20–25 Agustus
yang ikut/tidak ikut terhitung tergantung tanggal mulai yang dipilih).
Kasus tepi (Tanggal Mulai diset SETELAH Tanggal Evaluasi) menghasilkan
Result 0 di semua cabang dengan peringatan yang jelas, bukan angka
negatif/error.

## Analisa Mendalam: LUNA, Selain LUNA & Parfum UMAIR

**Fitur baru**, ditempatkan di tab Penjualan Aksesoris sebelum bagian
grafik perbandingan — tiga sub-bagian dengan struktur yang mirip:

**1️⃣ Aksesoris LUNA** dan **3️⃣ Parfum UMAIR** (struktur identik, beda sumber
data): masing-masing menampilkan
- **Stok**: Nilai Stok, Qty Stok (dari data Persediaan, difilter kategori
  & brand yang sesuai)
- **Sudah Terjual**: Omzet Terjual, Qty Terjual, Rata-rata Qty/Omzet
  Terjual per Hari (dihitung dari jumlah HARI yang punya transaksi
  tercatat, bukan dibagi rata sepanjang kalender)
- **Bundling pada Transaksi Service**: Qty yang terbundling (nota-nya juga
  berisi kategori lain), dan breakdown 3 kelompok nota Service — (a) pakai
  brand target, (b) pakai brand aksesoris LAIN (sesuai pengecualian SE
  Bundling kalau brand target kosong — BUKAN pelanggaran), (c) **SAMA
  SEKALI TIDAK ADA aksesoris** (temuan pelanggaran murni)
- **Temuan**: tabel Cabang + Nomor Nota untuk kelompok (c), bisa difilter
  per cabang, dengan ringkasan jumlah per cabang di atasnya, dan tombol
  unduh CSV lengkap.

**2️⃣ Aksesoris Selain LUNA** (Vivan, Robot, Anker, dll): rincian LENGKAP
semua barang (per Cabang × Nama Barang) dengan kotak pencarian nama
produk/brand, diurutkan dari nilai stok terbesar, plus unduh CSV lengkap
(tidak dipotong oleh pencarian).

**Fungsi baru di `logic_aksesoris.py`**: `ringkasan_stok_dan_terjual_brand()`,
`analisa_bundling_brand()`, `rincian_produk_brand()`.

**Catatan penting soal "bundling"**: definisi "nota terbundling" mengikuti
`prompt_dashboard_bundling.md` — satu nota dianggap bundling kalau memuat
minimal satu item AKSESORIS dan minimal satu item kategori lain. Dashboard
SENGAJA memisahkan "nota Service tanpa brand target tapi pakai brand lain"
dari "nota Service tanpa aksesoris sama sekali", karena Surat Edaran SE
mengizinkan penggantian brand kalau brand target kosong — mencampur
keduanya sebagai satu angka "pelanggaran" akan menyesatkan.

**Diuji dengan data asli** (184.712 baris penjualan semua kategori,
59.184 nota Service):
- LUNA: Nilai Stok Rp 285.094.168, Omzet Terjual Rp 223.513.860 (rata-rata
  54 unit/hari dari 159 hari data). Bundling: 7.771 nota pakai LUNA
  (13,1%), 38.551 pakai brand lain (65,1%, sesuai pengecualian),
  **12.867 nota (21,7%) SAMA SEKALI TIDAK ADA aksesoris** (temuan).
- Selain LUNA: 20.915 baris rincian (Cabang × Produk), termasuk brand
  Vivan, Robot, Anker, dll — diuji filter pencarian ("VIVAN" → 765 baris).
- Parfum UMAIR: Nilai Stok Rp 175.717.670, Omzet Terjual Rp 45.185.000
  (rata-rata 1,9 unit/hari). Bundling UMAIR sangat rendah (22 nota, 0,04%)
  — wajar karena UMAIR kategori terpisah (Parfum), bukan bagian dari
  program bundling aksesoris yang sama.
- **Bug ditemukan & diperbaiki**: filter cabang di panel atas awalnya
  belum diterapkan ke deteksi bundling (`df_semua_kategori` belum
  difilter) — temuan selalu menampilkan SEMUA cabang meski sudah difilter
  ke satu cabang. Sudah diperbaiki (`df_semua_kategori_f`) dan
  diverifikasi: filter ke cabang Bintara saja menghasilkan 709 nota temuan
  (bukan lagi 12.867 semua cabang), seluruhnya benar dari Bintara.

## Pencapaian per Periode Samurai & Perbandingan Antar Periode

**Fitur baru**, ditempatkan di tab Penjualan Aksesoris setelah bagian
grafik LUNA vs Selain LUNA vs Parfum:

- **Periode "Samurai"** — penamaan kuartalan internal, ditanam sebagai
  konstanta `PERIODE_SAMURAI` di `logic_aksesoris.py`, sekarang mencakup
  **8 periode**: Samurai 37 (Jan–Mar 2026) sampai Samurai 44
  (Okt–Des 2027) — diperluas dari 4 periode awal (37–40) atas permintaan
  untuk mendukung pemilih periode di bagian Target LUNA (lihat di bawah).
  Satu sumber data dipakai bersama oleh kedua bagian (Perbandingan Antar
  Periode di sini, dan Monitoring per Cabang di bagian Target LUNA).
- **Pilihan pencapaian per periode**: dropdown untuk memilih SATU periode,
  menampilkan Omzet, Gross Profit, Margin, jumlah nota & item terjual untuk
  LUNA vs Selain LUNA pada periode itu saja (fungsi
  `pencapaian_kelompok_periode()`).
- **Perbandingan antar periode**: tabel + 2 grafik batang (Omzet dan Gross
  Profit) yang menyandingkan SELURUH periode Samurai sekaligus, LUNA vs
  Selain LUNA berdampingan per periode (fungsi
  `perbandingan_antar_periode_samurai()`). Periode yang belum ada datanya
  (mis. Samurai 40 kalau data terbaru belum sampai Oktober 2026) otomatis
  tidak muncul di perbandingan, bukan tampil sebagai baris kosong/error.
- Dihitung dari data **AKSESORIS yang sudah difilter kategori** (`df`,
  bukan `dff`) — **tidak terpengaruh filter tahun/bulan** di bagian atas
  tab, karena periode Samurai sudah menentukan rentang tanggalnya sendiri
  secara eksplisit (mengikuti prinsip yang sama dengan Target LUNA/UMAIR).

**Diuji dengan data asli** (184.712 baris, data sampai 24 Agustus 2026):
- Samurai 37: LUNA Rp1,2jt (margin 68,8%) vs Selain LUNA Rp1,50M (margin 44,2%)
- Samurai 38: LUNA Rp126,6jt (margin 54,6%) vs Selain LUNA Rp1,55M (margin 39,6%)
- Samurai 39: LUNA Rp95,7jt (margin 57,6%) vs Selain LUNA Rp963,1jt (margin 34,4%)
- Samurai 40: belum ada data (benar, karena data terbaru baru sampai Agustus)
- Terlihat tren jelas: **omzet LUNA melonjak drastis dari Samurai 37 ke 38**
  (Rp1,2jt → Rp126,6jt) — konsisten dengan program bundling LUNA yang mulai
  digalakkan pertengahan 2026.
- Termasuk kasus tepi: periode tanpa data (pesan info, bukan error), dan
  data kosong total (semua fungsi mengembalikan tabel kosong dengan aman).

## Grafik Penjualan LUNA vs Selain LUNA vs Parfum & Kontribusi Cabang

**Fitur baru**, ditempatkan di tab Penjualan Aksesoris setelah bagian
"Omzet & HPP Seluruh Cabang":

- **Grafik perbandingan Omzet 3 kelompok**: Aksesoris LUNA, Aksesoris
  Selain LUNA, dan Parfum (kategori terpisah) — fungsi
  `omzet_per_kelompok()` di `logic_aksesoris.py`, mengikuti filter
  tahun/bulan/cabang yang sama dengan bagian atasnya (Parfum diambil dari
  `df_semua_kategori` yang difilter manual dengan filter yang sama, karena
  kategorinya beda dari data Aksesoris yang sudah difilter di awal fungsi).
- **Diagram indikator kontribusi cabang**: total omzet Aksesoris + Parfum
  digabung per cabang, **diurutkan dari kontribusi PALING RENDAH ke PALING
  BESAR** (fungsi `kontribusi_cabang_gabungan()`) — supaya cabang yang
  paling perlu didorong langsung terlihat di paling atas grafik/tabel.
  Kolom "Porsi Kontribusi (%)" selalu berjumlah tepat 100% (diverifikasi).
- **Diuji dengan data asli**: 3 kelompok (LUNA Rp223,5jt, Selain LUNA
  Rp4,02 M, Parfum Rp45,9jt), 18 cabang terurut dari Cibubur (0,20%
  kontribusi, terendah) sampai Dramaga (14,01%, tertinggi) — termasuk kasus
  tepi filter ke satu cabang saja dan filter yang menghasilkan data kosong.

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
- **Target LUNA** (mulai 20 Agustus 2026, direvisi dari perkiraan awal
  20 Juli — sesuai koreksi tanggal barang masuk): tercapai Rp 24.957.500
  dari target s/d hari ini Rp 38.356.164 (65,1%), baru hari ke-7 dari
  365 hari program.
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
