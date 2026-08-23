"""
Logika inti — Dashboard Persediaan Aksesoris, fokus produk LUNA (MFLASH, 18 cabang).

Sumber data: sheet "Daftar Barang dan Jasa" pada berkas Persediaan Aksesoris
Regional, atau CSV dengan skema kolom yang sama.

Cara kerja indikator stok LUNA:
1. Filter ke barang yang namanya mengandung "LUNA" (brand tertanam di
   `Nama Barang`, karena berkas ini tidak punya kolom Pemasok/Brand terpisah).
2. Indikator dihitung dari **jumlah stok aktual** (`Kts (Semua Gdng)`), bukan
   persentase relatif — supaya konsisten dan mudah dipahami tanpa perlu
   pembanding antar cabang atau antar produk.
3. Ambang batas (ditetapkan dari `app.py`, saat ini tetap/tidak muncul di
   sidebar):
   - 🔴 Merah  : stok ≤ 25   (kritis, perlu restock segera; termasuk 0 dan
                 anomali negatif)
   - 🟡 Kuning : stok 26–99  (menipis, perlu diawasi)
   - 🟢 Hijau  : stok ≥ 100  (aman)
   Ambang ini ditentukan langsung oleh pengguna — bukan hasil analisa
   statistik atas sebaran data.

Keterbatasan yang perlu diketahui pengguna: karena tidak ada data kecepatan
jual per produk per cabang yang bisa dicocokkan andal (nama produk di data
stok vs penjualan cuma cocok sekitar 45% karena variasi penulisan), indikator
ini BUKAN indikator "hari persediaan" — murni dari jumlah unit fisik yang
tersisa. Sesuaikan ambang batas kalau standar operasional MFLASH berbeda.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Cabang", "Kategori Barang", "Kode Barang", "Nama Barang",
    "Kts (Semua Gdng)", "Nilai Satuan", "Nilai Total",
]

SHEET_NAME = "Daftar Barang dan Jasa"

MERAH = "🔴 Merah"
KUNING = "🟡 Kuning"
HIJAU = "🟢 Hijau"


def load_persediaan(file_or_path, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Baca berkas Excel (sheet Daftar Barang dan Jasa) atau CSV sepadan."""
    name = getattr(file_or_path, "name", str(file_or_path))
    is_excel = str(name).lower().endswith((".xlsx", ".xls"))

    if is_excel:
        try:
            df = pd.read_excel(file_or_path, sheet_name=sheet_name)
        except ValueError:
            df = pd.read_excel(file_or_path, sheet_name=0)
    else:
        df = pd.read_csv(file_or_path, compression="infer", low_memory=False)

    # Buang kolom "Unnamed" kosong (pemisah dari format sumber)
    empty_unnamed = [c for c in df.columns if str(c).startswith("Unnamed") and df[c].notna().sum() == 0]
    if empty_unnamed:
        df = df.drop(columns=empty_unnamed)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Kolom berikut tidak ditemukan di berkas: " + ", ".join(missing))

    df = df.copy()
    df["Cabang"] = df["Cabang"].astype(str).str.strip()
    df["Nama Barang"] = df["Nama Barang"].astype(str).str.strip()
    df["Kode Barang"] = df["Kode Barang"].astype(str).str.strip()
    df["Kts (Semua Gdng)"] = pd.to_numeric(df["Kts (Semua Gdng)"], errors="coerce").fillna(0)
    df["Nilai Satuan"] = pd.to_numeric(df["Nilai Satuan"], errors="coerce").fillna(0)
    df["Nilai Total"] = pd.to_numeric(df["Nilai Total"], errors="coerce").fillna(0)

    kat = df["Kategori Barang"].astype(str).str.strip().str.upper()
    kat = kat.replace({"ACCESORIES": "AKSESORIS", "ACCESSORIES": "AKSESORIS"})
    df["KATEGORI_NORM"] = kat

    df["ADALAH_LUNA"] = df["Nama Barang"].str.upper().str.contains("LUNA", na=False)
    df["STOK_ANOMALI"] = df["Kts (Semua Gdng)"] < 0

    return df


