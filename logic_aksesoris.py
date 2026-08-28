"""
Logika inti — Dashboard Revenue Penjualan Aksesoris (MFLASH, 18 cabang).

Sumber data: sheet "Rincian Faktur Penjualan" pada berkas Penjualan Aksesoris
Regional, atau CSV dengan skema kolom yang sama.

Aturan yang diterapkan (konsisten dengan dashboard MFLASH lainnya):
1. Satu nota = kombinasi CABANG + NO FAKTUR (bukan nomor faktur saja).
2. HARGA BELI sudah berupa total per baris -> MODAL = HARGA BELI,
   LABA = TOTAL HARGA - MODAL (tidak dikalikan QTY lagi).
3. Baris kembar tidak dibuang, dihitung apa adanya.
4. Kategori "AKSESORIS"/"Aksesoris" digabung.
5. Angka ditampilkan gaya Indonesia (68.838 / 10,3% / Rp 4.711.790.000).
"""

from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Cabang", "TGL FAKTUR", "NO FAKTUR", "KATEGORI PENJUALAN",
    "KATEGORI BARANG", "NAMA BARANG", "HARGA BELI", "QTY", "@HARGA",
    "TOTAL HARGA",
]

SHEET_NAME = "Rincian Faktur Penjualan"

BULAN_NAMA = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Ags", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}


class MissingCabangColumn(Exception):
    """Berkas terbaca sukses tapi tidak punya kolom CABANG (file 1 cabang)."""


