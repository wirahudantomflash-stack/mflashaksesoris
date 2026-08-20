"""
Logika inti untuk dashboard MFLASH — Top Cabang / Top Produk / Top Sales.

Aturan data (WAJIB, sesuai instruksi):
1. Satu nota = kombinasi CABANG + NO FAKTUR (nomor faktur berjalan sendiri
   per cabang, sehingga nomor yang sama bisa muncul di beberapa cabang).
2. HARGA BELI sudah berupa TOTAL per baris, bukan harga satuan.
   MODAL = HARGA BELI (tidak dikalikan QTY lagi).
   LABA  = TOTAL HARGA - HARGA BELI.
3. Baris kembar pada data penjualan TIDAK dibuang — dihitung apa adanya.
4. Kategori aksesoris ditulis dua cara di sumber: AKSESORIS dan ACCESORIES.
   Keduanya digabung jadi satu kategori "AKSESORIS" untuk pelaporan.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "TGL FAKTUR", "NO FAKTUR", "CABANG", "KATEGORI BARANG", "NAMA BARANG",
    "HARGA BELI", "QTY", "@HARGA", "TOTAL HARGA", "NAMA CUSTOMER",
    "ID PELANGGAN", "KATEGORI PELANGGAN", "KATEGORI PENJUALAN",
    "NAMA TEKNISI (FINAL)", "YANG MENYERAHKAN/MENJUAL",
]


def load_penjualan(file_or_path) -> pd.DataFrame:
    """Baca penjualan.csv.gz (atau file csv/csv.gz apa pun dengan skema yang sama)."""
    df = pd.read_csv(file_or_path, compression="infer", low_memory=False)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Kolom berikut tidak ditemukan di berkas: " + ", ".join(missing)
        )

    # Tipe data
    df["TGL FAKTUR"] = pd.to_datetime(df["TGL FAKTUR"], errors="coerce", dayfirst=False)
    for col in ["HARGA BELI", "QTY", "@HARGA", "TOTAL HARGA"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Kunci nota = CABANG + NO FAKTUR (bukan NO FAKTUR saja)
    df["NOTA_ID"] = df["CABANG"].astype(str).str.strip() + "||" + df["NO FAKTUR"].astype(str).str.strip()

    # Gabungkan AKSESORIS / ACCESORIES
    kat = df["KATEGORI BARANG"].astype(str).str.strip().str.upper()
    kat = kat.replace({"ACCESORIES": "AKSESORIS", "ACCESSORIES": "AKSESORIS"})
    df["KATEGORI BARANG NORM"] = kat

    # Modal & laba per baris (HARGA BELI sudah total, jangan dikalikan QTY lagi)
    df["MODAL"] = df["HARGA BELI"]
    df["LABA"] = df["TOTAL HARGA"] - df["MODAL"]

    df["TAHUN"] = df["TGL FAKTUR"].dt.year
    df["BULAN"] = df["TGL FAKTUR"].dt.month

    return df


def apply_filters(df: pd.DataFrame, tahun=None, bulan=None, cabang=None) -> pd.DataFrame:
    out = df
    if tahun:
        out = out[out["TAHUN"].isin(tahun)]
    if bulan:
        out = out[out["BULAN"].isin(bulan)]
    if cabang:
        out = out[out["CABANG"].isin(cabang)]
    return out


def top_cabang(df: pd.DataFrame, metric: str = "Omzet", n: int = 3) -> pd.DataFrame:
    """Top N cabang berdasarkan omzet, laba, atau jumlah nota."""
    if df.empty:
        return pd.DataFrame(columns=["CABANG", "Omzet", "Modal", "Laba", "Margin (%)", "Jumlah Nota"])

    g = df.groupby("CABANG", dropna=False).agg(
        Omzet=("TOTAL HARGA", "sum"),
        Modal=("MODAL", "sum"),
        Laba=("LABA", "sum"),
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index()
    g["Margin (%)"] = np.where(g["Omzet"] != 0, g["Laba"] / g["Omzet"] * 100, 0)

    sort_col = {"Omzet": "Omzet", "Laba": "Laba", "Jumlah Nota": "Jumlah Nota"}[metric]
    g = g.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)
    g.index = g.index + 1
    return g[["CABANG", "Omzet", "Modal", "Laba", "Margin (%)", "Jumlah Nota"]]


def top_produk(df: pd.DataFrame, metric: str = "Omzet", n: int = 10) -> pd.DataFrame:
    """Top N produk terlaris berdasarkan qty terjual atau omzet."""
    if df.empty:
        return pd.DataFrame(columns=["NAMA BARANG", "Kategori", "Qty Terjual", "Omzet", "Laba"])

    g = df.groupby("NAMA BARANG", dropna=False).agg(
        Kategori=("KATEGORI BARANG NORM", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
        **{"Qty Terjual": ("QTY", "sum")},
        Omzet=("TOTAL HARGA", "sum"),
        Laba=("LABA", "sum"),
    ).reset_index()

    sort_col = {"Qty Terjual": "Qty Terjual", "Omzet": "Omzet"}[metric]
    g = g.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)
    g.index = g.index + 1
    return g[["NAMA BARANG", "Kategori", "Qty Terjual", "Omzet", "Laba"]]


def top_sales_retail(
    df: pd.DataFrame,
    retail_values: list[str],
    metric: str = "Omzet",
    n: int = 5,
) -> pd.DataFrame:
    """Top N sales/penjual pada transaksi retail (KATEGORI PENJUALAN sesuai retail_values)."""
    d = df[df["KATEGORI PENJUALAN"].isin(retail_values)]
    if d.empty:
        return pd.DataFrame(columns=["Sales", "Omzet", "Laba", "Jumlah Nota"])

    g = d.groupby("YANG MENYERAHKAN/MENJUAL", dropna=False).agg(
        Omzet=("TOTAL HARGA", "sum"),
        Laba=("LABA", "sum"),
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index().rename(columns={"YANG MENYERAHKAN/MENJUAL": "Sales"})

    sort_col = {"Omzet": "Omzet", "Laba": "Laba", "Jumlah Nota": "Jumlah Nota"}[metric]
    g = g.sort_values(sort_col, ascending=False).head(n).reset_index(drop=True)
    g.index = g.index + 1
    return g[["Sales", "Omzet", "Laba", "Jumlah Nota"]]


# ---------------------------------------------------------------------------
# Format angka gaya Indonesia: 68.838 / 1.234,5 / 10,3%
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
