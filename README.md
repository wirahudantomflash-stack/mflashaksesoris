# MFlash Dashboard Gadget dan Aksesoris (Persediaan LUNA + Parfum + Penjualan Aksesoris)

> ## ⏸️ Bagian Parfum SEMENTARA DISEMBUNYIKAN dari dashboard
>
> Atas permintaan, **seluruh bagian yang berkaitan dengan Parfum** (Dashboard
> Persediaan Parfum, sub-bagian Parfum UMAIR di Analisa Mendalam, target
> penjualan UMAIR, kolom/kartu Parfum di grafik & Ringkasan Eksekutif)
> **disembunyikan dari tampilan** — dikendalikan oleh SATU flag di
> `app.py`:
> ```python
> TAMPILKAN_PARFUM = False
> ```
> **Kode/logikanya TIDAK dihapus** — cuma dilewati saat render. Untuk
> memunculkan kembali semua bagian Parfum kapan saja, ubah nilai flag ini
> jadi `True` dan simpan ulang `app.py` (tidak perlu ubah bagian lain).
> Bagian README di bawah yang membahas Parfum tetap dipertahankan sebagai
> dokumentasi — anggap sebagai referensi untuk saat fitur ini diaktifkan
> kembali.

> ## ⏸️ Ringkasan Eksekutif dan Matrix Insentif juga SEMENTARA DISEMBUNYIKAN
>
> Dua flag serupa, mekanisme & alasan sama seperti di atas:
> ```python
> TAMPILKAN_RINGKASAN_EKSEKUTIF = False   # bagian kartu ringkasan paling atas halaman
> TAMPILKAN_MATRIX_INSENTIF = False       # Skema Tiering Sales Retail + Matrix Insentif Per Item
> ```
> **Ringkasan Eksekutif**: seluruh bagian "📌 Ringkasan Eksekutif" (kartu
> Omzet/Margin/Nilai Stok per kelompok, grafik, breakdown bundling, progress
> target) di paling atas halaman tidak dirender sama sekali — halaman
> langsung mulai dari "📊 Dashboard Persediaan Aksesoris".
> **Matrix Insentif**: seluruh bagian "💸 Matrix Insentif Aksesoris" (Skema
> Tiering Sales Retail 10 tier + expander Matrix Insentif Per Item) di
> dalam Dashboard Penjualan Aksesoris tidak dirender — bagian sebelumnya
> (Katalog Referensi Harga LUNA) langsung disambung ke bagian sesudahnya
> ("🎯 Target Pencapaian Penjualan Aksesoris").
> Sama seperti flag Parfum: kode/logikanya tetap ada, cuma dilewati saat
> render, dan bisa dimunculkan lagi kapan saja dengan mengubah nilai flag
> jadi `True`.

**Satu halaman panjang** (bukan tab terpisah — digabung sesuai permintaan),
berisi dashboard berurutan dari atas ke bawah:

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
   **⏸️ Saat ini disembunyikan** (lihat catatan `TAMPILKAN_PARFUM` di atas).
3. **🧾 Dashboard Penjualan Aksesoris** — berisi dua bagian:
   - **Ringkasan Cabang, Produk & Sales**: ranking Seluruh Cabang, Semua
     Produk Aksesoris (terlaris & profit), dan Seluruh Sales.
   - **Revenue, HPP & Katalog LUNA**: revenue & tren bulanan, Top 10 produk
     aksesoris terlaris & profit, omzet + HPP seluruh cabang, katalog
     referensi harga LUNA & potensi profit, **matrix insentif resmi &
     kalkulator THP Sales Retail** (dikalibrasi ke target Rp5-8jt/bulan)
     **⏸️ saat ini disembunyikan**,
     **target pencapaian penjualan LUNA** (default Rp 2 miliar / 12 bulan
     mulai 20 Agustus 2026), serta analisa + proyeksi 5–10 tahun.
     (Target penjualan Parfum UMAIR **⏸️ saat ini disembunyikan**.)
4. **📦 Dashboard Pembelian & Perbandingan Penjualan Aksesoris** — sudah
   AKSESORIS-only sejak awal dibuat, tidak terpengaruh flag ini sama sekali.