def apply_filters(df: pd.DataFrame, cabang=None, hanya_aksesoris: bool = True, filter_luna: bool | None = True) -> pd.DataFrame:
    """filter_luna: True -> hanya nama barang mengandung LUNA,
    False -> hanya SELAIN LUNA, None -> tidak difilter berdasarkan brand."""
    out = df
    if hanya_aksesoris:
        out = out[out["KATEGORI_NORM"] == "AKSESORIS"]
    if filter_luna is True:
        out = out[out["ADALAH_LUNA"]]
    elif filter_luna is False:
        out = out[~out["ADALAH_LUNA"]]
    if cabang:
        out = out[out["Cabang"].isin(cabang)]
    return out


def klasifikasi_stok(qty: float, batas_merah: float = 25, batas_kuning: float = 99) -> str:
    if qty <= batas_merah:
        return MERAH
    if qty <= batas_kuning:
        return KUNING
    return HIJAU


def indikator_stok_luna(df: pd.DataFrame, batas_merah: float = 25, batas_kuning: float = 99) -> pd.DataFrame:
    """Indikator stok per (Cabang, Kode Barang, Nama Barang) — fungsi ini generik,
    bisa dipakai untuk himpunan produk manapun yang sudah difilter sebelumnya
    (LUNA maupun selain LUNA), bukan cuma untuk LUNA meski nama fungsinya begitu.

    Kolom hasil: Cabang, Kode Barang, Nama Barang, Stok, Nilai Stok, Indikator.
    """
    cols = ["Cabang", "Kode Barang", "Nama Barang", "Stok", "Nilai Stok", "Indikator"]
    if df.empty:
        return pd.DataFrame(columns=cols)

    g = df.groupby(["Cabang", "Kode Barang", "Nama Barang"]).agg(
        Stok=("Kts (Semua Gdng)", "sum"),
        **{"Nilai Stok": ("Nilai Total", "sum")},
    ).reset_index()

    g["Indikator"] = g["Stok"].apply(lambda q: klasifikasi_stok(q, batas_merah, batas_kuning))
    g = g.sort_values(["Stok", "Cabang"]).reset_index(drop=True)
    return g[cols]


