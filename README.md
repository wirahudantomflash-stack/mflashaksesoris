# MFlash Dashboard Aksesoris (Persediaan LUNA + Penjualan Aksesoris)

Satu aplikasi Streamlit dengan dua tab:

1. **📊 Dashboard Persediaan Aksesoris** — indikator stok dengan kode warna
   🔴🟡🟢 (berdasarkan jumlah unit stok aktual), dibagi dua bagian:
   - **Stok Persediaan — Nama Barang LUNA**: fokus brand yang wajib disetok
     semua cabang, dilengkapi **peta stok (heatmap) Cabang × Produk** untuk
     pemantauan sekali-lihat.
   - **Stok Persediaan — Nama Barang Selain LUNA**: brand lain sebagai
     pembanding.
   Tiap bagian punya kotak **"Cabang Paling Perlu Perhatian"** (5 cabang
   dengan porsi Merah tertinggi, ditampilkan paling atas), tabel ringkasan
   dengan gradasi warna otomatis, ringkasan produk, nilai persediaan per
   cabang, dan kotak analisa yang membandingkan kondisi LUNA vs selain LUNA.
2. **🧾 Dashboard Penjualan Aksesoris** — satu tab gabungan berisi dua bagian:
   - **Ringkasan Cabang, Produk & Sales**: ranking Seluruh Cabang, Semua
     Produk Aksesoris (terlaris & profit), dan Seluruh Sales.
   - **Revenue, HPP & Katalog LUNA**: revenue & tren bulanan, Top 10 produk
     aksesoris terlaris & profit, omzet + HPP seluruh cabang, katalog
     referensi harga LUNA & potensi profit, **matrix insentif resmi &
     kalkulator THP Sales Retail** (dikalibrasi ke target Rp5-8jt/bulan),
     **target pencapaian penjualan LUNA** (default Rp 2 miliar / 12 bulan
     mulai Agustus 2026), serta analisa + proyeksi 5–10 tahun.

Kedua bagian dalam tab Penjualan Aksesoris memakai **satu berkas data
penjualan yang sama** (satu tombol unggah saja di panel kiri) — dibaca dua
kali secara independen oleh dua modul olah data yang berbeda, jadi tidak
perlu unggah berkas terpisah untuk tiap bagian.

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
> nilai default (Merah ≤ 2 unit, Kuning 3–7 unit, Hijau ≥ 8 unit), diatur
> lewat variabel `batas_merah`/`batas_kuning` di awal `app.py` kalau perlu
> diubah. Beri tahu saya kapan saja kalau kontrolnya mau dimunculkan lagi.

Filter tahun/bulan/cabang untuk tiap bagian ada **di dalam bagian
masing-masing** (bukan di sidebar), supaya filter tidak tertukar.

## Aturan data — Tab Persediaan Aksesoris

- Barang LUNA diidentifikasi dari **nama barang yang mengandung kata
  "LUNA"** (sumber data tidak punya kolom Pemasok/Brand terpisah untuk stok);
  sisanya masuk kelompok "Selain LUNA".
- Data difilter ke kategori barang **AKSESORIS** (dua ejaan digabung),
  sesuai kolom `Kategori Barang` — berlaku untuk kedua kelompok.
- **Kelompok "Selain LUNA" jauh lebih besar** (≈22.700 baris, ≈12.600 nama
  produk unik, vs LUNA ≈360 baris/≈90 nama produk) — supaya tabel di layar
  tetap ringan, ringkasan per produk kelompok ini dibatasi tampilan (default
  30, bisa diperbesar lewat slider di dashboard), tapi **tombol unduh CSV
  selalu berisi semua produk**, tidak dipotong.
- **Indikator dari jumlah stok aktual** (`Kts (Semua Gdng)`), bukan
  persentase relatif terhadap cabang lain — supaya konsisten dan tidak
  bergantung pada produk pembanding. Ambang batas default diturunkan dari
  sebaran stok LUNA riil (median 3, kuartil-3 ≈10), dan dipakai sama untuk
  kedua kelompok supaya bisa dibandingkan apel-ke-apel:
  - 🔴 **Merah**: stok ≤ 2 (kritis, termasuk 0 dan anomali negatif)
  - 🟡 **Kuning**: stok 3–7 (menipis, perlu diawasi)
  - 🟢 **Hijau**: stok ≥ 8 (aman)
  Ambang ini **bisa diubah dari sidebar** kalau standar operasional MFLASH
  berbeda dari saran ini.
- Stok negatif pada sumber data (anomali sistem, biasanya transaksi keluar
  tercatat sebelum stok masuk disesuaikan) otomatis masuk kategori Merah,
  bukan disembunyikan atau di-clip jadi 0.