def read_raw(file_or_path, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Baca berkas Excel (sheet Rincian Faktur Penjualan) atau CSV sepadan.
    CABANG TIDAK wajib di sini — ditangani lewat `finalize_data`."""
    name = getattr(file_or_path, "name", str(file_or_path))
    is_excel = str(name).lower().endswith((".xlsx", ".xls"))

    if is_excel:
        try:
            df = pd.read_excel(file_or_path, sheet_name=sheet_name)
        except ValueError:
            df = pd.read_excel(file_or_path, sheet_name=0)
    else:
        df = pd.read_csv(file_or_path, compression="infer", low_memory=False)

    # Buang kolom "Unnamed" (pemisah kosong ATAU duplikat kolom utama —
    # sudah diverifikasi 100% identik untuk berkas sumber MFLASH)
    unnamed_cols = [c for c in df.columns if str(c).startswith("Unnamed")]
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    # Samakan nama kolom cabang ("Cabang" atau "CABANG")
    rename_map = {c: "CABANG" for c in df.columns if str(c).strip().upper() == "CABANG"}
    if rename_map:
        df = df.rename(columns=rename_map)

    required_minus_cabang = [c for c in REQUIRED_COLUMNS if c != "Cabang"]
    missing = [c for c in required_minus_cabang if c not in df.columns]
    if missing:
        raise ValueError("Kolom berikut tidak ditemukan di berkas: " + ", ".join(missing))
    return df


def finalize_data(df: pd.DataFrame, cabang_default: str | None = None) -> pd.DataFrame:
    """Normalisasi tipe data, kunci nota, kategori, modal/laba, segmen.

    Kalau kolom CABANG tidak ada di berkas:
    - `cabang_default` diisi -> semua baris diberi nama cabang itu (kasus
      berkas rincian satu cabang).
    - `cabang_default` kosong -> lempar MissingCabangColumn supaya pemanggil
      (aplikasi) bisa menanyakan nama cabangnya ke pengguna lebih dulu.
    """
    df = df.copy()

    if "CABANG" not in df.columns:
        if not cabang_default:
            raise MissingCabangColumn(
                "Berkas ini tidak memiliki kolom CABANG (kemungkinan berkas rincian "
                "satu cabang). Masukkan nama cabangnya untuk melanjutkan."
            )
        df["CABANG"] = cabang_default
    else:
        df["CABANG"] = df["CABANG"].fillna(cabang_default or "TIDAK DIKETAHUI")

    df["TGL FAKTUR"] = pd.to_datetime(df["TGL FAKTUR"], errors="coerce")
    for col in ["HARGA BELI", "QTY", "@HARGA", "TOTAL HARGA"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["CABANG"] = df["CABANG"].astype(str).str.strip()
    df["NOTA_ID"] = df["CABANG"] + "||" + df["NO FAKTUR"].astype(str).str.strip()

    kat = df["KATEGORI BARANG"].astype(str).str.strip().str.upper()
    kat = kat.replace({"ACCESORIES": "AKSESORIS", "ACCESSORIES": "AKSESORIS"})
    df["KATEGORI_NORM"] = kat

    df["MODAL"] = df["HARGA BELI"]
    df["LABA"] = df["TOTAL HARGA"] - df["MODAL"]

    df["TAHUN"] = df["TGL FAKTUR"].dt.year
    df["BULAN"] = df["TGL FAKTUR"].dt.month
    df["PERIODE"] = df["TGL FAKTUR"].dt.to_period("M")

    # Segmen penjualan: Service vs Penjualan Unit vs Lainnya, dari KATEGORI PENJUALAN
    kp = df["KATEGORI PENJUALAN"].fillna("").astype(str).str.upper()
    def segmen(v: str) -> str:
        if "SERVICE" in v:
            return "Service"
        if "PENJUALAN" in v:
            return "Penjualan Unit"
        return "Lainnya"
    df["SEGMEN"] = kp.apply(segmen)

    return df


def load_aksesoris(file_or_path, sheet_name: str = SHEET_NAME, cabang_default: str | None = None) -> pd.DataFrame:
    """Baca + finalisasi dalam satu langkah (dipakai kalau berkas sudah pasti
    punya kolom CABANG sendiri, atau nama cabang default sudah diketahui)."""
    return finalize_data(read_raw(file_or_path, sheet_name), cabang_default=cabang_default)


def apply_filters(df: pd.DataFrame, tahun=None, bulan=None, cabang=None, segmen=None) -> pd.DataFrame:
    out = df
    if tahun:
        out = out[out["TAHUN"].isin(tahun)]
    if bulan:
        out = out[out["BULAN"].isin(bulan)]
    if cabang:
        out = out[out["CABANG"].isin(cabang)]
    if segmen:
        out = out[out["SEGMEN"].isin(segmen)]
    return out


def hanya_kategori(df: pd.DataFrame, kategori: str = "AKSESORIS") -> pd.DataFrame:
    """Filter ke satu kategori barang saja (KATEGORI_NORM) — PENTING dipakai
    sebelum menghitung revenue/HPP/katalog aksesoris, supaya berkas penjualan
    yang mencakup SEMUA kategori (JASA, SPAREPART, dll — bukan cuma
    aksesoris) tidak ikut membesarkan angka Omzet Aksesoris."""
    if "KATEGORI_NORM" not in df.columns:
        return df
    return df[df["KATEGORI_NORM"] == kategori.strip().upper()]


# ---------------------------------------------------------------------------
# Periode "Samurai" (kuartelan bernama internal) — dipakai untuk pencapaian
# per periode dan perbandingan antar periode LUNA vs Selain LUNA.
# ---------------------------------------------------------------------------
PERIODE_SAMURAI = {
    "Samurai 37 (Jan–Mar 2026)": (pd.Timestamp("2026-01-01"), pd.Timestamp("2026-03-31")),
    "Samurai 38 (Apr–Jun 2026)": (pd.Timestamp("2026-04-01"), pd.Timestamp("2026-06-30")),
    "Samurai 39 (Jul–Sep 2026)": (pd.Timestamp("2026-07-01"), pd.Timestamp("2026-09-30")),
    "Samurai 40 (Okt–Des 2026)": (pd.Timestamp("2026-10-01"), pd.Timestamp("2026-12-31")),
    "Samurai 41 (Jan–Mar 2027)": (pd.Timestamp("2027-01-01"), pd.Timestamp("2027-03-31")),
    "Samurai 42 (Apr–Jun 2027)": (pd.Timestamp("2027-04-01"), pd.Timestamp("2027-06-30")),
    "Samurai 43 (Jul–Sep 2027)": (pd.Timestamp("2027-07-01"), pd.Timestamp("2027-09-30")),
    "Samurai 44 (Okt–Des 2027)": (pd.Timestamp("2027-10-01"), pd.Timestamp("2027-12-31")),
}


def filter_periode_samurai(df: pd.DataFrame, nama_periode: str) -> pd.DataFrame:
    """Filter data penjualan ke satu periode Samurai (berdasar TGL FAKTUR)."""
    if nama_periode not in PERIODE_SAMURAI or df.empty:
        return df.iloc[0:0]
    mulai, selesai = PERIODE_SAMURAI[nama_periode]
    return df[(df["TGL FAKTUR"] >= mulai) & (df["TGL FAKTUR"] <= selesai)]


def pencapaian_kelompok_periode(df_aksesoris: pd.DataFrame, nama_periode: str, keyword_brand: str = "LUNA") -> pd.DataFrame:
    """Omzet & Gross Profit LUNA vs Selain LUNA untuk SATU periode Samurai
    yang dipilih — dipakai untuk tampilan "pencapaian per periode"."""
    cols = ["Kelompok", "Omzet", "Gross Profit", "Margin (%)", "Jumlah Nota", "Jumlah Item Terjual"]
    df_p = filter_periode_samurai(df_aksesoris, nama_periode)
    if df_p.empty:
        return pd.DataFrame(columns=cols)

    mask = df_p["NAMA BARANG"].astype(str).str.upper().str.contains(keyword_brand.upper(), na=False)
    rows = []
    for label, sub in [(keyword_brand.upper(), df_p[mask]), (f"Selain {keyword_brand.upper()}", df_p[~mask])]:
        omzet = sub["TOTAL HARGA"].sum()
        gp = sub["LABA"].sum()
        rows.append({
            "Kelompok": label,
            "Omzet": omzet,
            "Gross Profit": gp,
            "Margin (%)": (gp / omzet * 100) if omzet else 0,
            "Jumlah Nota": sub["NOTA_ID"].nunique() if "NOTA_ID" in sub.columns else 0,
            "Jumlah Item Terjual": sub["QTY"].sum(),
        })
    return pd.DataFrame(rows, columns=cols)


def perbandingan_antar_periode_samurai(df_aksesoris: pd.DataFrame, keyword_brand: str = "LUNA") -> pd.DataFrame:
    """Bandingkan Omzet & Gross Profit LUNA vs Selain LUNA di SELURUH 4
    periode Samurai sekaligus — satu baris per (Periode, Kelompok)."""
    cols = ["Periode", "Kelompok", "Omzet", "Gross Profit", "Margin (%)"]
    if df_aksesoris.empty:
        return pd.DataFrame(columns=cols)

    rows = []
    for nama_periode in PERIODE_SAMURAI:
        hasil = pencapaian_kelompok_periode(df_aksesoris, nama_periode, keyword_brand=keyword_brand)
        for _, r in hasil.iterrows():
            rows.append({
                "Periode": nama_periode,
                "Kelompok": r["Kelompok"],
                "Omzet": r["Omzet"],
                "Gross Profit": r["Gross Profit"],
                "Margin (%)": r["Margin (%)"],
            })
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


def omzet_per_kelompok(df_aksesoris: pd.DataFrame, df_parfum: pd.DataFrame, keyword_brand: str = "LUNA") -> pd.DataFrame:
    """Bandingkan omzet 3 kelompok: Aksesoris ber-brand `keyword_brand`
    (mis. LUNA), Aksesoris SELAIN brand itu, dan Parfum (kelompok terpisah,
    kategori beda) — untuk grafik perbandingan penjualan lintas kategori."""
    cols = ["Kelompok", "Omzet", "Laba", "Jumlah Nota", "Jumlah Item Terjual"]
    rows = []

    if not df_aksesoris.empty:
        mask_brand = df_aksesoris["NAMA BARANG"].astype(str).str.upper().str.contains(keyword_brand.upper(), na=False)
        for label, sub in [
            (f"Aksesoris {keyword_brand.upper()}", df_aksesoris[mask_brand]),
            (f"Aksesoris Selain {keyword_brand.upper()}", df_aksesoris[~mask_brand]),
        ]:
            rows.append({
                "Kelompok": label,
                "Omzet": sub["TOTAL HARGA"].sum(),
                "Laba": sub["LABA"].sum(),
                "Jumlah Nota": sub["NOTA_ID"].nunique() if "NOTA_ID" in sub.columns else 0,
                "Jumlah Item Terjual": sub["QTY"].sum(),
            })

    if not df_parfum.empty:
        rows.append({
            "Kelompok": "Parfum",
            "Omzet": df_parfum["TOTAL HARGA"].sum(),
            "Laba": df_parfum["LABA"].sum(),
            "Jumlah Nota": df_parfum["NOTA_ID"].nunique() if "NOTA_ID" in df_parfum.columns else 0,
            "Jumlah Item Terjual": df_parfum["QTY"].sum(),
        })
    else:
        rows.append({"Kelompok": "Parfum", "Omzet": 0, "Laba": 0, "Jumlah Nota": 0, "Jumlah Item Terjual": 0})

    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


def kontribusi_cabang_gabungan(df_aksesoris: pd.DataFrame, df_parfum: pd.DataFrame) -> pd.DataFrame:
    """Total omzet per cabang, GABUNGAN Aksesoris (LUNA + selain LUNA) dan
    Parfum, diurutkan dari yang PALING RENDAH ke PALING BESAR kontribusinya
    — untuk diagram indikator cabang paling berkontribusi."""
    cols = ["Cabang", "Omzet Aksesoris", "Omzet Parfum", "Total Omzet", "Porsi Kontribusi (%)"]
    aks = df_aksesoris.groupby("CABANG")["TOTAL HARGA"].sum() if not df_aksesoris.empty else pd.Series(dtype=float)
    prf = df_parfum.groupby("CABANG")["TOTAL HARGA"].sum() if not df_parfum.empty else pd.Series(dtype=float)

    semua_cabang = sorted(set(aks.index) | set(prf.index))
    if not semua_cabang:
        return pd.DataFrame(columns=cols)

    g = pd.DataFrame({"Cabang": semua_cabang})
    g["Omzet Aksesoris"] = g["Cabang"].map(aks).fillna(0)
    g["Omzet Parfum"] = g["Cabang"].map(prf).fillna(0)
    g["Total Omzet"] = g["Omzet Aksesoris"] + g["Omzet Parfum"]
    total_keseluruhan = g["Total Omzet"].sum()
    g["Porsi Kontribusi (%)"] = np.where(total_keseluruhan != 0, g["Total Omzet"] / total_keseluruhan * 100, 0)
    g = g.sort_values("Total Omzet", ascending=True).reset_index(drop=True)
    return g[cols]


# ---------------------------------------------------------------------------
# 7. Analisa mendalam per brand: Stok + Terjual + Bundling + Temuan
# ---------------------------------------------------------------------------

def ringkasan_stok_dan_terjual_brand(df_persediaan_brand: pd.DataFrame, df_jual_brand: pd.DataFrame) -> dict:
    """Ringkasan Stok (nilai & qty) + Sudah Terjual (omzet & qty) + rata-rata
    per hari untuk satu brand/kelompok produk. `df_persediaan_brand` pakai
    skema kolom persediaan (Nilai Total, Kts (Semua Gdng)); `df_jual_brand`
    pakai skema kolom penjualan (TOTAL HARGA, QTY, TGL FAKTUR)."""
    nilai_stok = df_persediaan_brand["Nilai Total"].sum() if not df_persediaan_brand.empty else 0
    qty_stok = df_persediaan_brand["Kts (Semua Gdng)"].sum() if not df_persediaan_brand.empty else 0

    omzet_terjual = df_jual_brand["TOTAL HARGA"].sum() if not df_jual_brand.empty else 0
    qty_terjual = df_jual_brand["QTY"].sum() if not df_jual_brand.empty else 0
    jumlah_hari_data = df_jual_brand["TGL FAKTUR"].dt.date.nunique() if not df_jual_brand.empty else 0
    rata2_qty_per_hari = (qty_terjual / jumlah_hari_data) if jumlah_hari_data else 0
    rata2_omzet_per_hari = (omzet_terjual / jumlah_hari_data) if jumlah_hari_data else 0

    return dict(
        nilai_stok=nilai_stok,
        qty_stok=qty_stok,
        omzet_terjual=omzet_terjual,
        qty_terjual=qty_terjual,
        jumlah_hari_data=jumlah_hari_data,
        rata2_qty_per_hari=rata2_qty_per_hari,
        rata2_omzet_per_hari=rata2_omzet_per_hari,
    )


def analisa_bundling_brand(df_jual_brand: pd.DataFrame, df_jual_semua_kategori: pd.DataFrame, keyword: str = "LUNA"):
    """Analisa bundling untuk satu brand pada transaksi Service:
    1. Jumlah unit/transaksi brand tsb yang notanya juga berisi kategori
       lain (indikasi terbundling dengan Service/Sparepart/dll).
    2. Breakdown nota Service jadi 3 kelompok: (a) sudah bundling dengan
       brand target, (b) bundling tapi pakai brand LAIN (sesuai pengecualian
       SE kalau brand target kosong), (c) TIDAK ADA aksesoris sama sekali
       (pelanggaran murni terhadap kebijakan bundling).
    3. Detail nota kelompok (c) — Cabang & Nomor Nota — sebagai temuan.

    Mengembalikan (ringkasan: dict, detail_temuan: DataFrame)."""
    ringkasan = dict(
        qty_terbundling=0, jumlah_transaksi_terbundling=0, jumlah_nota_service=0,
        jumlah_service_dgn_brand=0, jumlah_service_dgn_aksesoris_lain=0,
        jumlah_service_tanpa_aksesoris=0, pct_bundling_brand=0, pct_tanpa_aksesoris=0,
    )
    cols_temuan = ["Cabang", "NO FAKTUR", "TGL FAKTUR", "NOTA_ID"]
    if df_jual_semua_kategori.empty:
        return ringkasan, pd.DataFrame(columns=cols_temuan)

    # 1. Qty brand yang terbundling (nota-nya lintas kategori)
    if not df_jual_brand.empty:
        nota_kategori_count = df_jual_semua_kategori.groupby("NOTA_ID")["KATEGORI_NORM"].nunique()
        nota_multi = set(nota_kategori_count[nota_kategori_count > 1].index)
        mask_bundling = df_jual_brand["NOTA_ID"].isin(nota_multi)
        ringkasan["qty_terbundling"] = df_jual_brand[mask_bundling]["QTY"].sum()
        ringkasan["jumlah_transaksi_terbundling"] = int(mask_bundling.sum())

    # 2. Breakdown nota Service
    service_notas = set(df_jual_semua_kategori[df_jual_semua_kategori["SEGMEN"] == "Service"]["NOTA_ID"].unique())
    notas_dgn_aksesoris = set(df_jual_semua_kategori[df_jual_semua_kategori["KATEGORI_NORM"] == "AKSESORIS"]["NOTA_ID"].unique())
    mask_keyword_all = df_jual_semua_kategori["NAMA BARANG"].astype(str).str.upper().str.contains(keyword.upper(), na=False)
    notas_dgn_keyword = set(df_jual_semua_kategori[mask_keyword_all]["NOTA_ID"].unique())

    service_tanpa_aksesoris = service_notas - notas_dgn_aksesoris
    service_dgn_brand = service_notas & notas_dgn_keyword
    service_dgn_aksesoris_lain = (service_notas & notas_dgn_aksesoris) - notas_dgn_keyword

    n_service = len(service_notas)
    ringkasan["jumlah_nota_service"] = n_service
    ringkasan["jumlah_service_dgn_brand"] = len(service_dgn_brand)
    ringkasan["jumlah_service_dgn_aksesoris_lain"] = len(service_dgn_aksesoris_lain)
    ringkasan["jumlah_service_tanpa_aksesoris"] = len(service_tanpa_aksesoris)
    ringkasan["pct_bundling_brand"] = (len(service_dgn_brand) / n_service * 100) if n_service else 0
    ringkasan["pct_tanpa_aksesoris"] = (len(service_tanpa_aksesoris) / n_service * 100) if n_service else 0

    # 3. Detail temuan: nota Service TANPA aksesoris sama sekali
    detail = df_jual_semua_kategori[df_jual_semua_kategori["NOTA_ID"].isin(service_tanpa_aksesoris)][
        ["CABANG", "NO FAKTUR", "TGL FAKTUR", "NOTA_ID"]
    ].drop_duplicates(subset=["NOTA_ID"]).rename(columns={"CABANG": "Cabang"}).sort_values(["Cabang", "TGL FAKTUR"]).reset_index(drop=True)

    return ringkasan, detail[cols_temuan]


def rincian_produk_brand(df_persediaan_brand: pd.DataFrame) -> pd.DataFrame:
    """Rincian SEMUA barang (per Cabang x Nama Barang) untuk satu kelompok
    brand — dari data persediaan, diurutkan dari nilai stok terbesar."""
    cols = ["Cabang", "Kode Barang", "Nama Barang", "Stok", "Nilai Stok"]
    if df_persediaan_brand.empty:
        return pd.DataFrame(columns=cols)
    g = df_persediaan_brand.groupby(["Cabang", "Kode Barang", "Nama Barang"]).agg(
        Stok=("Kts (Semua Gdng)", "sum"), **{"Nilai Stok": ("Nilai Total", "sum")},
    ).reset_index()
    g = g.sort_values("Nilai Stok", ascending=False).reset_index(drop=True)
    return g[cols]


# ---------------------------------------------------------------------------
# 1. Revenue
# ---------------------------------------------------------------------------

def revenue_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(omzet=0, modal=0, laba=0, margin=0, jumlah_nota=0, jumlah_item=0, rata_per_nota=0)
    omzet = df["TOTAL HARGA"].sum()
    modal = df["MODAL"].sum()
    laba = df["LABA"].sum()
    jumlah_nota = df["NOTA_ID"].nunique()
    return dict(
        omzet=omzet, modal=modal, laba=laba,
        margin=(laba / omzet * 100) if omzet else 0,
        jumlah_nota=jumlah_nota,
        jumlah_item=df["QTY"].sum(),
        rata_per_nota=(omzet / jumlah_nota) if jumlah_nota else 0,
    )


def revenue_trend_bulanan(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Periode", "Omzet", "Modal", "Laba", "Margin (%)", "Qty Terjual", "Jumlah Nota"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby("PERIODE").agg(
        Omzet=("TOTAL HARGA", "sum"),
        Modal=("MODAL", "sum"),
        Laba=("LABA", "sum"),
        **{"Qty Terjual": ("QTY", "sum")},
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index().rename(columns={"PERIODE": "Periode"})
    g["Margin (%)"] = np.where(g["Omzet"] != 0, g["Laba"] / g["Omzet"] * 100, 0)
    g["Periode"] = g["Periode"].astype(str)
    return g[cols]


def revenue_per_segmen(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Segmen", "Omzet", "Laba", "Margin (%)", "Jumlah Nota", "Porsi Omzet (%)"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby("SEGMEN").agg(
        Omzet=("TOTAL HARGA", "sum"),
        Laba=("LABA", "sum"),
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index().rename(columns={"SEGMEN": "Segmen"})
    total = g["Omzet"].sum()
    g["Margin (%)"] = np.where(g["Omzet"] != 0, g["Laba"] / g["Omzet"] * 100, 0)
    g["Porsi Omzet (%)"] = np.where(total != 0, g["Omzet"] / total * 100, 0)
    g = g.sort_values("Omzet", ascending=False).reset_index(drop=True)
    return g[cols]


# ---------------------------------------------------------------------------
# 2. Top produk terlaris + profit
# ---------------------------------------------------------------------------

def top_produk(df: pd.DataFrame, metric: str = "Qty Terjual", n: int = 10) -> pd.DataFrame:
    cols = ["NAMA BARANG", "Qty Terjual", "Omzet", "Modal", "Laba", "Margin (%)"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby("NAMA BARANG").agg(
        **{"Qty Terjual": ("QTY", "sum")},
        Omzet=("TOTAL HARGA", "sum"),
        Modal=("MODAL", "sum"),
        Laba=("LABA", "sum"),
    ).reset_index()
    g["Margin (%)"] = np.where(g["Omzet"] != 0, g["Laba"] / g["Omzet"] * 100, 0)
    sort_col = {"Qty Terjual": "Qty Terjual", "Omzet": "Omzet", "Laba": "Laba"}[metric]
    g = g.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)
    g.index = g.index + 1
    return g[cols]


# ---------------------------------------------------------------------------
# 3. Omzet semua cabang
# ---------------------------------------------------------------------------

def omzet_cabang(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Cabang", "Omzet", "HPP", "Laba", "Margin (%)", "HPP terhadap Omzet (%)", "Jumlah Nota", "Rata-rata / Nota"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby("CABANG").agg(
        Omzet=("TOTAL HARGA", "sum"),
        HPP=("MODAL", "sum"),
        Laba=("LABA", "sum"),
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index().rename(columns={"CABANG": "Cabang"})
    g["Margin (%)"] = np.where(g["Omzet"] != 0, g["Laba"] / g["Omzet"] * 100, 0)
    g["HPP terhadap Omzet (%)"] = np.where(g["Omzet"] != 0, g["HPP"] / g["Omzet"] * 100, 0)
    g["Rata-rata / Nota"] = np.where(g["Jumlah Nota"] != 0, g["Omzet"] / g["Jumlah Nota"], 0)
    g = g.sort_values("Omzet", ascending=False).reset_index(drop=True)
    g.index = g.index + 1
    return g[cols]


# ---------------------------------------------------------------------------
# 4. Proyeksi & analisa 5-10 tahun
# ---------------------------------------------------------------------------

def hitung_run_rate(df: pd.DataFrame) -> dict:
    """Rata-rata omzet & laba bulanan dari periode LENGKAP saja (bulan penuh),
    supaya bulan berjalan yang belum lengkap tidak menurunkan rata-rata secara
    tidak adil."""
    if df.empty:
        return dict(omzet_bulanan=0, laba_bulanan=0, margin=0, jumlah_bulan=0, bulan_tidak_lengkap=None)

    tgl_max = df["TGL FAKTUR"].max()
    periode_max = tgl_max.to_period("M") if pd.notna(tgl_max) else None

    # Anggap bulan terakhir pada data tidak lengkap kalau tanggal maksimalnya
    # bukan tanggal akhir bulan itu.
    bulan_tidak_lengkap = None
    if periode_max is not None:
        akhir_bulan = periode_max.to_timestamp(how="end").normalize()
        if tgl_max.normalize() < akhir_bulan:
            bulan_tidak_lengkap = str(periode_max)

    df_lengkap = df if bulan_tidak_lengkap is None else df[df["PERIODE"].astype(str) != bulan_tidak_lengkap]
    if df_lengkap.empty:
        df_lengkap = df  # fallback kalau data cuma 1 bulan dan itu tidak lengkap

    trend = df_lengkap.groupby("PERIODE").agg(Omzet=("TOTAL HARGA", "sum"), Laba=("LABA", "sum")).reset_index()
    jumlah_bulan = len(trend)
    omzet_bulanan = trend["Omzet"].mean() if jumlah_bulan else 0
    laba_bulanan = trend["Laba"].mean() if jumlah_bulan else 0

    return dict(
        omzet_bulanan=omzet_bulanan,
        laba_bulanan=laba_bulanan,
        margin=(laba_bulanan / omzet_bulanan * 100) if omzet_bulanan else 0,
        jumlah_bulan=jumlah_bulan,
        bulan_tidak_lengkap=bulan_tidak_lengkap,
    )


def proyeksi_tahunan(omzet_bulanan: float, tahun_list=(1, 3, 5, 10), skenario=None) -> pd.DataFrame:
    """Proyeksi omzet tahunan dari run-rate bulanan saat ini, dengan beberapa
    skenario pertumbuhan tahunan (majemuk). Ini estimasi kasar berbasis
    ekstrapolasi linier dari data yang tersedia (bukan model statistik penuh),
    karena data historis yang ada baru mencakup kurang dari 1 tahun."""
    if skenario is None:
        skenario = {"Konservatif (5%/th)": 0.05, "Moderat (12%/th)": 0.12, "Optimis (20%/th)": 0.20}

    omzet_tahun_dasar = omzet_bulanan * 12
    rows = []
    for label, growth in skenario.items():
        for th in tahun_list:
            proyeksi = omzet_tahun_dasar * ((1 + growth) ** th)
            rows.append({"Skenario": label, "Tahun ke-": th, "Proyeksi Omzet Tahunan": proyeksi})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. Katalog referensi harga LUNA & potensi profit
# ---------------------------------------------------------------------------
# Diketik ulang dari pricelist resmi LUNA (NEW_PL_05_JULI_LUNA_2026.pdf).
# Kolom: kategori, kode_produk, deskripsi_singkat, harga_dealer, harga_srp
# (SRP = Suggested Retail Price / saran harga jual ke konsumen).
_LUNA_ACCESSORIES_RAW = [
    ("Adapter", "AJ-4PJ JAR", "Adapter Jar (12pc) QC 2.4A Micro USB", 186500, 266450),
    ("Adapter", "AJ-5O TRAY", "Adapter Tray (15pc) Fast Charging 25W Type-C", 804000, 950000),
    ("Adapter", "AJ5Y-T", "Adapter Box (20pc) Dual Port 2.4A USB-A", 350000, 590000),
    ("Adapter", "AJ5G-J", "Adapter Jar (15pc) QC 1.5A Micro USB", 195000, 278500),
    ("Adapter", "AJ5S", "Adapter GAN 35W PD Single Port Type C", 89000, 129500),
    ("Adapter", "AJ-5F", "Adapter 30W PD Single Port USB-C", 66000, 94000),
    ("Adapter", "AJ-5E", "Adapter 25W PD Single Port USB-C", 63000, 90000),
    ("Adapter", "AJ-4Y", "Adapter 20W QC3.0 Micro USB", 39000, 55500),
    ("Adapter", "AJ-5A", "Adapter Fast Charging QC3.0 Micro USB", 35000, 50000),
    ("Adapter", "AJ-4A", "Adapter 20W QC3.0 Type C", 59000, 84000),
    ("Adapter", "AJ-5K", "Adapter+Cable Dual Port GAN 45W Retractable", 165000, 235500),
    ("Adapter", "AJ5W-CC KIT", "Adapter+Cable GAN 45W + Kabel C to C 5A", 116000, 181000),
    ("Adapter", "AJ5S-CC", "Adapter+Cable GAN 35W + Kabel Type-C 60W", 99000, 145000),
    ("Adapter", "AJ5T-CC", "Adapter+Cable GAN 30W + Kabel Type-C 60W", 90000, 131000),
    ("Adapter", "AJ5U-CC", "Adapter+Cable GAN 25W + Kabel Type-C 60W", 83000, 121000),
    ("Adapter", "AJ4C-CL", "Adapter+Cable PD 20W + Kabel PD 27W", 71500, 106000),
    ("Adapter", "AJ-4C C TO C", "Adapter+Cable QC3.0+20W + Kabel Type C", 65000, 84500),
    ("Adapter", "AJ4Y-AC (KIT)", "Adapter+Cable USB-A 20W + Kabel Type C 3A", 51000, 88500),
    ("Adapter", "AJ5A-AC (KIT)", "Adapter+Cable USB-A 18W + Kabel Type C 3A", 43500, 62000),
    ("Adapter", "AJ-3D", "Adapter+Cable 1 port 1.5A + Kabel Micro", 19000, 27000),
    ("Adapter", "AJ5H-AC", "Adapter+Cable Dual Port 2.4A + Kabel C to C", 32800, 57500),
    ("Adapter", "AJ-4E", "Adapter 45W QC3.0 Type C", 99000, 141500),
    ("Adapter", "A196", "Adapter PD-65W 2 Port USB QC3.0 + Type C", 200000, 285500),
    ("Adapter", "DJ-3A", "Car Charger (15pc) 2 Port 2.4A Fast Charging", 250000, 430000),
    ("Adapter", "DJ-5A RETRACTABLE", "Car Charger 120W Retractable 4in1", 125000, 178500),
    ("Adapter", "DJ-5B RETRACTABLE", "Car Charger 120W Voltage Display 4in1", 109000, 155500),
    ("Adapter", "R1B1", "Car Adapter Turbo Charger PD20W+QC3.0", 37000, 53000),
    ("Adapter", "DR-4R", "Car Charger 2 Port QC3.0 25W+PD30W", 78000, 111500),
    ("Adapter", "R1B2Q", "Car Charger 2 Port QC3.0 + Indikator", 41000, 58500),
    ("Adapter", "DJ-3B", "Car Charger 2.4A + Kabel 100cm", 32000, 45500),
    ("Cable", "CJ-5CJ TYPE C JAR", "Charging Cable Jar (15pc) Type C 2.4A 120cm", 91500, 130500),
    ("Cable", "CJ-5CJ Micro", "Charging Cable Jar (15pc) Micro 2.4A 120cm", 78000, 111500),
    ("Cable", "CB-2AEJ Micro JAR", "Data Cable Jar (15pc) Micro Flat 3.0A 100cm", 121500, 173500),
    ("Cable", "CB-2AEJ Type C JAR", "Data Cable Jar (15pc) Type C Flat 3.0A 100cm", 135000, 193000),
    ("Cable", "CB-2AEJ Lightning JAR", "Data Cable Jar (15pc) Lightning Flat 3.0A 100cm", 199500, 285000),
    ("Cable", "CJ-4J C TO C", "Cable Jar (15pc) Type C to C PD 40W 120cm", 192000, 320000),
    ("Cable", "CJ-4G TYPE C JAR", "Charging Cable Jar (20pc) Type C 5A 100cm", 280000, 400000),
    ("Cable", "CJ-4FC JAR", "Charging Cable Jar (20pc) Type C up to 45W", 140000, 200000),
    ("Cable", "CJ-4FL JAR", "Charging Cable Jar (20pc) Lightning up to 45W", 164000, 234000),
    ("Cable", "CB-2E Micro Tray", "Data Cable Tray (21pc) Micro Braided 2.4A", 330000, 471500),
    ("Cable", "CB-2E Lightning Tray", "Data Cable Tray (21pc) Lightning Braided 2.4A", 405300, 579000),
    ("Cable", "CJ5Q-JCC", "Charging Cable Jar (20pc) Braided 60W", 320000, 457000),
    ("Cable", "CJ5H-JAM", "Charging Cable Jar (20pc) Micro 2A 100cm", 94000, 157000),
    ("Cable", "CJ-4P TYPE C WITH DATA", "Charging Cable Box (24pc) Type C Data 3.0A", 201600, 336000),
    ("Cable", "CJ5L-KCL", "Charging Cable Box (15pc) Lightning PD 27W", 354000, 505500),
    ("Cable", "CB-2A7M", "Charging Cable Pastel USB 2.4A 100cm", 21000, 29000),
    ("Cable", "CB-2A7C", "Charging Cable Pastel Type C 2.4A 100cm", 24000, 35000),
    ("Cable", "CB-2A7L", "Charging Cable Pastel Lightning 2.4A 100cm", 25000, 37000),
    ("Cable", "CJ-5R", "Charging Cable Type C Braided PD 60W 100cm", 22000, 31500),
    ("Cable", "CJ-5A", "Data Cable Fast Charging 40W 100cm", 21000, 30000),
    ("Cable", "CR-4S", "Data Cable Type C PD 18W 100cm", 15000, 21500),
    ("Cable", "CJ-4G C To C (2 Meter)", "Charging Cable Type C PD 65W 2 Meter", 35000, 50000),
    ("Cable", "CJ-4XC", "Charging Cable Aluminium PD 66W 120cm", 45000, 75000),
    ("Cable", "CJ-5B Magnetic C to C", "Charging Cable Magnetic PD 65W 100cm", 45000, 64000),
    ("Cable", "CB-2A9 (1m)", "Cable 3 in 1 Nylon 2A 100cm", 30000, 43000),
    ("Cable", "CB-2A9 (1,2m)", "Cable 3 in 1 Nylon 2A 120cm", 33000, 47000),
    ("Earphone", "TWS TJ-4P EXODUS", "Premium TWS ANC + Display", 236000, 337000),
    ("Earphone", "OWS TJ-4Q SPORT", "Open Wearable Stereo BT 5.3", 193000, 275000),
    ("Earphone", "TWS TJ-4F PEGASSUS", "TWS In-Ear BT 5.3", 94000, 134000),
    ("Earphone", "ER5A-J", "Wired Earphone Jar (15pc) Hi-Res 120cm", 195000, 289000),
    ("Earphone", "ER5B", "Balanced Performance Earphone", 19000, 27000),
    ("Earphone", "EJ5A-K", "Wired Earphone Kaleng (20pc) Semi In-Ear", 260000, 372000),
    ("Earphone", "NECKBAND V1 RIVER", "Bluetooth Headset Neckband V5.0", 38000, 54000),
    ("Earphone", "NECKBAND L2 FOREST", "Sport Neckband BT V5.0 300 Jam", 94000, 122200),
    ("Earphone", "NEXUS HJ-4H", "Headphone Wireless BT 5.0", 160000, 228500),
    ("Earphone", "ZENITH HJ-4K", "Headphone Wireless BT 5.3", 140000, 200000),
    ("Earphone", "BHETRIX HJ-4K", "Headphone Wireless BT 5.0", 120000, 171500),
    ("Earphone", "EJ-4V", "Earphone In-Ear Jack 3.5mm 120cm", 19500, 28000),
    ("Earphone", "EJ-4W", "Earphone Semi In-Ear Jack 3.5mm 100cm", 45000, 53000),
    ("Earphone", "EJ-4X", "Earphone In-Ear Jack 3.5mm 120cm", 35000, 46000),
    ("Earphone", "EJ-4R", "Earphone Comfort Eartips Jack 3.5mm 100cm", 42000, 59000),
    ("Speaker", "S4-2AS", "Hera Speaker Bluetooth IPX4", 95000, 135500),
    ("Speaker", "S4-2AR", "Artemis Speaker Bluetooth IPX5", 145000, 207000),
    ("Powerbank", "PJ-4D", "Powerbank 10.000mAh PD 25W", 187500, 270000),
    ("Others", "CJ5J-PCC", "Cable Cross Body Type C PD 60W", 37800, 54000),
    ("Others", "CJ5J-PCL", "Cable Cross Body Lightning PD 27W", 39000, 55500),
    ("Others", "G1-2AI", "Car Holder Rotate Metal-Plastic", 29000, 41500),
    ("Others", "G1-2A8", "Car Holder Rotate Metal-Plastic Modern", 35000, 50000),
    ("Others", "R1A1", "Car Holder All Cars Compatible", 51000, 73000),
    ("Others", "GJ-4I", "Phone Holder Adjustable 360", 45000, 64000),
    ("Others", "RNPH 1001", "Phone Holder Compact", 41400, 59000),
    ("Others", "OR5D", "Mobile Phone Holder Helmet Motor", 49000, 70000),
    ("Others", "GJ-4H", "Selfie Stick Bluetooth Remote 100m", 98000, 140000),
    ("Others", "GJ-4C", "Mousepad Gaming RGB 1.8M", 85000, 105000),
    ("Others", "WIFI REPEATER GJ-4N", "Wifi Repeater 100-300m", 150000, 235000),
]

# Katalog bahan & mesin cutting screen protector — HANYA ada harga dealer per
# box (bukan per pcs), TIDAK ada SRP resmi karena harga jual ke konsumen
# ditentukan sendiri oleh tiap cabang per potongan (dipotong sesuai model HP
# dengan mesin cutting). Tidak dipakai untuk hitung margin potensial —
# disediakan sebagai referensi harga modal saja.
_LUNA_MATERIAL_RAW = [
    ("Alasca Cutting Machine S310 White - A2", 4500000, None),
    ("Alasca Ruby Material Matte", 900000, 50),
    ("Alasca Ruby Material Anti Blue", 900000, 50),
    ("Alasca Ruby Material Clear", 900000, 50),
    ("Alasca Sapphire Material Anti Blue", 725000, 50),
    ("Alasca Sapphire Material Clear", 725000, 50),
    ("Alasca Sapphire Material Matte", 725000, 50),
    ("Alasca Emerald Material Clear", 400036, 50),
    ("Alasca Emerald Material Clear (20pc)", 160000, 20),
    ("Alasca Emerald Material Matte", 400036, 50),
    ("Alasca Emerald Material Anti Blue", 400036, 50),
    ("Alasca Sapphire Material Anti Blue (20pc)", 290000, 20),
    ("Alasca Sapphire Material Matte (20pc)", 290000, 20),
    ("Alaska Ruby Material Anti Spy (10pc)", 447000, 10),
    ("Alaska Ruby Material Tablet 10\" Clear (10pc)", 490000, 10),
    ("Alaska Skin Material Back Cover", 950000, 50),
    ("Vermont Ruby Material Anti Spy (10pc)", 447000, 10),
    ("Vermont Ruby Material Tablet 10\" Clear (10pc)", 490000, 10),
    ("Vermont Ruby Material Anti Blue", 900000, 50),
    ("Vermont Ruby Material Clear", 900000, 50),
    ("Vermont Ruby Material Matte", 900000, 50),
    ("Vermont Sapphire Material Anti Blue", 725000, 50),
    ("Vermont Sapphire Material Clear", 725000, 50),
    ("Vermont Sapphire Material Matte", 725000, 50),
    ("Vermont Emerald Material Clear", 400036, 50),
    ("Vermont Material Back Cover", 950000, 50),
    ("Cutting Machine Material Blader", 75000, None),
    ("Non Slip Mat Cutting Green", 49000, None),
]


def katalog_luna_aksesoris() -> pd.DataFrame:
    """Katalog resmi LUNA (produk aksesoris dengan SRP), lengkap dengan
    potensi profit & margin per unit kalau dijual sesuai SRP dan dibeli
    sesuai harga dealer."""
    df = pd.DataFrame(_LUNA_ACCESSORIES_RAW, columns=["Kategori", "Kode", "Deskripsi", "Dealer", "SRP"])
    df["Potensi Profit"] = df["SRP"] - df["Dealer"]
    df["Potensi Margin (%)"] = np.where(df["SRP"] != 0, df["Potensi Profit"] / df["SRP"] * 100, 0)
    return df


def katalog_luna_material() -> pd.DataFrame:
    """Katalog bahan/mesin cutting LUNA — harga dealer per box saja (tidak
    ada SRP resmi), plus estimasi harga modal per pcs kalau jumlah isi box
    diketahui."""
    df = pd.DataFrame(_LUNA_MATERIAL_RAW, columns=["Nama Barang", "Dealer (per box)", "Isi per Box"])
    df["Estimasi Modal per Pcs"] = np.where(
        df["Isi per Box"].notna() & (df["Isi per Box"] > 0),
        df["Dealer (per box)"] / df["Isi per Box"],
        np.nan,
    )
    return df


def ringkasan_margin_katalog(katalog: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan rata-rata margin potensial per kategori dari katalog LUNA."""
    cols = ["Kategori", "Jumlah Produk", "Rata-rata Dealer", "Rata-rata SRP", "Rata-rata Margin (%)"]
    if katalog.empty:
        return pd.DataFrame(columns=cols)
    g = katalog.groupby("Kategori").agg(
        **{"Jumlah Produk": ("Kode", "count")},
        **{"Rata-rata Dealer": ("Dealer", "mean")},
        **{"Rata-rata SRP": ("SRP", "mean")},
        **{"Rata-rata Margin (%)": ("Potensi Margin (%)", "mean")},
    ).reset_index()
    return g.sort_values("Rata-rata Margin (%)", ascending=False).reset_index(drop=True)[cols]


# ---------------------------------------------------------------------------
# 6. Simulasi insentif penjualan & target pencapaian LUNA
# ---------------------------------------------------------------------------

def simulasi_insentif(
    penjualan_harian_list,
    gp_persen: float = 40,
    hari_kerja: int = 26,
    harian_min: float = 500_000,
    harian_max: float = 2_000_000,
    thp_min: float = 5_000_000,
    thp_max: float = 8_000_000,
) -> pd.DataFrame:
    """Simulasi insentif/THP sales retail dari target penjualan aksesoris
    harian. THP diinterpolasi LINIER antara (harian_min -> thp_min) dan
    (harian_max -> thp_max) — bukan dihitung sebagai % dari Gross Profit
    (supaya tidak terkesan insentif "dibiayai murni" dari GP kategori
    aksesoris saja), tapi kolom "THP thd Gross Profit (%)" tetap ditampilkan
    sebagai informasi seberapa besar porsi GP yang habis kalau insentif ini
    dianggap dibiayai dari situ — berguna untuk cek kewajaran asumsi.
    Nilai di luar rentang harian_min/harian_max tetap di-clip ke thp_min/
    thp_max (tidak diekstrapolasi di luar rentang)."""
    cols = ["Penjualan Harian", "Penjualan Bulanan", f"Gross Profit Bulanan ({gp_persen:.0f}%)", "Estimasi THP", "THP thd Gross Profit (%)"]
    rows = []
    rentang = (harian_max - harian_min) or 1
    for harian in penjualan_harian_list:
        harian = float(harian)
        bulanan = harian * hari_kerja
        gp_bulanan = bulanan * gp_persen / 100
        frac = (harian - harian_min) / rentang
        frac = min(max(frac, 0), 1)
        thp = thp_min + frac * (thp_max - thp_min)
        thp_thd_gp = (thp / gp_bulanan * 100) if gp_bulanan else 0
        rows.append({
            "Penjualan Harian": harian,
            "Penjualan Bulanan": bulanan,
            f"Gross Profit Bulanan ({gp_persen:.0f}%)": gp_bulanan,
            "Estimasi THP": thp,
            "THP thd Gross Profit (%)": thp_thd_gp,
        })
    out = pd.DataFrame(rows)
    return out[cols] if not out.empty else pd.DataFrame(columns=cols)


# ---------------------------------------------------------------------------
# 6b. Matrix insentif resmi (transkrip dari referensi perusahaan) + kalkulator
#     THP Sales Retail yang dikalibrasi ke target Rp 5jt–Rp 8jt/bulan.
# ---------------------------------------------------------------------------

_MATRIX_PEKANAN_RAW = [
    # (Jabatan, Basis Pencapaian, Omzet/Pekan, %Insentif dari GP, Keterangan)
    ("Sales Retail", "Omzet Individu", 5_000_000, 0.05, "Minimum"),
    ("Sales Retail", "Omzet Individu", 6_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 7_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 8_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 9_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 10_000_000, 0.05, "Target 80%"),
    ("Sales Retail", "Omzet Individu", 11_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 12_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 13_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 14_000_000, 0.05, ""),
    ("Sales Retail", "Omzet Individu", 15_000_000, 0.05, "Maksimum"),
    ("Store Manager", "Omzet Toko", 20_000_000, 0.02, "Minimum"),
    ("Store Manager", "Omzet Toko", 25_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 30_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 35_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 40_000_000, 0.02, "Target 80%"),
    ("Store Manager", "Omzet Toko", 45_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 50_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 55_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 60_000_000, 0.02, "Maksimum"),
    ("Regional Manager", "Omzet Regional", 60_000_000, 0.01, "Minimum"),
    ("Regional Manager", "Omzet Regional", 75_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 90_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 105_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 120_000_000, 0.01, "Target 80%"),
    ("Regional Manager", "Omzet Regional", 135_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 150_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 165_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 180_000_000, 0.01, "Maksimum"),
]

GP_PERSEN_MATRIX_PEKANAN = 0.30  # "Asumsi GP 30%" pada matrix resmi (v2)
MINGGU_PER_BULAN_MATRIX = 4  # matrix resmi memakai kelipatan 4 minggu/bulan (bukan 4,33)


def matrix_insentif_pekanan() -> pd.DataFrame:
    """Transkrip persis dari 'MATRIX INSENTIF PEKANAN - RETAIL (IDEAL)' v2:
    Sales Retail (5% dari GP), Store Manager (2%), Regional Manager (1%),
    dengan asumsi GP 30% dari omzet. Kolom Omzet/Bulan & Insentif/Bulan
    dihitung dari kolom mingguan dikali 4 (persis mengikuti matrix resmi,
    bukan 4,33) — sudah diverifikasi cocok 100% dengan angka pada gambar
    referensi untuk seluruh 29 baris."""
    df = pd.DataFrame(_MATRIX_PEKANAN_RAW, columns=["Jabatan", "Basis Pencapaian", "Omzet / Pekan", "% Insentif dari GP", "Keterangan"])
    df["Omzet / Bulan"] = df["Omzet / Pekan"] * MINGGU_PER_BULAN_MATRIX
    df["Estimasi GP (30%)"] = df["Omzet / Pekan"] * GP_PERSEN_MATRIX_PEKANAN
    df["Insentif / Pekan"] = df["Estimasi GP (30%)"] * df["% Insentif dari GP"]
    df["Insentif / Bulan"] = df["Insentif / Pekan"] * MINGGU_PER_BULAN_MATRIX
    return df[[
        "Jabatan", "Basis Pencapaian", "Omzet / Pekan", "Omzet / Bulan", "Estimasi GP (30%)",
        "% Insentif dari GP", "Insentif / Pekan", "Insentif / Bulan", "Keterangan",
    ]]


# ---------------------------------------------------------------------------
# 6b2. Skema BARU (v3) — Tiering Insentif Sales Retail + Manager, transkrip
#      dari berkas "Aksesoris_Skema_Insentif_Tiering_Sales_Retail.xlsx".
#      Sales Retail sekarang beda struktur dari matrix_insentif_pekanan() di
#      atas: GP 30%, insentif 50% dari GP, Gaji Bulanan TETAP Rp4.000.000,
#      THP dihitung langsung per tier (Gaji Bulanan + Insentif/Bulan).
#      Store Manager & Regional Manager tetap sama seperti sebelumnya (GP
#      30%, 2% & 1%) — ditranskrip ulang di sini dari sumber baru yang sama
#      supaya satu sumber data konsisten.
#
#      CATATAN: 2 baris pada berkas sumber tampak salah ketik (dikeluarkan
#      dari transkripsi ini) — baris "Store Manager" Rp15jt/pekan memakai
#      50% insentif (pola Sales Retail, bukan pola Store Manager 2%), dan
#      baris "Regional Manager" Rp60jt/pekan memakai 2% insentif (pola Store
#      Manager, bukan pola Regional Manager 1%). Beri tahu jika ini disengaja.
# ---------------------------------------------------------------------------

_SALES_RETAIL_TIERING_OMZET_PEKAN = [
    750_000, 1_500_000, 2_250_000, 3_000_000, 3_750_000,
    4_500_000, 5_250_000, 6_000_000, 6_750_000, 7_500_000,
]
GP_PERSEN_TIERING = 0.30
INSENTIF_PERSEN_SALES_RETAIL_TIERING = 0.50
GAJI_BULANAN_SALES_RETAIL = 4_000_000
MINGGU_PER_BULAN_TIERING = 4


def matrix_tiering_sales_retail() -> pd.DataFrame:
    """Skema BARU khusus Sales Retail (v3) — transkrip persis dari
    'Aksesoris_Skema_Insentif_Tiering_Sales_Retail.xlsx': 10 tier Omzet/Pekan
    Rp750rb–Rp7,5jt, GP 30%, insentif 50% dari GP, Gaji Bulanan TETAP
    Rp4.000.000, THP = Gaji Bulanan + Insentif/Bulan (dihitung langsung per
    tier, bukan hasil kalibrasi). Sudah diverifikasi cocok 100% dengan
    seluruh 10 baris pada berkas sumber."""
    rows = []
    for omzet_pekan in _SALES_RETAIL_TIERING_OMZET_PEKAN:
        omzet_bulan = omzet_pekan * MINGGU_PER_BULAN_TIERING
        gp_pekan = omzet_pekan * GP_PERSEN_TIERING
        insentif_pekan = gp_pekan * INSENTIF_PERSEN_SALES_RETAIL_TIERING
        insentif_bulan = insentif_pekan * MINGGU_PER_BULAN_TIERING
        thp = GAJI_BULANAN_SALES_RETAIL + insentif_bulan
        rows.append({
            "Tiering Omzet / Pekan": omzet_pekan,
            "Omzet / Bulan": omzet_bulan,
            "Estimasi GP (30%)": gp_pekan,
            "% Insentif dari GP": INSENTIF_PERSEN_SALES_RETAIL_TIERING,
            "Insentif / Pekan": insentif_pekan,
            "Insentif / Bulan": insentif_bulan,
            "Gaji Bulanan": GAJI_BULANAN_SALES_RETAIL,
            "THP": thp,
        })
    return pd.DataFrame(rows)


_MANAGER_TIER_RAW = [
    # (Jabatan, Basis Pencapaian, Omzet / Pekan, % Insentif dari GP, Keterangan)
    ("Store Manager", "Omzet Toko", 20_000_000, 0.02, "Minimum"),
    ("Store Manager", "Omzet Toko", 25_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 30_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 35_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 40_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 45_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 50_000_000, 0.02, ""),
    ("Store Manager", "Omzet Toko", 55_000_000, 0.02, "Maksimum"),
    ("Regional Manager", "Omzet Regional", 60_000_000, 0.01, "Minimum"),
    ("Regional Manager", "Omzet Regional", 75_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 90_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 105_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 120_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 135_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 150_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 165_000_000, 0.01, ""),
    ("Regional Manager", "Omzet Regional", 180_000_000, 0.01, "Maksimum"),
]


def matrix_insentif_manager() -> pd.DataFrame:
    """Store Manager (2% dari GP, 8 tier) & Regional Manager (1% dari GP,
    9 tier) — GP 30%, ditranskrip dari berkas sumber yang sama dengan
    `matrix_tiering_sales_retail()`. 2 baris anomali pada berkas sumber
    (lihat catatan di atas) dikeluarkan dari transkripsi ini."""
    df = pd.DataFrame(_MANAGER_TIER_RAW, columns=["Jabatan", "Basis Pencapaian", "Omzet / Pekan", "% Insentif dari GP", "Keterangan"])
    df["Omzet / Bulan"] = df["Omzet / Pekan"] * MINGGU_PER_BULAN_TIERING
    df["Estimasi GP (30%)"] = df["Omzet / Pekan"] * GP_PERSEN_TIERING
    df["Insentif / Pekan"] = df["Estimasi GP (30%)"] * df["% Insentif dari GP"]
    df["Insentif / Bulan"] = df["Insentif / Pekan"] * MINGGU_PER_BULAN_TIERING
    return df[[
        "Jabatan", "Basis Pencapaian", "Omzet / Pekan", "Omzet / Bulan", "Estimasi GP (30%)",
        "% Insentif dari GP", "Insentif / Pekan", "Insentif / Bulan", "Keterangan",
    ]]



_MATRIX_PER_ITEM_RAW = [
    ("Rp50.000 - Rp100.000", 50_000, 15_000, 7_500),
    (">Rp100.000 - Rp250.000", 100_001, 30_000, 15_000),
    (">Rp250.000 - Rp500.000", 250_001, 75_000, 37_500),
    (">Rp500.000 - Rp750.000", 500_001, 150_000, 75_000),
    (">Rp750.000 - Rp1.000.000", 750_001, 225_000, 112_500),
    (">Rp1.000.000", 1_000_001, 300_000, 150_000),
]

# Pengecualian: produk HYDROGEL (mis. "VIVAN HYDROGEL BASIC ...") dapat
# insentif TETAP per pcs, terlepas dari tingkat harga jualnya pada matrix
# umum di atas — beda perlakuan karena hydrogel biasanya harga jualnya
# tinggi (masuk tingkat atas) tapi marginnya beda karakteristik.
INSENTIF_HYDROGEL_PER_PCS = 10_000
KATA_KUNCI_HYDROGEL = "HYDROGEL"


def matrix_insentif_per_item() -> pd.DataFrame:
    """Transkrip persis dari 'MATRIX INSENTIF PER ITEM' (6 tingkat harga jual,
    asumsi Gross Profit 30% dari harga acuan, Insentif = 50% dari GP secara
    konsisten di semua tingkat) — insentif tetap per unit terjual (bukan %
    dari omzet). CATATAN: produk HYDROGEL PENGECUALIAN dari tabel ini —
    insentifnya tetap Rp10.000/pcs berapa pun harga jualnya, lihat
    `INSENTIF_HYDROGEL_PER_PCS`."""
    df = pd.DataFrame(_MATRIX_PER_ITEM_RAW, columns=["Range Harga Jual", "Harga Acuan", "Gross Profit", "Insentif / Item"])
    df["% Insentif vs GP"] = df["Insentif / Item"] / df["Gross Profit"] * 100
    df["Sisa GP"] = df["Gross Profit"] - df["Insentif / Item"]
    return df[["Range Harga Jual", "Harga Acuan", "Gross Profit", "Insentif / Item", "% Insentif vs GP", "Sisa GP"]]


def kalkulator_thp_sales_retail(
    gaji_pokok: float,
    sertakan_insentif_item: bool = False,
    item_per_hari_per_tier=None,
    sertakan_insentif_hydrogel: bool = False,
    hydrogel_per_hari: float = 0,
    hari_kerja: int = 26,
    thp_min: float = 5_000_000,
    thp_max: float = 8_000_000,
) -> pd.DataFrame:
    """Hitung Total THP Sales Retail untuk tiap tier omzet mingguan pada
    matrix resmi = Gaji Pokok + Insentif %GP Bulanan (kolom "Insentif / Bulan"
    RESMI dari matrix pekanan v2, bukan estimasi minggu×4,33) + opsional
    Insentif Per Item Bulanan (dari matrix per-item, dikali estimasi jumlah
    item terjual/hari per tingkat harga, dikali hari kerja/bulan) + opsional
    Insentif Hydrogel Bulanan (Rp10.000/pcs TETAP, terpisah dari matrix
    per-item karena hydrogel dikecualikan dari aturan tingkat harga umum).
    Beri tanda ✅/⚠️ apakah Total THP masuk rentang target [thp_min, thp_max]."""
    matrix = matrix_insentif_pekanan()
    sales = matrix[matrix["Jabatan"] == "Sales Retail"].copy().reset_index(drop=True)

    sales["Insentif %GP Bulanan"] = sales["Insentif / Bulan"]

    insentif_item_bulanan = 0.0
    if sertakan_insentif_item and item_per_hari_per_tier:
        item_matrix = matrix_insentif_per_item()
        n = min(len(item_matrix), len(item_per_hari_per_tier))
        insentif_item_bulanan = sum(
            float(item_matrix.iloc[i]["Insentif / Item"]) * float(item_per_hari_per_tier[i]) * hari_kerja
            for i in range(n)
        )

    insentif_hydrogel_bulanan = 0.0
    if sertakan_insentif_hydrogel:
        insentif_hydrogel_bulanan = INSENTIF_HYDROGEL_PER_PCS * float(hydrogel_per_hari) * hari_kerja

    sales["Insentif Per Item Bulanan"] = insentif_item_bulanan
    sales["Insentif Hydrogel Bulanan"] = insentif_hydrogel_bulanan
    sales["Gaji Pokok"] = gaji_pokok
    sales["Total THP"] = gaji_pokok + sales["Insentif %GP Bulanan"] + insentif_item_bulanan + insentif_hydrogel_bulanan
    sales["Status Target"] = sales["Total THP"].apply(
        lambda x: "✅ Dalam target" if thp_min <= x <= thp_max else ("⬇️ Di bawah target" if x < thp_min else "⬆️ Di atas target")
    )
    return sales[[
        "Basis Pencapaian", "Omzet / Pekan", "Omzet / Bulan", "Insentif / Pekan", "Insentif %GP Bulanan",
        "Insentif Per Item Bulanan", "Insentif Hydrogel Bulanan", "Gaji Pokok", "Total THP", "Keterangan", "Status Target",
    ]]


def saran_gaji_pokok(
    sertakan_insentif_item: bool = False,
    item_per_hari_per_tier=None,
    sertakan_insentif_hydrogel: bool = False,
    hydrogel_per_hari: float = 0,
    hari_kerja: int = 26,
    thp_min: float = 5_000_000,
) -> float:
    """Saran awal Gaji Pokok supaya tier omzet MINIMUM Sales Retail pas
    mencapai thp_min — titik awal untuk dikalibrasi manual oleh pengguna,
    bukan jawaban final (tier MAKSIMUM belum tentu otomatis pas di thp_max,
    tergantung seberapa besar kontribusi insentif per item & hydrogel)."""
    matrix = matrix_insentif_pekanan()
    sales_min = matrix[(matrix["Jabatan"] == "Sales Retail") & (matrix["Keterangan"] == "Minimum")]
    if sales_min.empty:
        return thp_min
    insentif_min_bulanan = float(sales_min.iloc[0]["Insentif / Bulan"])

    insentif_item_bulanan = 0.0
    if sertakan_insentif_item and item_per_hari_per_tier:
        item_matrix = matrix_insentif_per_item()
        n = min(len(item_matrix), len(item_per_hari_per_tier))
        insentif_item_bulanan = sum(
            float(item_matrix.iloc[i]["Insentif / Item"]) * float(item_per_hari_per_tier[i]) * hari_kerja
            for i in range(n)
        )

    insentif_hydrogel_bulanan = 0.0
    if sertakan_insentif_hydrogel:
        insentif_hydrogel_bulanan = INSENTIF_HYDROGEL_PER_PCS * float(hydrogel_per_hari) * hari_kerja

    return max(thp_min - insentif_min_bulanan - insentif_item_bulanan - insentif_hydrogel_bulanan, 0)


# ---------------------------------------------------------------------------
# 6c. Target penjualan aksesoris per individu Sales Retail
# ---------------------------------------------------------------------------

def target_individual_sales_retail(
    nama_list,
    target_omzet_pekan_list,
    gp_persen: float = 0.30,
    insentif_persen: float = 0.05,
    minggu_per_bulan: int = 4,
) -> pd.DataFrame:
    """Target penjualan aksesoris & estimasi insentif per INDIVIDU Sales
    Retail (bukan per tier omzet umum seperti matrix pekanan) — dipakai
    saat target Store Manager (mis. Rp 60jt/bulan omzet aksesoris) dibagi
    ke beberapa Sales Retail per toko. Pakai persentase yang sama dengan
    matrix pekanan resmi (default GP 30%, insentif Sales Retail 5% dari GP),
    tapi target omzet per pekan BISA BEDA-BEDA per orang (tidak harus rata)."""
    cols = ["Sales Retail", "Target Omzet Aksesoris / Pekan", "Target Omzet Aksesoris / Bulan",
            "Estimasi GP", "Insentif / Pekan", "Insentif / Bulan"]
    rows = []
    n = min(len(nama_list), len(target_omzet_pekan_list))
    for i in range(n):
        nama = nama_list[i]
        omzet_pekan = float(target_omzet_pekan_list[i])
        omzet_bulan = omzet_pekan * minggu_per_bulan
        gp_pekan = omzet_pekan * gp_persen
        insentif_pekan = gp_pekan * insentif_persen
        insentif_bulan = insentif_pekan * minggu_per_bulan
        rows.append({
            "Sales Retail": nama,
            "Target Omzet Aksesoris / Pekan": omzet_pekan,
            "Target Omzet Aksesoris / Bulan": omzet_bulan,
            "Estimasi GP": gp_pekan,
            "Insentif / Pekan": insentif_pekan,
            "Insentif / Bulan": insentif_bulan,
        })
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


def target_penjualan_brand(
    df: pd.DataFrame,
    keyword: str | None = "LUNA",
    target: float = 2_000_000_000,
    tanggal_mulai=None,
    durasi_bulan: int = 12,
    kategori_barang: str | None = None,
    tahap_list=None,
) -> dict:
    """Indikator pencapaian target penjualan produk dengan brand/kata kunci
    tertentu (nama barang mengandung `keyword`, case-insensitive) dalam
    jangka waktu tertentu. Generik — dipakai untuk LUNA (aksesoris) maupun
    UMAIR (parfum), tinggal ganti `keyword`, `kategori_barang`, `target`,
    `tanggal_mulai`, `durasi_bulan`.

    `keyword=None` (atau string kosong) -> TIDAK memfilter brand sama
    sekali, seluruh baris pada `df` (biasanya sudah difilter kategori,
    mis. AKSESORIS) dihitung — dipakai untuk mode "Semua Aksesoris" (bukan
    cuma satu brand seperti LUNA).

    `kategori_barang` opsional: kalau diisi (mis. "PARFUM"), tambahan filter
    KATEGORI_NORM == kategori_barang.upper() — supaya kata kunci brand yang
    kebetulan sama tidak salah tangkap produk dari kategori lain.

    `tahap_list` opsional: list of dict [{"nama": "Tahap 1", "tanggal": ...,
    "target": ...}, ...] — checkpoint target per tahap (mis. milestone
    tanggal tertentu dalam program), dibandingkan dengan pencapaian aktual
    sampai tanggal checkpoint itu.

    Tanggal acuan "hari berjalan" memakai tanggal faktur TERAKHIR pada data
    (bukan tanggal hari ini), supaya persentase tidak terlihat rendah cuma
    karena data belum diperbarui."""
    if tanggal_mulai is None:
        tanggal_mulai = pd.Timestamp("2026-08-01")
    else:
        tanggal_mulai = pd.Timestamp(tanggal_mulai)
    tanggal_selesai = tanggal_mulai + pd.DateOffset(months=durasi_bulan) - pd.Timedelta(days=1)
    total_hari_program = (tanggal_selesai - tanggal_mulai).days + 1

    df_periode = df[(df["TGL FAKTUR"] >= tanggal_mulai) & (df["TGL FAKTUR"] <= tanggal_selesai)]
    if kategori_barang and "KATEGORI_NORM" in df_periode.columns:
        df_periode = df_periode[df_periode["KATEGORI_NORM"] == kategori_barang.strip().upper()]
    if keyword:
        df_brand = df_periode[df_periode["NAMA BARANG"].astype(str).str.upper().str.contains(keyword.upper(), na=False)]
    else:
        df_brand = df_periode
    tercapai = df_brand["TOTAL HARGA"].sum()

    tgl_acuan = df["TGL FAKTUR"].max()
    if pd.isna(tgl_acuan) or tgl_acuan < tanggal_mulai:
        hari_berjalan = 0
    else:
        tgl_efektif = min(tgl_acuan, tanggal_selesai)
        hari_berjalan = (tgl_efektif - tanggal_mulai).days + 1
    hari_berjalan = max(hari_berjalan, 0)

    target_sampai_hari_ini = target * (hari_berjalan / total_hari_program) if total_hari_program else 0
    pct_pencapaian = (tercapai / target_sampai_hari_ini * 100) if target_sampai_hari_ini else 0
    pct_dari_target_penuh = (tercapai / target * 100) if target else 0
    sisa_hari = max(total_hari_program - hari_berjalan, 0)

    tahap_hasil = []
    for tahap in (tahap_list or []):
        tgl_tahap = pd.Timestamp(tahap["tanggal"])
        df_sampai_tahap = df_brand[df_brand["TGL FAKTUR"] <= tgl_tahap]
        tercapai_tahap = df_sampai_tahap["TOTAL HARGA"].sum()
        target_tahap = tahap.get("target", 0)
        tahap_hasil.append({
            "nama": tahap.get("nama", ""),
            "tanggal": tgl_tahap,
            "target": target_tahap,
            "tercapai": tercapai_tahap,
            "pct": (tercapai_tahap / target_tahap * 100) if target_tahap else 0,
        })

    return dict(
        tercapai=tercapai,
        target=target,
        target_sampai_hari_ini=target_sampai_hari_ini,
        pct_pencapaian=pct_pencapaian,
        pct_dari_target_penuh=pct_dari_target_penuh,
        tanggal_mulai=tanggal_mulai,
        tanggal_selesai=tanggal_selesai,
        hari_berjalan=hari_berjalan,
        total_hari_program=total_hari_program,
        sisa_hari=sisa_hari,
        tgl_acuan=tgl_acuan,
        jumlah_transaksi=len(df_brand),
        tahap=tahap_hasil,
    )


def target_penjualan_luna(
    df: pd.DataFrame,
    target: float = 2_000_000_000,
    tanggal_mulai=None,
    durasi_bulan: int = 12,
    tahap_list=None,
) -> dict:
    """Alias khusus LUNA dari `target_penjualan_brand()` — dipertahankan
    untuk kompatibilitas kode yang sudah ada."""
    return target_penjualan_brand(
        df, keyword="LUNA", target=target, tanggal_mulai=tanggal_mulai,
        durasi_bulan=durasi_bulan, tahap_list=tahap_list,
    )


def target_brand_per_cabang(
    df_aksesoris: pd.DataFrame,
    target_total: float,
    tanggal_mulai,
    durasi_bulan: int = 3,
    keyword: str | None = "LUNA",
    target_per_cabang: dict | None = None,
) -> pd.DataFrame:
    """Monitoring pencapaian target penjualan brand (mis. LUNA) PER CABANG,
    untuk satu periode. 9 kolom sesuai spesifikasi:
    Cabang, Target, Result, Expected, % Actual, % Expected, GAP,
    Target Kejar Per Hari, Sisa Hari.

    `keyword=None` (atau string kosong) -> TIDAK memfilter brand, seluruh
    baris pada `df_aksesoris` dihitung — dipakai untuk mode "Semua
    Aksesoris" (bukan cuma satu brand seperti LUNA).

    `target_per_cabang` opsional: dict {nama_cabang: nilai_target_rp} untuk
    distribusi target TIDAK RATA antar cabang. Kalau tidak diisi, target
    dibagi RATA ke seluruh cabang yang ada di data (`target_total / jumlah
    cabang`).

    Tanggal acuan "hari berjalan" memakai tanggal faktur TERAKHIR pada
    SELURUH data (bukan cuma yang sudah masuk periode ini) — konsisten
    dengan `target_penjualan_brand()` — supaya persentase tidak terlihat
    rendah cuma karena data belum diperbarui."""
    cols = ["Cabang", "Target", "Result", "Expected", "% Actual", "% Expected", "GAP", "Target Kejar Per Hari", "Sisa Hari"]
    if df_aksesoris.empty:
        return pd.DataFrame(columns=cols)

    tanggal_mulai = pd.Timestamp(tanggal_mulai)
    tanggal_selesai = tanggal_mulai + pd.DateOffset(months=durasi_bulan) - pd.Timedelta(days=1)
    total_hari = (tanggal_selesai - tanggal_mulai).days + 1

    # Hari berjalan & sisa hari — dari tanggal faktur TERAKHIR di seluruh data
    tgl_acuan = df_aksesoris["TGL FAKTUR"].max()
    if pd.isna(tgl_acuan) or tgl_acuan < tanggal_mulai:
        hari_berjalan = 0
    else:
        tgl_efektif = min(tgl_acuan, tanggal_selesai)
        hari_berjalan = (tgl_efektif - tanggal_mulai).days + 1
    hari_berjalan = max(hari_berjalan, 0)
    sisa_hari = max(total_hari - hari_berjalan, 0)

    df_periode = df_aksesoris[(df_aksesoris["TGL FAKTUR"] >= tanggal_mulai) & (df_aksesoris["TGL FAKTUR"] <= tanggal_selesai)]
    if keyword:
        mask_brand = df_periode["NAMA BARANG"].astype(str).str.upper().str.contains(keyword.upper(), na=False)
        result_per_cabang = df_periode[mask_brand].groupby("CABANG")["TOTAL HARGA"].sum()
    else:
        result_per_cabang = df_periode.groupby("CABANG")["TOTAL HARGA"].sum()

    semua_cabang = sorted(df_aksesoris["CABANG"].dropna().unique().tolist())
    n_cabang = len(semua_cabang) or 1

    rows = []
    for cabang in semua_cabang:
        if target_per_cabang and cabang in target_per_cabang:
            target_cabang = float(target_per_cabang[cabang])
        else:
            target_cabang = target_total / n_cabang

        result = float(result_per_cabang.get(cabang, 0))
        expected = target_cabang * (hari_berjalan / total_hari) if total_hari else 0
        pct_actual = (result / target_cabang * 100) if target_cabang else 0
        pct_expected = (expected / target_cabang * 100) if target_cabang else 0
        gap = result - expected
        target_kejar_per_hari = (max(target_cabang - result, 0) / sisa_hari) if sisa_hari else 0

        rows.append({
            "Cabang": cabang,
            "Target": target_cabang,
            "Result": result,
            "Expected": expected,
            "% Actual": pct_actual,
            "% Expected": pct_expected,
            "GAP": gap,
            "Target Kejar Per Hari": target_kejar_per_hari,
            "Sisa Hari": sisa_hari,
        })

    return pd.DataFrame(rows, columns=cols)


def tambah_baris_total(df_per_cabang: pd.DataFrame, label: str = "TOTAL JARINGAN") -> pd.DataFrame:
    """Tambahkan baris rekapan TOTAL di paling bawah tabel monitoring per
    cabang — kolom Rp dijumlahkan, kolom % dihitung ulang dari rasio total
    (bukan dijumlah/dirata begitu saja, supaya tetap akurat secara
    matematis), "Sisa Hari" diambil dari baris pertama (sama untuk semua
    cabang dalam satu periode). Berlaku untuk skema kolom
    `target_brand_per_cabang()` (9 kolom) maupun skema Tahap 1 yang lebih
    ringkas (Cabang, Target, Result, % Actual, GAP)."""
    if df_per_cabang.empty:
        return df_per_cabang

    total = {"Cabang": label}
    kolom_rp_jumlah = [c for c in ["Target", "Result", "Expected", "GAP", "Target Kejar Per Hari"] if c in df_per_cabang.columns]
    for c in kolom_rp_jumlah:
        total[c] = df_per_cabang[c].sum()

    target_total = total.get("Target", 0)
    if "% Actual" in df_per_cabang.columns:
        total["% Actual"] = (total.get("Result", 0) / target_total * 100) if target_total else 0
    if "% Expected" in df_per_cabang.columns:
        total["% Expected"] = (total.get("Expected", 0) / target_total * 100) if target_total else 0
    if "Sisa Hari" in df_per_cabang.columns:
        total["Sisa Hari"] = df_per_cabang["Sisa Hari"].iloc[0]

    baris_total = pd.DataFrame([total])[df_per_cabang.columns]
    return pd.concat([df_per_cabang, baris_total], ignore_index=True)


# Target Tahap 1 per cabang (referensi resmi) — total persis Rp 300.006.600.
TARGET_TAHAP1_LUNA_PER_CABANG = {
    "Klender": 16_690_500, "Ceger": 16_651_500, "Bintara": 16_892_100,
    "Radjiman": 16_651_500, "Jatimulya": 16_651_500, "Dramaga": 16_651_500,
    "Condet": 16_651_500, "Jatibening": 16_651_500, "Sawangan": 16_651_500,
    "Warbong": 16_651_500, "Cinere": 16_651_500, "Cibinong": 16_651_500,
    "Karawang": 16_651_500, "Jatiwaringin": 16_651_500, "Cikampek": 16_651_500,
    "Cilangkap": 16_651_500, "Pejaten": 16_651_500, "Cibubur": 16_651_500,
}


def monitoring_tahap_per_cabang(
    df_aksesoris: pd.DataFrame,
    target_per_cabang: dict,
    tanggal_mulai,
    tanggal_evaluasi=None,
    keyword: str = "LUNA",
    keyword_kecuali: str | None = None,
) -> pd.DataFrame:
    """Monitoring pencapaian MILESTONE/TAHAP tetap per cabang (bukan target
    rate-per-hari seperti `target_brand_per_cabang()`) — dipakai untuk
    Tahap 1: target per cabang sudah ditentukan di muka (`target_per_cabang`),
    dihitung KUMULATIF sejak `tanggal_mulai` (tanggal produk mulai
    didistribusikan/bisa mulai transaksi) sampai `tanggal_evaluasi`.

    `tanggal_evaluasi` opsional: kalau tidak diisi, otomatis memakai tanggal
    faktur TERAKHIR pada data (bukan tanggal hari ini) — supaya pencapaian
    tidak terlihat rendah cuma karena dievaluasi persis di tanggal_mulai
    (kesalahan yang sempat terjadi di versi sebelumnya). Bisa juga diisi
    manual kalau ingin evaluasi di tanggal tertentu.

    `keyword_kecuali` opsional: nama barang yang mengandung kata ini
    DIKELUARKAN dari perhitungan Result, meski juga mengandung `keyword`
    (mis. keyword="LUNA", keyword_kecuali="HYDROGEL" — untuk target Tahap 1
    yang khusus LUNA SELAIN varian Hydrogel, karena Hydrogel punya skema
    insentif & mungkin target terpisah sendiri)."""
    cols = ["Cabang", "Target", "Result", "% Actual", "GAP"]
    if df_aksesoris.empty or not target_per_cabang:
        return pd.DataFrame(columns=cols)

    tanggal_mulai = pd.Timestamp(tanggal_mulai)
    if tanggal_evaluasi is None:
        tanggal_evaluasi = df_aksesoris["TGL FAKTUR"].max()
        if pd.isna(tanggal_evaluasi):
            tanggal_evaluasi = tanggal_mulai
    else:
        tanggal_evaluasi = pd.Timestamp(tanggal_evaluasi)

    df_periode = df_aksesoris[(df_aksesoris["TGL FAKTUR"] >= tanggal_mulai) & (df_aksesoris["TGL FAKTUR"] <= tanggal_evaluasi)]
    nama_upper = df_periode["NAMA BARANG"].astype(str).str.upper()
    mask_brand = nama_upper.str.contains(keyword.upper(), na=False)
    if keyword_kecuali:
        mask_brand = mask_brand & ~nama_upper.str.contains(keyword_kecuali.upper(), na=False)
    result_per_cabang = df_periode[mask_brand].groupby("CABANG")["TOTAL HARGA"].sum()

    rows = []
    for cabang, target_cabang in target_per_cabang.items():
        result = float(result_per_cabang.get(cabang, 0))
        pct_actual = (result / target_cabang * 100) if target_cabang else 0
        gap = result - target_cabang
        rows.append({"Cabang": cabang, "Target": target_cabang, "Result": result, "% Actual": pct_actual, "GAP": gap})

    return pd.DataFrame(rows, columns=cols)


def detail_produk_brand_cabang(
    df_aksesoris: pd.DataFrame,
    cabang: str,
    tanggal_mulai,
    tanggal_evaluasi,
    keyword: str = "LUNA",
    keyword_kecuali: str | None = None,
) -> pd.DataFrame:
    """Rincian PER JENIS PRODUK (Nama Barang) untuk satu cabang, dalam
    rentang tanggal tertentu — dipakai untuk "drill-down" dari tabel
    monitoring per cabang: pilih satu cabang, lihat barang apa saja
    yang terjual dan berapa kuantitasnya yang menyusun angka Result-nya."""
    cols = ["Nama Barang", "Qty", "Omzet"]
    if df_aksesoris.empty:
        return pd.DataFrame(columns=cols)

    tanggal_mulai = pd.Timestamp(tanggal_mulai)
    tanggal_evaluasi = pd.Timestamp(tanggal_evaluasi)
    df_periode = df_aksesoris[
        (df_aksesoris["TGL FAKTUR"] >= tanggal_mulai) &
        (df_aksesoris["TGL FAKTUR"] <= tanggal_evaluasi) &
        (df_aksesoris["CABANG"] == cabang)
    ]
    nama_upper = df_periode["NAMA BARANG"].astype(str).str.upper()
    mask = nama_upper.str.contains(keyword.upper(), na=False)
    if keyword_kecuali:
        mask = mask & ~nama_upper.str.contains(keyword_kecuali.upper(), na=False)
    df_brand = df_periode[mask]
    if df_brand.empty:
        return pd.DataFrame(columns=cols)

    g = df_brand.groupby("NAMA BARANG").agg(
        Qty=("QTY", "sum"), Omzet=("TOTAL HARGA", "sum"),
    ).reset_index().rename(columns={"NAMA BARANG": "Nama Barang"})
    g = g.sort_values("Omzet", ascending=False).reset_index(drop=True)
    return g[cols]


def warna_indikator_pencapaian(pct):
    """Warna indikator ambang batas: <85% Merah, 85–99% Kuning, ≥100% Hijau.
    Dipakai lewat pandas Styler (`.map(warna_indikator_pencapaian, subset=[...])`)
    pada kolom persentase pencapaian."""
    try:
        v = float(pct)
    except (TypeError, ValueError):
        return ""
    if v < 85:
        return "background-color: #f5c6cb; color: #58151c;"
    elif v < 100:
        return "background-color: #ffe69c; color: #664d03;"
    else:
        return "background-color: #c3e6cb; color: #0f5132;"


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
