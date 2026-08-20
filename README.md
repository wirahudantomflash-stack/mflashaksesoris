# MFLASH — Top Cabang / Top Produk / Top Sales Retail

Dashboard Streamlit ringan untuk tiga ranking:

- **Top 3 Cabang** (berdasarkan omzet, laba, atau jumlah nota)
- **Top 10 Produk Terlaris** (berdasarkan qty terjual atau omzet)
- **Top 5 Sales Retail** (berdasarkan omzet, laba, atau jumlah nota, khusus
  transaksi berkategori retail)

## Isi repo

```
app.py            # aplikasi Streamlit
logic.py          # semua logika olah data (bisa diuji terpisah dari UI)
requirements.txt  # dependensi untuk Streamlit Cloud
```

## Cara pakai di GitHub + Streamlit Cloud

1. Buat repo baru di GitHub, unggah ketiga berkas di atas.
2. **Opsional tapi disarankan:** unggah juga `penjualan.csv.gz` ke root repo
   (sejajar dengan `app.py`). Kalau ada, aplikasi otomatis memuatnya tanpa
   perlu upload manual setiap kali dibuka. Kalau tidak ada, aplikasi
   menampilkan tombol unggah berkas di panel kiri.
3. Buka [share.streamlit.io](https://share.streamlit.io), hubungkan ke repo
   tersebut, pilih `app.py` sebagai entry point, lalu deploy.

### Unggah data satu cabang saja

Aplikasi juga menerima berkas rincian faktur untuk **satu cabang saja** (mis.
hasil export per cabang dari sistem, yang biasanya tidak punya kolom
`CABANG` sama sekali). Kalau kolom itu tidak ditemukan, aplikasi akan
meminta Anda mengisi nama cabangnya lewat kotak input di panel kiri sebelum
data diproses — bukan langsung gagal. Dalam mode ini, tabel Top 3 Cabang
wajar hanya menampilkan satu baris karena datanya memang hanya dari satu
cabang.

## Aturan data yang diterapkan

- **Satu nota = kombinasi `CABANG` + `NO FAKTUR`**, bukan nomor faktur saja
  (nomor faktur berjalan sendiri-sendiri per cabang).
- **`HARGA BELI` sudah berupa total per baris** — tidak dikalikan `QTY` lagi.
  `MODAL = HARGA BELI`, `LABA = TOTAL HARGA − HARGA BELI`.
- **Baris kembar tidak dibuang** — dihitung apa adanya.
- Kategori **`AKSESORIS`** dan **`ACCESORIES`** digabung jadi satu kategori
  di kolom "Kategori" pada tabel Top Produk.
- Angka ditampilkan dengan format Indonesia (`68.838`, `10,3%`, `Rp 4.711.790.000`).

## Catatan tentang "Sales Retail"

Kolom **`YANG MENYERAHKAN/MENJUAL`** dipakai sebagai nama sales, dan
transaksi dianggap "retail" berdasarkan kolom **`KATEGORI PENJUALAN`**.
Karena nilai persis kolom itu di data Anda belum dikonfirmasi, aplikasi
secara otomatis menebak kategori yang mengandung kata "RETAIL" — tapi Anda
bisa mengoreksi pilihannya langsung lewat dropdown "Kategori penjualan yang
dianggap retail" di dashboard, tanpa perlu mengubah kode.

## Pengujian

Logika inti (`logic.py`) sudah diuji dengan data sintetis yang meniru skema
asli, termasuk kasus tepi: filter yang membuat hasil kosong, faktur yang
sama muncul di beberapa cabang, dan HARGA BELI yang tidak dikalikan ulang.

**Catatan jujur:** lingkungan tempat saya membuat berkas ini tidak
tersambung ke internet, sehingga saya tidak bisa memasang paket `streamlit`
dan benar-benar menjalankan `streamlit run app.py` di sini. Yang sudah saya
uji langsung adalah seluruh logika di `logic.py` (fungsi olah data), dan
`app.py` hanya menyusun logika itu ke widget Streamlit standar (`columns`,
`metric`, `radio`, `multiselect`, `dataframe`, `download_button`,
`file_uploader`) — tidak ada fitur eksotis di dalamnya. Saya sarankan Anda
menjalankannya sekali secara lokal (`streamlit run app.py`) sebelum atau
sesudah deploy ke Streamlit Cloud, dan beri tahu saya kalau ada error —
saya perbaiki dari sana.