def ringkasan_indikator_cabang(indikator_df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan per cabang: jumlah SKU LUNA di tiap indikator, dan porsi
    Merah (cabang dengan porsi Merah tertinggi = paling perlu segera
    ditindaklanjuti)."""
    cols = ["Cabang", "Jumlah SKU LUNA", "Merah", "Kuning", "Hijau", "Porsi Merah (%)"]
    if indikator_df.empty:
        return pd.DataFrame(columns=cols)

    piv = indikator_df.pivot_table(
        index="Cabang", columns="Indikator", values="Nama Barang", aggfunc="count", fill_value=0
    )
    for col in [MERAH, KUNING, HIJAU]:
        if col not in piv.columns:
            piv[col] = 0
    piv = piv.rename(columns={MERAH: "Merah", KUNING: "Kuning", HIJAU: "Hijau"})
    piv["Jumlah SKU LUNA"] = piv["Merah"] + piv["Kuning"] + piv["Hijau"]
    piv["Porsi Merah (%)"] = np.where(piv["Jumlah SKU LUNA"] > 0, piv["Merah"] / piv["Jumlah SKU LUNA"] * 100, 0)
    piv = piv.reset_index().sort_values("Porsi Merah (%)", ascending=False).reset_index(drop=True)
    return piv[cols]


def ringkasan_indikator_produk(indikator_df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan per produk LUNA: di berapa cabang produk ini Merah/Kuning/
    Hijau — untuk melihat produk mana yang paling sering kritis di banyak
    cabang sekaligus (kemungkinan masalah pasokan dari pemasok, bukan cuma
    satu cabang)."""
    cols = ["Nama Barang", "Jumlah Cabang Tercatat", "Merah", "Kuning", "Hijau", "Porsi Merah (%)"]
    if indikator_df.empty:
        return pd.DataFrame(columns=cols)

    piv = indikator_df.pivot_table(
        index="Nama Barang", columns="Indikator", values="Cabang", aggfunc="count", fill_value=0
    )
    for col in [MERAH, KUNING, HIJAU]:
        if col not in piv.columns:
            piv[col] = 0
    piv = piv.rename(columns={MERAH: "Merah", KUNING: "Kuning", HIJAU: "Hijau"})
    piv["Jumlah Cabang Tercatat"] = piv["Merah"] + piv["Kuning"] + piv["Hijau"]
    piv["Porsi Merah (%)"] = np.where(piv["Jumlah Cabang Tercatat"] > 0, piv["Merah"] / piv["Jumlah Cabang Tercatat"] * 100, 0)
    piv = piv.reset_index().sort_values("Porsi Merah (%)", ascending=False).reset_index(drop=True)
    return piv[cols]


def nilai_persediaan_cabang(df: pd.DataFrame) -> pd.DataFrame:
    """Nilai total persediaan (sesuai filter yang aktif — biasanya sudah
    difilter ke LUNA) per cabang."""
    cols = ["Cabang", "Jumlah SKU", "Total Qty", "Nilai Persediaan"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby("Cabang").agg(
        **{"Jumlah SKU": ("Kode Barang", "count")},
        **{"Total Qty": ("Kts (Semua Gdng)", "sum")},
        **{"Nilai Persediaan": ("Nilai Total", "sum")},
    ).reset_index()
    g = g.sort_values("Nilai Persediaan", ascending=False).reset_index(drop=True)
    return g[cols]


# ---------------------------------------------------------------------------
# Pemantauan cepat: cabang prioritas & peta stok (heatmap)
# ---------------------------------------------------------------------------

def cabang_prioritas(ringkasan_cabang_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """N cabang dengan porsi Merah tertinggi — dipakai untuk kotak "perlu
    perhatian" di paling atas dashboard, supaya tidak perlu baca tabel penuh
    untuk tahu cabang mana yang harus diprioritaskan duluan."""
    if ringkasan_cabang_df.empty:
        return ringkasan_cabang_df
    # Ringkasan sudah terurut dari porsi Merah tertinggi (lihat ringkasan_indikator_cabang)
    return ringkasan_cabang_df[ringkasan_cabang_df["Porsi Merah (%)"] > 0].head(n)


def pivot_heatmap_stok(indikator_df: pd.DataFrame):
    """Pivot dua tabel selebar (Nama Barang x Cabang): satu berisi jumlah
    stok, satu berisi label indikator — dipakai untuk membuat peta warna
    (heatmap) Cabang x Produk. Cocok untuk himpunan produk yang tidak
    terlalu banyak (puluhan-ratusan) supaya tetap kebaca; untuk ribuan
    produk (misal kelompok "selain LUNA"), heatmap ini tidak disarankan —
    pakai ringkasan per produk dengan batas top-N sebagai gantinya.
    """
    if indikator_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    pivot_stok = indikator_df.pivot_table(index="Nama Barang", columns="Cabang", values="Stok", aggfunc="sum")
    pivot_ind = indikator_df.pivot_table(index="Nama Barang", columns="Cabang", values="Indikator", aggfunc="first")
    # Urutkan baris dari yang paling banyak Merah-nya (paling perlu perhatian di atas)
    urutan = (pivot_ind == MERAH).sum(axis=1).sort_values(ascending=False).index
    pivot_stok = pivot_stok.loc[urutan]
    pivot_ind = pivot_ind.loc[urutan]
    return pivot_stok, pivot_ind


_WARNA_INDIKATOR = {
    MERAH: "background-color: #f5c6cb; color: #58151c;",
    KUNING: "background-color: #ffe69c; color: #664d03;",
    HIJAU: "background-color: #c3e6cb; color: #0f5132;",
}
_WARNA_KOSONG = "background-color: #f1f1f1; color: #adb5bd;"


def styler_heatmap(pivot_stok: pd.DataFrame, pivot_ind: pd.DataFrame):
    """Bungkus pivot_stok jadi pandas Styler dengan warna latar per sel
    mengikuti pivot_ind (Merah/Kuning/Hijau), sel yang tidak tercatat di
    cabang tsb diberi warna netral abu-abu (bukan Merah — supaya tidak
    disalahartikan sebagai "kritis" padahal memang belum pernah dicatat)."""
    try:
        warna = pivot_ind.map(lambda v: _WARNA_INDIKATOR.get(v, _WARNA_KOSONG))
    except AttributeError:
        warna = pivot_ind.applymap(lambda v: _WARNA_INDIKATOR.get(v, _WARNA_KOSONG))
    tampil = pivot_stok.copy()
    for c in tampil.columns:
        tampil[c] = tampil[c].apply(lambda x: "-" if pd.isna(x) else format_int_id(x))
    return tampil.style.apply(lambda _: warna, axis=None)


def styler_gradasi_merah(df: pd.DataFrame, kolom: str = "Porsi Merah (%)"):
    """Beri gradasi warna latar merah pada satu kolom (mis. 'Porsi Merah (%)')
    di sebuah tabel ringkasan, supaya baris paling kritis langsung menonjol
    tanpa perlu membaca angkanya satu per satu."""
    if df.empty or kolom not in df.columns:
        return df.style
    return df.style.background_gradient(subset=[kolom], cmap="Reds", vmin=0, vmax=100)


# ---------------------------------------------------------------------------
# Dashboard sederhana: nilai persediaan LUNA vs Selain LUNA, produk favorit
# per cabang, kebutuhan konsumen yang belum terpenuhi, lokasi cabang.
# CATATAN: bagian ini SENGAJA tidak memakai indikator warna Merah/Kuning/
# Hijau — indikator tri-warna itu hanya dipakai di Peta Stok (heatmap).
# ---------------------------------------------------------------------------

def nilai_persediaan_perbandingan(df_luna: pd.DataFrame, df_non_luna: pd.DataFrame) -> pd.DataFrame:
    """Bandingkan nilai persediaan LUNA vs Selain LUNA per cabang, dalam
    satu tabel sejajar supaya mudah dikontrol sekali lihat."""
    cols = ["Cabang", "Nilai LUNA", "Nilai Selain LUNA", "Total Nilai", "Porsi LUNA (%)"]
    nv_luna = nilai_persediaan_cabang(df_luna)[["Cabang", "Nilai Persediaan"]].rename(columns={"Nilai Persediaan": "Nilai LUNA"})
    nv_non = nilai_persediaan_cabang(df_non_luna)[["Cabang", "Nilai Persediaan"]].rename(columns={"Nilai Persediaan": "Nilai Selain LUNA"})
    g = nv_luna.merge(nv_non, on="Cabang", how="outer").fillna(0)
    if g.empty:
        return pd.DataFrame(columns=cols)
    g["Total Nilai"] = g["Nilai LUNA"] + g["Nilai Selain LUNA"]
    g["Porsi LUNA (%)"] = np.where(g["Total Nilai"] != 0, g["Nilai LUNA"] / g["Total Nilai"] * 100, 0)
    g = g.sort_values("Total Nilai", ascending=False).reset_index(drop=True)
    return g[cols]


def _jumlah_bulan_data(df_jual: pd.DataFrame) -> int:
    """Jumlah bulan unik (Tahun+Bulan) pada data penjualan — dipakai sebagai
    pembagi untuk estimasi rata-rata terjual per bulan."""
    if df_jual.empty or "TAHUN" not in df_jual.columns or "BULAN" not in df_jual.columns:
        return 1
    n = df_jual[["TAHUN", "BULAN"]].drop_duplicates().shape[0]
    return max(n, 1)


def produk_favorit_per_cabang(df_jual: pd.DataFrame, df_stok: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Produk aksesoris paling diminati (terjual terbanyak) per cabang,
    disandingkan dengan stok saat ini, potensi omzet & laba, dan estimasi
    kebutuhan restock bulanan — supaya langsung kelihatan produk favorit
    mana yang stoknya kosong/rendah, seberapa besar nilainya kalau terjual,
    dan berapa unit yang sebaiknya dibeli.

    df_jual: data penjualan aksesoris (kolom CABANG, NAMA BARANG, QTY,
    TOTAL HARGA, HARGA BELI, TAHUN, BULAN).
    df_stok: data persediaan yang sudah difilter kategori aksesoris (kolom
    Cabang, Nama Barang, Kts (Semua Gdng)).
    """
    cols = [
        "Cabang", "Peringkat", "Nama Barang", "Qty Terjual", "Rata-rata Terjual/Bulan",
        "Potensi Omzet", "Potensi Laba", "Stok Saat Ini", "Estimasi Kebutuhan Restock",
        "Wajib Direstock",
    ]
    if df_jual.empty:
        return pd.DataFrame(columns=cols)

    # Buang baris dengan NAMA BARANG kosong/NaN — bukan SKU sungguhan,
    # jangan sampai ikut masuk ranking produk favorit maupun opsi cabang.
    nama = df_jual["NAMA BARANG"].astype(str).str.strip()
    df_jual = df_jual[df_jual["NAMA BARANG"].notna() & (nama != "") & (nama.str.lower() != "nan")]
    if df_jual.empty:
        return pd.DataFrame(columns=cols)

    jumlah_bulan = _jumlah_bulan_data(df_jual)

    agg = df_jual.groupby(["CABANG", "NAMA BARANG"], dropna=False).agg(
        **{"Qty Terjual": ("QTY", "sum")}, Omzet=("TOTAL HARGA", "sum"), Modal=("HARGA BELI", "sum"),
    ).reset_index()
    agg["Potensi Laba"] = agg["Omzet"] - agg["Modal"]
    agg["Peringkat"] = agg.groupby("CABANG")["Qty Terjual"].rank(method="first", ascending=False).astype(int)
    top = agg[agg["Peringkat"] <= top_n].sort_values(["CABANG", "Peringkat"]).reset_index(drop=True)
    top["Rata-rata Terjual/Bulan"] = top["Qty Terjual"] / jumlah_bulan
    top = top.rename(columns={"Omzet": "Potensi Omzet"})

    if not df_stok.empty:
        stok_lookup = df_stok.groupby(["Cabang", "Nama Barang"])["Kts (Semua Gdng)"].sum().reset_index()
        stok_lookup = stok_lookup.rename(columns={"Cabang": "CABANG", "Nama Barang": "NAMA BARANG"})
        top = top.merge(stok_lookup, on=["CABANG", "NAMA BARANG"], how="left")
    else:
        top["Kts (Semua Gdng)"] = np.nan

    top["Stok Saat Ini"] = top["Kts (Semua Gdng)"].fillna(0)
    top["Estimasi Kebutuhan Restock"] = (top["Rata-rata Terjual/Bulan"] - top["Stok Saat Ini"]).clip(lower=0).round().astype(int)
    top["Wajib Direstock"] = top["Stok Saat Ini"].apply(lambda x: "⚠️ Ya — stok kosong/rendah" if x <= 2 else "Tidak")
    top = top.rename(columns={"CABANG": "Cabang", "NAMA BARANG": "Nama Barang"})
    return top[cols]


def produk_favorit_semua_cabang(
    df_jual: pd.DataFrame, df_stok: pd.DataFrame, top_n: int = 10, urutkan_dari: str = "Qty Terjual",
) -> pd.DataFrame:
    """Versi GABUNGAN semua cabang — untuk "Ranking Prioritas Restock
    Se-Jaringan". Qty terjual, potensi omzet & laba dijumlahkan LINTAS
    CABANG per nama barang, plus jumlah cabang yang stoknya kosong/rendah
    untuk produk itu (sinyal urgensi jaringan, bukan cuma satu cabang) dan
    estimasi kebutuhan restock bulanan total."""
    cols = [
        "Peringkat", "Nama Barang", "Qty Terjual", "Rata-rata Terjual/Bulan",
        "Potensi Omzet", "Potensi Laba", "Stok Semua Cabang", "Estimasi Kebutuhan Restock",
        "Jumlah Cabang Stok Kosong/Rendah", "Jumlah Cabang Menjual", "Wajib Direstock",
    ]
    if df_jual.empty:
        return pd.DataFrame(columns=cols)

    # Buang baris dengan NAMA BARANG kosong/NaN — bukan SKU sungguhan.
    nama = df_jual["NAMA BARANG"].astype(str).str.strip()
    df_jual = df_jual[df_jual["NAMA BARANG"].notna() & (nama != "") & (nama.str.lower() != "nan")]
    if df_jual.empty:
        return pd.DataFrame(columns=cols)

    jumlah_bulan = _jumlah_bulan_data(df_jual)

    agg = df_jual.groupby("NAMA BARANG", dropna=False).agg(
        **{"Qty Terjual": ("QTY", "sum")}, Omzet=("TOTAL HARGA", "sum"), Modal=("HARGA BELI", "sum"),
        **{"Jumlah Cabang Menjual": ("CABANG", "nunique")},
    ).reset_index()
    agg["Potensi Laba"] = agg["Omzet"] - agg["Modal"]
    agg["Rata-rata Terjual/Bulan"] = agg["Qty Terjual"] / jumlah_bulan
    agg = agg.rename(columns={"Omzet": "Potensi Omzet", "NAMA BARANG": "Nama Barang"})

    urutan_kolom = {"Qty Terjual": "Qty Terjual", "Potensi Omzet": "Potensi Omzet", "Potensi Laba": "Potensi Laba"}
    sort_col = urutan_kolom.get(urutkan_dari, "Qty Terjual")
    agg = agg.sort_values(sort_col, ascending=False).head(top_n).reset_index(drop=True)

    if not df_stok.empty:
        stok_per_cabang = df_stok.groupby(["Nama Barang", "Cabang"])["Kts (Semua Gdng)"].sum().reset_index()
        stok_total = stok_per_cabang.groupby("Nama Barang")["Kts (Semua Gdng)"].sum().clip(lower=0).reset_index().rename(
            columns={"Kts (Semua Gdng)": "Stok Semua Cabang"}
        )
        stok_per_cabang["Kosong"] = stok_per_cabang["Kts (Semua Gdng)"] <= 2
        jml_kosong = stok_per_cabang.groupby("Nama Barang")["Kosong"].sum().reset_index().rename(
            columns={"Kosong": "Jumlah Cabang Stok Kosong/Rendah"}
        )
        agg = agg.merge(stok_total, on="Nama Barang", how="left")
        agg = agg.merge(jml_kosong, on="Nama Barang", how="left")
    else:
        agg["Stok Semua Cabang"] = np.nan
        agg["Jumlah Cabang Stok Kosong/Rendah"] = np.nan

    agg["Stok Semua Cabang"] = agg["Stok Semua Cabang"].fillna(0)
    agg["Jumlah Cabang Stok Kosong/Rendah"] = agg["Jumlah Cabang Stok Kosong/Rendah"].fillna(0).astype(int)
    agg["Estimasi Kebutuhan Restock"] = (agg["Rata-rata Terjual/Bulan"] - agg["Stok Semua Cabang"]).clip(lower=0).round().astype(int)
    agg["Wajib Direstock"] = agg["Jumlah Cabang Stok Kosong/Rendah"].apply(lambda x: "⚠️ Ya — ada cabang stok kosong/rendah" if x > 0 else "Tidak")
    agg["Peringkat"] = range(1, len(agg) + 1)
    return agg[cols]


def kebutuhan_belum_terpenuhi(produk_favorit_df: pd.DataFrame) -> pd.DataFrame:
    """Saring produk_favorit_per_cabang() / produk_favorit_semua_cabang() ke
    baris yang perlu tindakan segera saja — produk favorit (sudah terbukti
    laku) tapi stoknya kosong/rendah saat ini. Ini yang paling menggambarkan
    "kebutuhan konsumen yang belum terpenuhi"."""
    if produk_favorit_df.empty:
        return produk_favorit_df
    return produk_favorit_df[produk_favorit_df["Wajib Direstock"].str.startswith("⚠️")].reset_index(drop=True)


# Lokasi 18 cabang MFlash (dicari langsung by name pada Google Maps —
# alamat, koordinat, dan rating asli, bukan perkiraan).
_LOKASI_CABANG_RAW = [
    ("Bintara", -6.2333032, 106.9663475, "Jl. Bintara No.31, Bekasi Barat, Kota Bekasi", "Kota Bekasi", 4.9, 5625),
    ("Ceger", -6.2625655, 106.7371545, "Jl. Ceger Raya No.1b, Pondok Aren, Tangerang Selatan", "Tangerang Selatan", 4.9, 4586),
    ("Cibinong", -6.4721488, 106.8430932, "Jl. Raya Cikaret, Pabuaran, Cibinong, Kab. Bogor", "Kab. Bogor", 4.9, 743),
    ("Cibubur", -6.3999095, 106.9591839, "Jl. Alternatif Cibubur, Cileungsi, Kab. Bogor", "Kab. Bogor", 4.9, 56),
    ("Cikampek", -6.4209110, 107.4741629, "Jl. Ir. Haji Juanda, Kota Baru, Karawang", "Karawang", 4.9, 520),
    ("Cilangkap", -6.3418003, 106.9054954, "Jl. Raya Cilangkap No.6, Cipayung, Jakarta Timur", "Jakarta Timur", 4.8, 595),
    ("Cinere", -6.3311695, 106.7838377, "Jl. Cinere Raya No.11, Cinere, Kota Depok", "Kota Depok", 4.9, 810),
    ("Condet", -6.2799532, 106.8551896, "Jl. Raya Condet, Kramat Jati, Jakarta Timur", "Jakarta Timur", 4.9, 1864),
    ("Dramaga", -6.5561290, 106.7037966, "Jl. Raya Tanjakan Cinangneng, Ciampea, Kab. Bogor", "Kab. Bogor", 4.9, 1928),
    ("Jatibening", -6.2653955, 106.9441790, "Jl. Caman Raya, Pondok Gede, Kota Bekasi", "Kota Bekasi", 4.8, 1730),
    ("Jatimulya", -6.2660474, 107.0166413, "Jl. HM. Joyo Martono No.9-4, Tambun Selatan, Kab. Bekasi", "Kab. Bekasi", 4.9, 3079),
    ("Jatiwaringin", -6.2592160, 106.9101611, "Jl. Raya Jatiwaringin No.6, Pondok Gede, Kota Bekasi", "Kota Bekasi", 4.9, 345),
    ("Klender", -6.2060058, 106.9029880, "Jl. Raya Bekasi KM.17, Cakung, Jakarta Timur", "Jakarta Timur", 4.9, 8237),
    ("Pejaten", -6.2770950, 106.8304872, "Pejaten Office Park, Jl. Buncit Raya, Pasar Minggu, Jakarta Selatan", "Jakarta Selatan", 5.0, 64),
    ("Radjiman", -6.2083183, 106.9230241, "Jl. Dr. KRT Radjiman Widyodiningrat No.20, Cakung, Jakarta Timur", "Jakarta Timur", 4.9, 1972),
    ("Sawangan", -6.3948944, 106.7991948, "Jl. Raya Sawangan, Pancoran Mas, Kota Depok", "Kota Depok", 4.9, 1506),
    ("Telukjambe", -6.3321200, 107.3125335, "Jl. Raya Teluk Jambe No.15, Telukjambe Timur, Karawang", "Karawang", 4.9, 1090),
    ("Warbong", -6.2704798, 107.1157773, "Jl. Raya Imam Bonjol, Cikarang Barat, Kab. Bekasi", "Kab. Bekasi", 5.0, 1568),
]


def data_lokasi_cabang() -> pd.DataFrame:
    """Data lokasi 18 cabang MFlash (nama, koordinat, alamat, wilayah,
    rating Google) — dicari manual per nama cabang, bukan perkiraan."""
    return pd.DataFrame(
        _LOKASI_CABANG_RAW,
        columns=["Cabang", "Lat", "Lon", "Alamat", "Wilayah", "Rating", "Jumlah Ulasan"],
    )


def ringkasan_wilayah(df_nilai_perbandingan: pd.DataFrame) -> pd.DataFrame:
    """Gabungkan lokasi (wilayah) dengan nilai persediaan per cabang, untuk
    melihat wilayah mana yang paling besar nilai persediaannya / paling
    padat jumlah cabangnya."""
    lokasi = data_lokasi_cabang()[["Cabang", "Wilayah"]]
    cols = ["Wilayah", "Jumlah Cabang", "Total Nilai Persediaan", "Rata-rata Nilai / Cabang"]
    if df_nilai_perbandingan.empty:
        return pd.DataFrame(columns=cols)
    g = df_nilai_perbandingan.merge(lokasi, on="Cabang", how="left")
    ring = g.groupby("Wilayah").agg(
        **{"Jumlah Cabang": ("Cabang", "nunique")},
        **{"Total Nilai Persediaan": ("Total Nilai", "sum")},
    ).reset_index()
    ring["Rata-rata Nilai / Cabang"] = np.where(
        ring["Jumlah Cabang"] != 0, ring["Total Nilai Persediaan"] / ring["Jumlah Cabang"], 0,
    )
    return ring.sort_values("Total Nilai Persediaan", ascending=False).reset_index(drop=True)[cols]


# ---------------------------------------------------------------------------
# Format angka gaya Indonesia
# ---------------------------------------------------------------------------

def format_int_id(x) -> str:
    try:
        x = int(round(float(x)))
    except (ValueError, TypeError):
        return str(x)
    return f"{x:,.0f}".replace(",", ".")


def format_rupiah_id(x) -> str:
    return "Rp " + format_int_id(x)


def format_decimal_id(x, decimals: int = 1) -> str:
    try:
        x = float(x)
    except (ValueError, TypeError):
        return str(x)
    s = f"{x:,.{decimals}f}"
    s = s.replace(",", "#").replace(".", ",").replace("#", ".")
    return s


def format_percent_id(x, decimals: int = 1) -> str:
    return format_decimal_id(x, decimals) + "%"