Seluruh dashboard memakai **satu tempat unggah data** di sidebar ("📁 Upload
Data" — tiga tombol: Persediaan, Penjualan, Pembelian) yang dipakai bersama
oleh semuanya, tinggal difilter kategorinya masing-masing per bagian. Karena
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
app.py               # aplikasi utama (satu halaman, 4 dashboard)
flash_logo.png        # logo Flash — dipakai di judul halaman & sidebar (st.logo)
logic_persediaan.py    # logika indikator stok (dipakai Aksesoris & Parfum)
logic_penjualan.py    # logika olah data penjualan/cabang (umum)
logic_aksesoris.py     # logika olah data revenue penjualan aksesoris
logic_pembelian.py     # logika olah data pembelian/pemasok — AKTIF lagi
requirements.txt      # dependensi untuk Streamlit Cloud
```

> **Penting:** `flash_logo.png` **wajib** ada di root repo, sejajar dengan
> `app.py` — dipanggil lewat `st.set_page_config(page_icon="flash_logo.png")`
> dan `st.logo("flash_logo.png")`. Kalau berkas ini tidak diunggah, aplikasi
> akan gagal jalan (`FileNotFoundError`) karena keduanya dipanggil di baris
> paling awal skrip.

> **Catatan (diperbarui):** `logic_pembelian.py` sebelumnya sempat TIDAK
> dipanggil dari `app.py` (sejak tab Pembelian versi awal diganti jadi tab
> Persediaan Aksesoris) — **sekarang AKTIF lagi**, dipakai untuk bagian
> "📦 Dashboard Pembelian & Perbandingan Penjualan Aksesoris" (kriteria
> "Total Pembelian Aksesoris — Pemasok LUNA"). Struktur modulnya ternyata
> masih cocok persis dengan skema kolom berkas Faktur Pembelian terbaru,
> jadi tidak perlu ditulis ulang.

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
- **Unggah data pembelian** (BARU) — khusus dipakai untuk bagian "📦 Dashboard
  Pembelian & Perbandingan Penjualan Aksesoris" (total pembelian per pemasok)

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

## Target Pencapaian Penjualan Aksesoris — LUNA vs Semua Aksesoris

**Baru: radio button "Target untuk"** — 2 pilihan: **Target LUNA** (brand
spesifik, seperti sebelumnya) atau **Target Semua Aksesoris** (seluruh
kategori AKSESORIS, tidak dibatasi brand). Berlaku untuk SELURUH bagian di
bawahnya (ringkasan jaringan maupun tabel per cabang) — pindah mode,
semua angka otomatis ikut menyesuaikan.

- Perubahan di `logic_aksesoris.py`: `target_penjualan_brand()` dan
  `target_brand_per_cabang()` sekarang menerima `keyword=None` yang
  berarti TIDAK memfilter brand sama sekali (seluruh baris kategori
  AKSESORIS dihitung) — sebelumnya `keyword` wajib diisi. Parameter
  default tetap `"LUNA"`, jadi kompatibel dengan pemanggilan lama yang
  sudah ada (diverifikasi: hasil identik dengan versi sebelum perubahan).
- Label tombol, judul sub-bagian, nama file unduhan CSV, dan teks
  penjelasan otomatis menyesuaikan mode yang dipilih (mis. "Monitoring
  Pencapaian per Cabang — LUNA" vs "— Semua Aksesoris").
- Default: **Rp 2.000.000.000** dalam **12 bulan mulai 20 Agustus 2026**
  — ketiganya bisa diubah langsung dari dashboard (target, tanggal mulai,
  durasi bulan), berlaku untuk mode manapun yang dipilih.
- **Pemilih Periode Samurai** (checkbox "Gunakan Periode Samurai") —
  saat aktif, pengguna tinggal pilih salah satu dari 6 periode kuartalan
  (Samurai 39–44, Jul 2026–Des 2027) lewat dropdown, dan tanggal mulai +
  durasi otomatis terisi (3 bulan per periode) — tidak perlu isi tanggal
  manual. Matikan checkbox untuk kembali ke mode tanggal manual + durasi
  bebas (mis. untuk periode 12 bulan lintas kuartal seperti sebelumnya).
- Mode **LUNA**: produk diidentifikasi dari **nama barang mengandung kata
  "LUNA"**. Mode **Semua Aksesoris**: seluruh baris kategori AKSESORIS
  dihitung tanpa filter nama. Keduanya dihitung dari **data yang sudah
  difilter ke kategori AKSESORIS** (tidak terpengaruh filter tahun/bulan/
  cabang di bagian atas tab), supaya progress tidak "menghilang" cuma
  karena pengguna sedang menyaring tampilan lain.
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

### 📋 Monitoring Pencapaian per Cabang — LUNA / Semua Aksesoris

Tabel dengan **9 kolom persis sesuai spesifikasi**: Cabang, Target, Result,
Expected, % Actual, % Expected, GAP, Target Kejar Per Hari, Sisa Hari.
Sekarang mengikuti mode yang dipilih di radio button "Target untuk"
(LUNA atau Semua Aksesoris) — judul, label, dan nama file unduhan
otomatis menyesuaikan.

- Fungsi `target_brand_per_cabang()` di `logic_aksesoris.py` — generik
  (bisa dipakai untuk brand apa saja lewat parameter `keyword`, termasuk
  `keyword=None` untuk "tanpa filter brand"/Semua Aksesoris), mengikuti
  periode yang sama dengan ringkasan jaringan di atasnya (Samurai atau
  manual).
- **Target per cabang sekarang BISA DIEDIT LANGSUNG** (`st.data_editor`) —
  tabel isian muncul sebelum tabel monitoring, default terisi dibagi RATA
  (Target Total ÷ jumlah cabang), tapi tiap baris bisa disesuaikan manual
  kalau distribusinya tidak mau rata (mis. cabang besar dikasih target
  lebih tinggi). Perubahan pada tabel isian langsung dipakai sebagai
  `target_per_cabang` di `target_brand_per_cabang()` — parameter yang
  sebelumnya sudah ada di fungsi tapi belum diekspos ke UI untuk tabel ini
  (kini sudah).
- **Result dihitung OTOMATIS** dari data penjualan aktual per cabang
  pada periode terpilih (LUNA saja, atau seluruh AKSESORIS tergantung
  mode) — bukan input manual seperti versi Excel sebelumnya, jadi selalu
  real-time mengikuti data yang diunggah.
- **GAP** = Result − Expected (positif = di atas target seharusnya,
  negatif = di bawah/tertinggal).
- Tabel diurutkan dari **% Actual TERENDAH** (cabang paling tertinggal di
  atas).
- **Baris rekapan "TOTAL JARINGAN"** di paling bawah (fungsi
  `tambah_baris_total()`) — kolom Rp dijumlahkan langsung, tapi kolom %
  DIHITUNG ULANG dari rasio total (Result total ÷ Target total), BUKAN
  dijumlah atau dirata-rata mentah, supaya tetap akurat secara matematis
  (rata-rata dari beberapa persentase tidak selalu sama dengan persentase
  dari totalnya). "Sisa Hari" di baris total diambil dari baris pertama
  (sama untuk semua cabang dalam satu periode).
- **Warna indikator berbasis AMBANG BATAS** (bukan gradasi kontinu
  seperti sebelumnya) — fungsi `warna_indikator_pencapaian()`: 🔴 Merah
  jika % Actual < 85%, 🟡 Kuning jika 85–99%, 🟢 Hijau jika ≥ 100%.

**Diuji dengan data asli** (Samurai 39, Target Rp2M): mode **LUNA**
tercapai Rp104.069.860 (8,4% dari target-sampai-hari-ini); mode **Semua
Aksesoris** tercapai Rp1.092.514.916 (88,2%) — perbedaan besar ini masuk
akal karena Semua Aksesoris mencakup seluruh brand, bukan cuma LUNA.
Kedua mode diuji render tabel per cabang tanpa error. Verifikasi
backward-compatibility: pemanggilan lama tanpa parameter `keyword`
eksplisit tetap default ke `"LUNA"`, hasil identik dengan sebelum
perubahan ini. Termasuk kasus tepi: periode masa depan tanpa data
(Result=0 di semua cabang, bukan error), dan data kosong total (tabel
kosong dengan aman).

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
  totalnya persis Rp 300.006.600**, diverifikasi baris per baris. Dict ini
  hanya dipakai sebagai NILAI AWAL (seed) — **sekarang bisa diedit
  langsung** lewat tabel isian (`st.data_editor`) yang muncul sebelum
  tabel monitoring Tahap 1, kalau ada revisi target per cabang.
- **🐛 Bug ditemukan & diperbaiki: nama cabang "Karawang" vs "Telukjambe"**
  — dict ini SEMPAT salah menulis salah satu cabang sebagai "Karawang",
  padahal nama cabang yang benar (dan konsisten dengan seluruh data
  penjualan/persediaan asli, serta data lokasi cabang di
  `logic_persediaan.py`) adalah **"Telukjambe"** ("Karawang" adalah nama
  KABUPATEN/wilayahnya, bukan nama cabang). Akibatnya, penjualan LUNA dari
  Telukjambe **selalu tampil Rp0** di tabel Tahap 1 — bukan karena memang
  tidak ada penjualan, tapi karena `monitoring_tahap_per_cabang()`
  mencari data dengan nama "Karawang" yang tidak pernah cocok dengan data
  asli ("Telukjambe"). **Terverifikasi dengan data asli**: periode 1 Jul–
  30 Ags 2026, Telukjambe punya Rp 3.461.000 penjualan LUNA (selain
  Hydrogel) yang sebelumnya hilang dari total — total jaringan yang benar
  adalah Rp 100.598.860, bukan Rp 97.137.860 (versi sebelum perbaikan).
  Sudah diperbaiki dengan mengganti key dict dari `"Karawang"` menjadi
  `"Telukjambe"` (nilai target Rp16.651.500 tidak berubah, cuma nama
  cabangnya).
- **Koreksi konsep #1**: tanggal 20 Agustus 2026 adalah tanggal produk
  LUNA **mulai didistribusikan** ke seluruh cabang (bukan tanggal
  checkpoint tunggal untuk dievaluasi). Versi SEBELUMNYA salah — mengevaluasi
  pencapaian PERSIS di tanggal 20 Agustus itu sendiri, sehingga hasilnya
  sangat kecil (cuma Rp 1.330.000, karena cuma menangkap transaksi HARI
  ITU saja). Sekarang fungsi `monitoring_tahap_per_cabang()` menghitung
  **KUMULATIF sejak 20 Agustus sampai tanggal evaluasi**.
- **Koreksi konsep #2 — pengecualian Hydrogel (HISTORIS, kini dibalik)**:
  target Rp 300.006.600 SEMPAT dihitung khusus untuk LUNA **SELAIN
  varian Hydrogel** (parameter `keyword_kecuali="HYDROGEL"` pada
  `monitoring_tahap_per_cabang()`), karena LUNA Hydrogel dianggap punya
  skema/target tersendiri. **Perubahan terbaru**: atas permintaan, SEMUA
  tahap (Tahap 1, 2, 3, dst) di bagian "Monitoring Pencapaian Cabang —
  Bertahap" sekarang menghitung **SELURUH produk LUNA, TERMASUK Hydrogel**
  (`keyword_kecuali=None`) — bagian rincian produk per cabang juga ikut
  berubah, sekarang produk seperti "LUNA HYDROGEL MATERIAL CLEAR" muncul
  di daftar (contoh nyata: Radjiman menjual 64 pcs Rp4.730.000 dari produk
  ini, sekarang ikut terhitung). Parameter `keyword_kecuali` tetap ada di
  fungsi (bersifat opsional) kalau suatu saat perlu dikecualikan lagi.
  **Catatan penting**: kata "HYDROGEL" ternyata juga muncul di produk
  brand LAIN yang tidak berkaitan (mis. "VIVAN HYDROGEL BASIC ANTI GLARE")
  — fungsi selalu mensyaratkan nama barang mengandung KEDUA kata ("LUNA"
  DAN "HYDROGEL") sebelum dianggap sebagai varian Hydrogel LUNA, supaya
  tidak salah tangkap produk brand lain yang kebetulan mengandung kata
  "Hydrogel" di namanya.
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

**Diuji: Target per cabang yang bisa diedit manual** (tabel utama maupun
Tahap 1) — simulasi mengubah target Dramaga jadi Rp200jt di tabel utama:
kolom Target, % Actual, % Expected, GAP, Target Kejar Per Hari untuk baris
Dramaga langsung ikut berubah sesuai angka baru, dan total keseluruhan
tabel ikut menyesuaikan (dari Rp2.000.000.000 jadi Rp2.088.888.889).
Simulasi serupa untuk Tahap 1 (target Klender diubah jadi Rp20jt): total
Tahap 1 berubah dari Rp300.006.600 jadi Rp303.316.100. Kedua tabel diuji
render (styling + format) tanpa error setelah target diedit.

## 📦 Dashboard Pembelian & Perbandingan Penjualan Aksesoris (BARU)

**Tab besar baru**, ditempatkan paling bawah halaman (setelah Dashboard
Penjualan Aksesoris) — sekarang ada **4 dashboard total** dalam satu
halaman, bukan 3.

**Sumber data baru**: kotak unggah **"📦 Data Pembelian"** ditambahkan di
sidebar (sejajar Persediaan & Penjualan) — sheet "DB Pembelian" atau CSV
skema sama. Nama file default yang dikenali otomatis: `pembelian.csv.gz`,
`pembelian.csv`, `Faktur_Pembelian.xlsx`.

**Modul `logic_pembelian.py` dihidupkan kembali** — sebelumnya sudah ada
di repo tapi TIDAK dipanggil dari `app.py` sejak lama (peninggalan dari
dashboard "Porsi Pemasok" versi awal proyek). Strukturnya (`load_pembelian()`,
`luna_progress()`, `porsi_pemasok()`) ternyata masih cocok persis dengan
skema kolom berkas Faktur Pembelian terbaru — tidak perlu ditulis ulang,
tinggal disambungkan lagi ke `app.py`.

**Fungsi baru di `logic_aksesoris.py`**: `total_hpp_brand()`,
`omzet_mingguan_perbandingan()`, `omzet_cabang_per_bulan()`.

**Keempat kriteria:**

1. **Total Pembelian Aksesoris — Pemasok LUNA**: dari FAKTUR PEMBELIAN
   (bukan penjualan) — total belanja ke pemasok bernama "LUNA"/"Luna"
   (disatukan case-insensitive), dibandingkan dengan total belanja
   aksesoris ke SEMUA pemasok, plus ranking lengkap semua pemasok di
   expander terpisah.
2. **Total HPP Aksesoris LUNA (dari Faktur Penjualan)**: BEDA sumber dari
   poin 1 — ini modal (kolom MODAL/HARGA BELI) dari barang LUNA **TERMASUK
   Hydrogel** yang SUDAH TERJUAL, bukan yang dibeli dari pemasok. (Berbeda
   dari definisi "Tertarget" yang dipakai di bagian lain dashboard — di
   sini sengaja mencakup Hydrogel atas permintaan, karena tujuannya
   melihat total modal barang LUNA yang sudah terjual secara keseluruhan,
   bukan target pencapaian per brand tertentu.) Kedua angka (Pembelian vs
   HPP) sengaja dipisah karena mewakili hal berbeda: satu soal pasokan
   masuk, satu soal biaya barang keluar (terjual). **Diuji dengan data
   asli**: Rp 64.550.291 HPP dari Rp 141.617.860 Omzet (margin 54,4%) —
   naik dari Rp 59.600.526/Rp 115.632.860 di versi sebelumnya yang
   mengecualikan Hydrogel (selisih Rp 4.949.765 HPP dan Rp 25.985.000
   Omzet, persis sebesar kontribusi Hydrogel).
3. **Grafik Penjualan Perbandingan per Pekan**: **direvisi total** dari
   versi sebelumnya berdasarkan permintaan lanjutan —
   - **Khusus produk LUNA** (seluruh varian, **TERMASUK Hydrogel**) —
     bukan lagi seluruh kategori Aksesoris (Tertarget+Non Tertarget).
     Grafik "Perbandingan Tertarget vs Non Tertarget" yang sebelumnya ada
     **dihapus** sesuai permintaan — sekarang cuma satu garis: total
     Omzet LUNA per pekan.
   - **Pekan dihitung per blok 7 hari TETAP**, bukan pekan kalender ISO
     seperti versi sebelumnya — Pekan 1 = tanggal paling awal pada data
     s/d +6 hari (mis. **1–7 Juli**), Pekan 2 = **8–14 Juli**, dst. Fungsi
     baru `omzet_luna_mingguan_blok7()` di `logic_aksesoris.py` — dimulai
     otomatis dari `TGL FAKTUR` paling awal di data (bukan tanggal
     hardcode), supaya tetap akurat kalau cakupan data berubah.
   - Menghitung SEMUA transaksi yang mengandung produk LUNA — **termasuk
     yang terjual lewat bundling** di transaksi Service/lainnya.
   - **Diuji dengan data asli**: 10 pekan (1 Juli – 8 September 2026),
     Pekan 1 tepat "01 Jul – 07 Jul" (Rp12.022.000), Pekan 9 tertinggi
     (Rp36.332.000, 26 Ags–1 Sep). Total seluruh pekan Rp141.617.860 —
     cocok persis dengan Total HPP/Omzet LUNA (termasuk Hydrogel) yang
     dihitung di bagian 2️⃣. Termasuk kasus tepi: data kosong dan data
     tanpa produk LUNA sama sekali (keduanya mengembalikan tabel kosong
     dengan aman, bukan error).
   - **Info tambahan — Kepatuhan Bundling Aksesoris pada Transaksi
     Service**: 4 kartu metrik di bawah grafik, memakai fungsi
     `analisa_bundling_brand()` yang sudah ada (dipakai ulang, tidak
     dihitung dari nol): Total Nota Service, Ada Bundling LUNA, Bundling
     Brand Lain (bukan LUNA — sesuai pengecualian SE), dan **⚠️ TIDAK Ada
     Bundling Aksesoris sama sekali** — metrik terakhir inilah yang paling
     perlu ditindaklanjuti. **Diuji dengan data asli**: dari 15.728 nota
     Service, 4.541 (28,9%) sudah bundling LUNA, 7.483 bundling brand lain,
     dan **3.704 (23,6%) sama sekali tidak ada bundling aksesoris apa pun**.
   - **Baru: Porsi Tanpa Bundling per Cabang** — tabel + grafik batang
     memakai fungsi `analisa_bundling_per_cabang()` yang SUDAH ADA di
     `logic_aksesoris.py` sejak sebelumnya tapi belum pernah dipakai di
     UI manapun — sekarang disambungkan ke sini. Diurutkan dari % Tanpa
     Bundling TERTINGGI (cabang paling perlu ditindaklanjuti di atas).
     Data uji: **Jatibening** paling tinggi (54,7% tanpa bundling),
     **Dramaga** paling rendah (5,9%).
     - **Diperbarui**: kolom "Nota Bundling Brand" diganti nama jadi
       **"Nota Bundling Luna"** (dibangun dinamis dari parameter
       `keyword.title()`, jadi otomatis menyesuaikan kalau suatu saat
       dipanggil dengan brand lain), dan ditambahkan **2 kolom persentase
       baru**: **"% Bundling Luna"** (persentase nota yang sudah bundling
       LUNA dari Total Nota Service) dan **"% Tanpa Bundling Luna"**
       (komplemennya — 100% dikurangi "% Bundling Luna", mencakup nota
       yang bundling brand lain MAUPUN yang sama sekali tidak ada
       bundling) — keduanya berdampingan dengan "% Tanpa Bundling" yang
       sudah ada sebelumnya (definisi berbeda: "Tanpa Bundling" murni =
       sama sekali tidak ada aksesoris apa pun, sedangkan "Tanpa Bundling
       Luna" = tidak ada LUNA spesifik, meski mungkin ada aksesoris brand
       lain). Diverifikasi `% Bundling Luna + % Tanpa Bundling Luna = 100`
       persis untuk seluruh 18 cabang. Kolom persentase & integer
       diformat otomatis berdasarkan awalan nama kolom (`%`), bukan
       daftar nama kolom hardcode, supaya tetap benar meski nama kolom
       brand berubah.
   - **Baru: Rincian Nomor Nota** — expander "🔍 Lihat Rincian Nomor Nota"
     berisi daftar lengkap NO FAKTUR + tanggal untuk nota Service yang
     sama sekali tidak ada bundling aksesoris, dengan dropdown filter per
     cabang dan tombol unduh CSV (baik untuk hasil terfilter maupun data
     lengkap semua cabang).
   - **🐛 Bug ditemukan & diperbaiki saat membangun fitur ini**: fungsi
     `analisa_bundling_brand()` (dan `analisa_bundling_per_cabang()`)
     SEMPAT menghitung "notas_dgn_keyword" (nota yang punya item bernama
     mengandung kata brand, mis. "LUNA") TANPA mensyaratkan kategori
     barangnya AKSESORIS. Ditemukan kasus nyata: item bernama
     **"LUNA DATA CABLE TYPE C TO C"** salah tercatat berkategori
     **SPAREPART** (bukan AKSESORIS) di data sumber — akibatnya nota yang
     memuat item ini terhitung GANDA: masuk kelompok "Ada Bundling LUNA"
     SEKALIGUS "Tanpa Bundling Aksesoris" (dua kelompok yang seharusnya
     saling eksklusif). Ini menyebabkan jumlah "Nota Tanpa Bundling" hasil
     breakdown per cabang (3.694) tidak cocok dengan angka ringkasan
     jaringan (3.704) — selisih 10 nota. Diperbaiki dengan menambahkan
     syarat `KATEGORI_NORM == "AKSESORIS"` pada perhitungan
     `notas_dgn_keyword` di KEDUA fungsi — sekarang kedua angka cocok
     persis (3.704 = 3.704), diverifikasi juga untuk kolom "Nota Bundling
     Brand" (4.541 = 4.541) dan Total Nota Service (15.728 = 15.728).
4. **Perbandingan Penjualan Aksesoris Semua Cabang per Bulan**: tabel
   pivot Cabang × Bulan, plus kolom Total dan grafik batang, diurutkan
   dari cabang dengan Total Omzet tertinggi.
   - **Baru: kolom "% Bulan A → Bulan B"** — pertumbuhan bulan-ke-bulan,
     disisipkan setelah tiap bulan (kecuali bulan pertama, karena tidak
     ada bulan sebelumnya untuk dibandingkan). Warna otomatis: 🟢 hijau
     kalau naik, 🔴 merah kalau turun (fungsi baru
     `warna_indikator_pencapaian_naik_turun()` — beda logika dari
     `warna_indikator_pencapaian()` yang berbasis ambang target 85%/100%,
     karena di sini yang dinilai adalah ARAH perubahan, bukan pencapaian
     target). Kolom Rp dan kolom % diformat & di-bar-chart TERPISAH (bar
     chart cuma pakai kolom Rp asli, supaya skala grafiknya tidak
     tercampur dengan skala persentase).
   - Kasus pembagi nol ditangani eksplisit: dari Rp0 ke Rp>0 dianggap
     +100%, dari Rp0 ke Rp0 dianggap 0% (bukan `inf`/error).
   - ⚠️ **Catatan penting**: bulan TERAKHIR pada data biasanya belum
     penuh sebulan (tergantung tanggal data terakhir diunggah) — pada
     data uji, September cuma berisi tanggal 1–2, sehingga wajar terlihat
     "turun drastis" (~90-99%) padahal bukan penurunan performa
     sungguhan. Caption di dashboard menjelaskan ini secara eksplisit
     supaya tidak disalahartikan.

**Diuji dengan data asli** (Faktur Pembelian: 1.782 baris aksesoris dari
Jul–Sep 2026; Faktur Penjualan: 51.179 baris periode sama):
- Total Pembelian ke LUNA: Rp 353.942.148 dari total Rp 1.095.016.240
  (32,3% porsi) — 62 pemasok berbeda teridentifikasi
- Total HPP LUNA (dari penjualan): Rp 59.600.526, Omzet Rp 115.632.860
- Grafik mingguan: 10 minggu, dari 2026-W27 sampai 2026-W36
- Perbandingan bulanan: 18 cabang × 3 bulan (Jul/Agu/Sep 2026), Cinere
  tertinggi total (Rp 218,1jt)
- Termasuk kasus tepi: data pembelian belum diunggah (pesan info, bukan
  error), data penjualan kosong, dan berkas rincian satu cabang tanpa
  nama cabang terisi.

**Catatan penting soal berkas sumber**: file Faktur Pembelian & Faktur
Penjualan terbaru (per 1 Jul–2 Sep 2026) ternyata **mencampur dua format
tanggal** dalam satu kolom — format standar (`2026-07-14 00:00:00`) untuk
data Juli, dan format Indonesia singkat (`22 Agu 2026`) untuk data
Agustus. Parser tanggal biasa gagal total pada ~49% baris. Sudah
ditangani saat konversi ke `.csv.gz` (di luar kode aplikasi ini) dengan
parser khusus yang mengenali kedua format — file CSV yang sudah dikonversi
aman dipakai langsung tanpa masalah ini.

## 🏆 Dashboard & Scoreboard Penjualan Aksesoris (BARU)

**Fitur besar baru**, ditempatkan paling atas di tab Penjualan Aksesoris —
sebelum bagian filter tahun/bulan/cabang yang sudah ada — karena
periodenya diatur sendiri (pilihan Samurai), tidak ikut filter di
bawahnya. **Parfum sengaja TIDAK disertakan** di bagian ini sesuai
permintaan.

**Definisi kelompok** (konsisten dengan seluruh perbaikan bug Hydrogel
sebelumnya):
- **Aksesoris Tertarget** = LUNA **KECUALI** Hydrogel
- **Aksesoris Non Tertarget** = Selain LUNA (**termasuk** LUNA Hydrogel)

**Fungsi baru di `logic_aksesoris.py`**: `split_tertarget_non_tertarget()`,
`scoreboard_cabang_aksesoris()`, `produk_terlaris_aksesoris_scoreboard()`.
**Fungsi baru di `logic_persediaan.py`**: `apply_filters_tertarget()`,
`nilai_persediaan_tertarget_vs_non()`, dan kolom baru
`ADALAH_LUNA_TERTARGET` + `ADALAH_HYDROGEL` di `load_persediaan()` (kolom
`ADALAH_LUNA` yang lama TIDAK diubah/dihapus, supaya bagian lain yang
masih memakainya tidak rusak).

**Ketujuh kriteria:**

1. **Total Target** — default Rp 3.500.000.000, periode default **Samurai
   39 (Jul–Sep 2026)** — keduanya bisa diubah (dropdown periode mencakup
   Samurai 37–44; target via number input). Target per cabang dibagi rata
   secara default, bisa disesuaikan lewat tabel isian di expander
   "✏️ Sesuaikan Target per Cabang".
2. **Scoreboard Penjualan per Cabang** — diurutkan dari **Total Omzet
   TERTINGGI ke TERENDAH** (beda dari tabel Monitoring Target LUNA yang
   urut dari % Actual terendah — di sini memang diminta urut Omzet).
   Warna indikator pada kolom "% Pencapaian" pakai ambang yang sama:
   🔴 <85% · 🟡 85–99% · 🟢 ≥100% (fungsi `warna_indikator_pencapaian()`
   yang sama, dipakai ulang).
3. **Grafik Rata-rata Penjualan per Hari per Cabang** — dihitung dari
   Total Omzet ÷ jumlah HARI dalam periode (bukan cuma hari yang ada
   transaksi), supaya representatif untuk perencanaan ke depan.
4. **Monitoring Margin Cabang < 40%** — otomatis menyaring & menghitung
   ulang cabang mana saja yang marginnya di bawah 40% pada periode ini,
   dengan pesan sukses kalau ternyata semua cabang sudah ≥40%.
5. **Produk Terlaris Aksesoris** — diurutkan dari Qty Terjual tertinggi,
   slider untuk atur berapa banyak ditampilkan (5–50), tombol unduh CSV
   berisi SELURUH produk (tidak dipotong slider).
6. **Monitoring Stok Tertarget vs Non Tertarget** — nilai & qty stok per
   cabang untuk kedua kelompok berdampingan, dari data Persediaan yang
   diunggah terpisah di sidebar.
7. **Monitoring Margin Produk** — tabel yang SAMA dengan poin 5 (fungsi
   `produk_terlaris_aksesoris_scoreboard()` dipanggil sekali, dipakai
   ulang), cuma diurutkan ulang berdasar kolom Margin (%) dari tertinggi
   ke terendah — tidak menghitung ulang dari nol.

**Diuji dengan data asli** (Samurai 39, Target Rp3,5M): scoreboard 18
cabang terurut benar dari **Cinere** (Rp214,5jt omzet, tertinggi) sampai
**Cibubur** (Rp11,9jt, terendah); Total Target hasil sum tepat
Rp3.500.000.000; **8 dari 18 cabang** bermargin di bawah 40%; 1.761 produk
unik teridentifikasi pada periode ini; stok Tertarget vs Non Tertarget
terhitung benar per cabang. Termasuk kasus tepi periode masa depan tanpa
data sama sekali (Samurai 44) — seluruh tabel tetap tampil dengan Omzet/
Result = 0, bukan error.

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
- **🐛 Bug ditemukan & diperbaiki: LUNA Hydrogel dihitung dua definisi
  berbeda** — bagian ini SEMPAT tidak mengecualikan LUNA Hydrogel dari
  kelompok "Aksesoris LUNA" (beda dengan bagian Monitoring Tahap 1 yang
  sudah eksplisit mengecualikan Hydrogel sejak diminta sebelumnya).
  Akibatnya, Omzet LUNA yang tampil di grafik ini **lebih besar** dari
  yang tampil di tabel Monitoring Tahap 1 untuk periode yang sama —
  inkonsistensi inilah yang terdeteksi pengguna sebagai "selisih dengan
  sumber data". **Terverifikasi dengan data asli** (periode 1 Jul–30 Ags
  2026): sebelum perbaikan Omzet LUNA tampil Rp 125.383.860 (termasuk
  Rp 24.785.000 dari Hydrogel); setelah perbaikan tampil Rp 100.598.860 —
  **persis cocok dengan angka di tabel Monitoring Tahap 1**. Diperbaiki
  dengan menambah parameter `keyword_kecuali="HYDROGEL"` (default) pada
  `omzet_per_kelompok()`, konsisten dengan `monitoring_tahap_per_cabang()`
  dan `analisa_bundling_brand()` — LUNA Hydrogel sekarang ikut masuk
  kelompok "Aksesoris Selain LUNA" di SELURUH bagian dashboard, bukan
  cuma sebagian. Parameter bersifat opsional & backward-compatible
  (`keyword_kecuali=None` mengembalikan perilaku lama, diverifikasi
  hasilnya identik dengan sebelum perbaikan).
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