- **Fitur pemantauan cepat** (supaya tidak perlu baca tabel panjang satu per
  satu):
  - **Kotak "Cabang Paling Perlu Perhatian"** — 5 cabang dengan porsi Merah
    tertinggi, ditampilkan sebagai kartu merah mencolok di paling atas tiap
    bagian.
  - **Gradasi warna otomatis** pada kolom "Porsi Merah (%)" di tabel
    ringkasan cabang & produk — makin pekat merahnya, makin kritis, tanpa
    perlu membaca angka satu per satu.
  - **Peta stok (heatmap) Cabang × Produk** — khusus bagian LUNA (87 produk,
    masih kebaca dalam satu grid). Sel diwarnai mengikuti indikator
    (🔴🟡🟢), sel abu-abu "-" berarti produk itu tidak tercatat sama sekali
    di cabang tsb (bukan berarti stoknya 0 — beda makna, sengaja dibedakan
    warnanya). Tidak dipasang di bagian "Selain LUNA" karena grid-nya akan
    terlalu besar (12.634 produk) untuk kebaca.
- Kotak Analisa & Tindak Lanjut membandingkan porsi Merah LUNA vs Selain
  LUNA secara eksplisit, di samping catatan per kelompok.
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

## Matrix Insentif & Kalkulator THP Sales Retail

Dipindahkan dari simulasi generik ke **transkrip matrix insentif resmi
perusahaan** (2 lembar referensi):

- **Matrix Insentif Pekanan — Retail (Ideal)**: 29 baris (Sales Retail 11
  tier, Store Manager 9 tier, Regional Manager 9 tier), masing-masing dari
  Omzet/Pekan → Estimasi GP (asumsi 40%) → Insentif/Pekan (Sales Retail 5%
  dari GP, Store Manager 2%, Regional Manager 1%). Ditanam persis di
  `logic_aksesoris.py` (`matrix_insentif_pekanan()`), sudah diverifikasi
  cocok 100% dengan angka pada gambar referensi.
- **Matrix Insentif Per Item**: 4 tier berdasarkan rentang harga jual
  (Rp50rb–100rb, >100rb–250rb, >250rb–500rb, >500rb), insentif TETAP per
  unit terjual (bukan % dari omzet) — Rp5.000/Rp10.000/Rp25.000/Rp50.000.
  Ditanam di `matrix_insentif_per_item()`.
- **Kalkulator THP Sales Retail**: Total THP = **Gaji Pokok** + **Insentif
  %GP Bulanan** (Insentif/Pekan × jumlah minggu/bulan, default 4,33) +
  opsional **Insentif Per Item Bulanan** (estimasi jumlah item terjual/hari
  per tingkat harga × Insentif/Item × hari kerja/bulan).
  - Fungsi `saran_gaji_pokok()` memberi **titik awal** Gaji Pokok supaya
    tier **Minimum** pas mencapai THP Minimum (default Rp 5jt) — bukan
    jawaban final, karena tier **Maksimum** belum tentu otomatis pas di
    THP Maksimum (default Rp 8jt): itu tergantung seberapa besar asumsi
    volume item terjual yang diinput.
  - Kolom **"Status Target"** (✅ dalam target / ⬇️ di bawah / ⬆️ di atas)
    ditampilkan per tier, supaya jelas terlihat kalau kalibrasi Gaji Pokok
    atau asumsi item/hari masih perlu disesuaikan.
  - **Diuji langsung**: dengan asumsi 1 item/hari di semua tingkat harga,
    tier Minimum-Maksimum berkisar Rp 5.000.000–Rp 5.866.000 (semua ✅
    kalau target dianggap 5–8jt karena batas atas belum terlampaui, tapi
    belum menyentuh Rp 8jt) — realistis, karena rentang insentif murni dari
    matrix pekanan+per-item dengan asumsi konservatif tidak otomatis
    selebar itu. Menaikkan asumsi item/hari di tier atas (mis. 1→4 item/hari
    berjenjang) bisa mendorong tier atas melewati Rp 8jt (terdeteksi
    sebagai ⬆️ di atas target) — dashboard tidak memaksakan satu jawaban
    "benar", tapi memberi alat kalibrasi supaya pengguna sendiri yang
    menentukan asumsi volume penjualan yang realistis di lapangan.

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
  - Kelompok **LUNA**: 358 baris (87 nama produk unik) — 335 kombinasi
    SKU×cabang, porsi Merah 40,0%.
  - Kelompok **Selain LUNA**: 22.766 baris (12.634 nama produk unik) —
    20.888 kombinasi SKU×cabang, porsi Merah 89,9% (jauh lebih kritis
    dibanding LUNA, sesuai dugaan karena LUNA ditarget khusus).
  Termasuk penanganan stok negatif dan kasus tepi filter cabang kosong
  untuk kedua kelompok.
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
