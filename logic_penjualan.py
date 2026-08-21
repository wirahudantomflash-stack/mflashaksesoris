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

# CABANG sengaja TIDAK wajib di sini — file rincian per cabang dari sistem
# sumbernya sering tidak menyertakan kolom CABANG sama sekali (karena satu
# file memang hanya berisi satu cabang). Ketiadaan kolom itu ditangani lewat
# `finalize_data(..., cabang_default=...)`, bukan dianggap error baca berkas.
REQUIRED_COLUMNS = [
    "TGL FAKTUR", "NO FAKTUR", "KATEGORI BARANG", "NAMA BARANG",
    "HARGA BELI", "QTY", "@HARGA", "TOTAL HARGA", "NAMA CUSTOMER",
    "ID PELANGGAN", "KATEGORI PELANGGAN", "KATEGORI PENJUALAN",
    "NAMA TEKNISI (FINAL)", "YANG MENYERAHKAN/MENJUAL",
]


class MissingCabangColumn(Exception):
    """Berkas terbaca sukses tapi tidak punya kolom CABANG (file 1 cabang)."""


def read_raw(file_or_path) -> pd.DataFrame:
    """Baca csv/csv.gz ATAU xlsx (sheet 'Rincian Faktur Penjualan') dan validasi
    kolom wajib (di luar CABANG)."""
    name = getattr(file_or_path, "name", str(file_or_path))
    is_excel = str(name).lower().endswith((".xlsx", ".xls"))

    if is_excel:
        try:
            df = pd.read_excel(file_or_path, sheet_name="Rincian Faktur Penjualan")
        except ValueError:
            # Sheet dengan nama lain / hanya satu sheet di berkas -> pakai yang pertama
            df = pd.read_excel(file_or_path, sheet_name=0)
    else:
        df = pd.read_csv(file_or_path, compression="infer", low_memory=False)

    # Normalisasi nama kolom cabang: sumber kadang menulis "Cabang", kadang
    # "CABANG" — disamakan ke "CABANG" supaya terdeteksi konsisten di bawah.
    rename_map = {c: "CABANG" for c in df.columns if str(c).strip().upper() == "CABANG"}
    if rename_map:
        df = df.rename(columns=rename_map)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Kolom berikut tidak ditemukan di berkas: " + ", ".join(missing)
        )
    return df


def finalize_data(df: pd.DataFrame, cabang_default: str | None = None) -> pd.DataFrame:
    """Normalisasi tipe data, kunci nota, kategori, modal/laba.

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


def load_penjualan(file_or_path, cabang_default: str | None = None) -> pd.DataFrame:
    """Baca + finalisasi dalam satu langkah (dipakai kalau nama cabang sudah diketahui
    di awal, atau kalau berkas sudah pasti punya kolom CABANG sendiri)."""
    return finalize_data(read_raw(file_or_path), cabang_default=cabang_default)


def apply_filters(df: pd.DataFrame, tahun=None, bulan=None, cabang=None) -> pd.DataFrame:
    out = df
    if tahun:
        out = out[out["TAHUN"].isin(tahun)]
    if bulan:
        out = out[out["BULAN"].isin(bulan)]
    if cabang:
        out = out[out["CABANG"].isin(cabang)]
    return out


def top_cabang(df: pd.DataFrame, metric: str = "Omzet", n: int | None = 3) -> pd.DataFrame:
    """Ranking cabang berdasarkan omzet, laba, atau jumlah nota.
    n=None -> tampilkan SELURUH cabang (tidak dibatasi)."""
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
    g = g.sort_values(sort_col, ascending=False).reset_index(drop=True)
    if n is not None:
        g = g.head(n)
    g.index = g.index + 1
    return g[["CABANG", "Omzet", "Modal", "Laba", "Margin (%)", "Jumlah Nota"]]


def top_produk(df: pd.DataFrame, metric: str = "Omzet", n: int | None = 10, hanya_aksesoris: bool = False) -> pd.DataFrame:
    """Ranking produk berdasarkan qty terjual atau omzet.
    n=None -> tampilkan SEMUA produk (tidak dibatasi).
    hanya_aksesoris=True -> filter ke KATEGORI BARANG NORM == "AKSESORIS" saja."""
    d = df
    if hanya_aksesoris:
        d = d[d["KATEGORI BARANG NORM"] == "AKSESORIS"]

    if d.empty:
        return pd.DataFrame(columns=["NAMA BARANG", "Kategori", "Qty Terjual", "Omzet", "Laba"])

    g = d.groupby("NAMA BARANG", dropna=False).agg(
        Kategori=("KATEGORI BARANG NORM", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
        **{"Qty Terjual": ("QTY", "sum")},
        Omzet=("TOTAL HARGA", "sum"),
        Laba=("LABA", "sum"),
    ).reset_index()

    sort_col = {"Qty Terjual": "Qty Terjual", "Omzet": "Omzet"}[metric]
    g = g.sort_values(sort_col, ascending=False).reset_index(drop=True)
    if n is not None:
        g = g.head(n)
    g.index = g.index + 1
    return g[["NAMA BARANG", "Kategori", "Qty Terjual", "Omzet", "Laba"]]


def ranking_sales(
    df: pd.DataFrame,
    metric: str = "Omzet",
    n: int | None = 5,
    kategori_penjualan: list[str] | None = None,
) -> pd.DataFrame:
    """Ranking sales/penjual berdasarkan omzet, laba, atau jumlah nota.
    n=None -> tampilkan SELURUH sales (tidak dibatasi).
    kategori_penjualan=None -> semua kategori penjualan diikutsertakan (tidak
    dibatasi ke retail saja)."""
    d = df if not kategori_penjualan else df[df["KATEGORI PENJUALAN"].isin(kategori_penjualan)]
    if d.empty:
        return pd.DataFrame(columns=["Sales", "Omzet", "Laba", "Jumlah Nota"])

    g = d.groupby("YANG MENYERAHKAN/MENJUAL", dropna=False).agg(
        Omzet=("TOTAL HARGA", "sum"),
        Laba=("LABA", "sum"),
        **{"Jumlah Nota": ("NOTA_ID", "nunique")},
    ).reset_index().rename(columns={"YANG MENYERAHKAN/MENJUAL": "Sales"})

    sort_col = {"Omzet": "Omzet", "Laba": "Laba", "Jumlah Nota": "Jumlah Nota"}[metric]
    g = g.sort_values(sort_col, ascending=False).reset_index(drop=True)
    if n is not None:
        g = g.head(n)
    g.index = g.index + 1
    return g[["Sales", "Omzet", "Laba", "Jumlah Nota"]]


# Alias lama dipertahankan supaya tidak memutus kode lain yang mungkin masih memanggilnya.
def top_sales_retail(df, retail_values, metric="Omzet", n=5):
    return ranking_sales(df, metric=metric, n=n, kategori_penjualan=retail_values)


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
