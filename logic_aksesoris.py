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


def load_aksesoris(file_or_path, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Baca berkas Excel (sheet Rincian Faktur Penjualan) atau CSV sepadan."""
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

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns and c != "Cabang"]
    if "CABANG" not in df.columns:
        missing.append("CABANG")
    if missing:
        raise ValueError("Kolom berikut tidak ditemukan di berkas: " + ", ".join(missing))

    df = df.copy()
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
    cols = ["Cabang", "Omzet", "Modal", "Laba", "Margin (%)", "Jumlah Nota", "Rata-rata / Nota"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.groupby("CABANG").agg(
        Omzet=("TOTAL HARGA", "sum"),
        Modal=("MODAL", "sum"),
        Laba=("LABA", "sum"),
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index().rename(columns={"CABANG": "Cabang"})
    g["Margin (%)"] = np.where(g["Omzet"] != 0, g["Laba"] / g["Omzet"] * 100, 0)
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
