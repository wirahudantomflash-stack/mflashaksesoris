"""
Logika inti — Dashboard Porsi Pemasok Aksesoris (MFLASH, 18 cabang).

Sumber data: sheet "DB Pembelian" pada berkas Excel pembelian aksesoris
regional, atau CSV dengan skema kolom yang sama.

Aturan/asumsi yang diterapkan (mengikuti pola dashboard MFLASH sebelumnya):
1. Nama kategori barang ditulis dua cara di sumber ("AKSESORIS", "Aksesoris")
   -> digabung jadi satu, dan data difilter hanya kategori aksesoris.
2. Nama pemasok punya variasi huruf besar/kecil ("LUNA" vs "Luna",
   "Supplier Umum" vs "SUPPLIER UMUM") -> disatukan dengan menaikkan semua
   ke huruf kapital sebagai kunci pengelompokan & tampilan.
3. Nilai pembelian per baris dipakai apa adanya dari kolom "Total Harga"
   (tidak dihitung ulang dari Kuantitas x @Harga, supaya tetap mengikuti
   sumber persis seperti aturan pada dashboard penjualan sebelumnya).
4. Angka ditampilkan gaya Indonesia (68.838 / 10,3% / Rp 4.711.790.000).
"""

from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Cabang", "Tanggal", "Nomor #", "Nama Kategori Barang", "Kode #",
    "Nama Barang", "Kuantitas", "@Harga", "Total Harga", "Pemasok",
]

SHEET_NAME = "DB Pembelian"


def load_pembelian(file_or_path, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Baca berkas Excel (sheet DB Pembelian) atau CSV dengan skema yang sama."""
    name = getattr(file_or_path, "name", str(file_or_path))
    is_excel = str(name).lower().endswith((".xlsx", ".xls"))

    if is_excel:
        df = pd.read_excel(file_or_path, sheet_name=sheet_name)
    else:
        df = pd.read_csv(file_or_path, compression="infer", low_memory=False)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Kolom berikut tidak ditemukan di berkas: " + ", ".join(missing)
        )

    df = df.copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=False)
    for col in ["Kuantitas", "@Harga", "Total Harga"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Normalisasi kategori barang -> hanya AKSESORIS yang dipertahankan
    kat = df["Nama Kategori Barang"].astype(str).str.strip().str.upper()
    kat = kat.replace({"ACCESORIES": "AKSESORIS", "ACCESSORIES": "AKSESORIS"})
    df["KATEGORI_NORM"] = kat
    df = df[df["KATEGORI_NORM"] == "AKSESORIS"].copy()

    # Normalisasi nama pemasok & nama barang (kunci pengelompokan)
    df["PEMASOK_NORM"] = df["Pemasok"].astype(str).str.strip().str.upper()
    df["NAMA_BARANG_NORM"] = df["Nama Barang"].astype(str).str.strip().str.upper()
    df["CABANG"] = df["Cabang"].astype(str).str.strip()

    df["TAHUN"] = df["Tanggal"].dt.year
    df["BULAN"] = df["Tanggal"].dt.month

    if "KATEGORI KEBUTUHAN" in df.columns:
        df["KATEGORI KEBUTUHAN"] = df["KATEGORI KEBUTUHAN"].astype(str).str.strip()

    return df


def apply_filters(df: pd.DataFrame, tahun=None, bulan=None, cabang=None, kebutuhan=None) -> pd.DataFrame:
    out = df
    if tahun:
        out = out[out["TAHUN"].isin(tahun)]
    if bulan:
        out = out[out["BULAN"].isin(bulan)]
    if cabang:
        out = out[out["CABANG"].isin(cabang)]
    if kebutuhan and "KATEGORI KEBUTUHAN" in out.columns:
        out = out[out["KATEGORI KEBUTUHAN"].isin(kebutuhan)]
    return out


def porsi_pemasok(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking pemasok dari terbesar ke terkecil, dengan porsi % dan kumulatif %."""
    cols = ["Pemasok", "Total Pembelian", "Jumlah Transaksi", "Porsi (%)", "Kumulatif (%)"]
    if df.empty:
        return pd.DataFrame(columns=cols)

    g = df.groupby("PEMASOK_NORM").agg(
        **{"Total Pembelian": ("Total Harga", "sum")},
        **{"Jumlah Transaksi": ("Nomor #", "nunique")},
    ).reset_index().rename(columns={"PEMASOK_NORM": "Pemasok"})

    total = g["Total Pembelian"].sum()
    g = g.sort_values("Total Pembelian", ascending=False).reset_index(drop=True)
    g["Porsi (%)"] = np.where(total != 0, g["Total Pembelian"] / total * 100, 0)
    g["Kumulatif (%)"] = g["Porsi (%)"].cumsum()
    g.index = g.index + 1
    return g[cols]


def luna_progress(df: pd.DataFrame, target: float, supplier_key: str = "LUNA") -> dict:
    """Ringkasan pencapaian target pembelian ke satu pemasok (default: LUNA)."""
    total_aksesoris = df["Total Harga"].sum()
    df_supplier = df[df["PEMASOK_NORM"] == supplier_key]
    tercapai = df_supplier["Total Harga"].sum()

    pct_target = (tercapai / target * 100) if target else 0
    pct_dari_total_aksesoris = (tercapai / total_aksesoris * 100) if total_aksesoris else 0
    sisa = max(target - tercapai, 0)

    tgl_min = df["Tanggal"].min()
    tgl_max = df["Tanggal"].max()
    hari_berjalan = max((tgl_max - tgl_min).days + 1, 1) if pd.notna(tgl_min) and pd.notna(tgl_max) else 1
    run_rate_harian = tercapai / hari_berjalan if hari_berjalan else 0

    return {
        "tercapai": tercapai,
        "target": target,
        "pct_target": pct_target,
        "sisa": sisa,
        "pct_dari_total_aksesoris": pct_dari_total_aksesoris,
        "total_aksesoris": total_aksesoris,
        "hari_berjalan": hari_berjalan,
        "run_rate_harian": run_rate_harian,
        "tgl_min": tgl_min,
        "tgl_max": tgl_max,
    }


def per_cabang_kepatuhan(df: pd.DataFrame, supplier_key: str = "LUNA") -> pd.DataFrame:
    """Per cabang: total belanja aksesoris, belanja ke pemasok target, dan porsinya.
    Diurutkan dari porsi TERKECIL (paling perlu didorong) ke terbesar.
    """
    cols = ["Cabang", "Total Belanja Aksesoris", f"Belanja ke {supplier_key}", "Porsi ke " + supplier_key + " (%)"]
    if df.empty:
        return pd.DataFrame(columns=cols)

    total_per_cabang = df.groupby("CABANG")["Total Harga"].sum()
    supplier_per_cabang = df[df["PEMASOK_NORM"] == supplier_key].groupby("CABANG")["Total Harga"].sum()

    g = pd.DataFrame({
        "Total Belanja Aksesoris": total_per_cabang,
        f"Belanja ke {supplier_key}": supplier_per_cabang,
    }).fillna(0).reset_index().rename(columns={"CABANG": "Cabang"})

    g[f"Porsi ke {supplier_key} (%)"] = np.where(
        g["Total Belanja Aksesoris"] != 0,
        g[f"Belanja ke {supplier_key}"] / g["Total Belanja Aksesoris"] * 100,
        0,
    )
    g = g.sort_values(f"Porsi ke {supplier_key} (%)", ascending=True).reset_index(drop=True)
    g.index = g.index + 1
    return g[["Cabang", "Total Belanja Aksesoris", f"Belanja ke {supplier_key}", f"Porsi ke {supplier_key} (%)"]]


def kandidat_kebocoran(df: pd.DataFrame, supplier_key: str = "LUNA") -> pd.DataFrame:
    """Baris pembelian BUKAN dari pemasok target, padahal nama barang yang sama
    pernah dibeli dari pemasok target di cabang/waktu lain.

    Ini sinyal awal (bukan bukti pelanggaran) untuk ditelusuri: bisa jadi memang
    sedang tidak tersedia di pemasok target saat itu, sesuai aturan "boleh beli
    di pemasok lain kalau produknya tidak ada di pemasok target".
    """
    cols = ["Cabang", "Tanggal", "Nama Barang", "Pemasok", "Total Harga"]
    barang_di_supplier = set(df[df["PEMASOK_NORM"] == supplier_key]["NAMA_BARANG_NORM"].unique())
    if not barang_di_supplier:
        return pd.DataFrame(columns=cols)

    non_supplier = df[df["PEMASOK_NORM"] != supplier_key].copy()
    kandidat = non_supplier[non_supplier["NAMA_BARANG_NORM"].isin(barang_di_supplier)]
    if kandidat.empty:
        return pd.DataFrame(columns=cols)

    kandidat = kandidat.sort_values("Total Harga", ascending=False)
    out = kandidat[["CABANG", "Tanggal", "Nama Barang", "Pemasok", "Total Harga"]].rename(
        columns={"CABANG": "Cabang"}
    )
    out["Tanggal"] = out["Tanggal"].dt.strftime("%Y-%m-%d")
    return out.reset_index(drop=True)


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
