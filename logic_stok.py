"""
Logika inti — Dashboard Stok Semua Cabang, dengan fokus buffer stok LUNA
(MFLASH, 18 cabang).

Sumber data: sheet "Daftar Barang dan Jasa" pada berkas Persediaan Aksesoris
Regional, atau CSV dengan skema kolom yang sama.

Cara kerja status buffer stok LUNA:
1. Filter ke barang yang namanya mengandung "LUNA" (brand tertanam di
   `Nama Barang`, karena berkas ini tidak punya kolom Pemasok terpisah).
2. Untuk tiap produk, ambil **stok tertinggi yang pernah tercatat di
   cabang manapun** sebagai baseline "stok penuh" — karena tidak ada kolom
   par-level/target stok resmi di sumber data.
3. Persen stok cabang = stok cabang ÷ baseline produk itu × 100.
4. Status: Merah (<20%), Kuning (20%–<90%), Hijau (≥90%) — ambang bisa
   diubah lewat parameter fungsi.

Keterbatasan yang perlu diketahui pengguna: baseline ini relatif antar
cabang (bukan target stok resmi dari manajemen), dan produk yang cuma
tercatat di satu cabang otomatis 100% (Hijau) karena tidak ada pembanding —
ditampilkan apa adanya, bukan disembunyikan.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Cabang", "Kategori Barang", "Kode Barang", "Nama Barang",
    "Kts (Semua Gdng)", "Nilai Satuan", "Nilai Total",
]

SHEET_NAME = "Daftar Barang dan Jasa"


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
    df["Kts (Semua Gdng)"] = pd.to_numeric(df["Kts (Semua Gdng)"], errors="coerce").fillna(0)
    df["Nilai Satuan"] = pd.to_numeric(df["Nilai Satuan"], errors="coerce").fillna(0)
    df["Nilai Total"] = pd.to_numeric(df["Nilai Total"], errors="coerce").fillna(0)

    kat = df["Kategori Barang"].astype(str).str.strip().str.upper()
    kat = kat.replace({"ACCESORIES": "AKSESORIS", "ACCESSORIES": "AKSESORIS"})
    df["KATEGORI_NORM"] = kat

    df["ADALAH_LUNA"] = df["Nama Barang"].str.upper().str.contains("LUNA", na=False)

    return df


def apply_filters(df: pd.DataFrame, cabang=None, hanya_aksesoris: bool = True) -> pd.DataFrame:
    out = df
    if hanya_aksesoris:
        out = out[out["KATEGORI_NORM"] == "AKSESORIS"]
    if cabang:
        out = out[out["Cabang"].isin(cabang)]
    return out


def status_stok_luna(
    df: pd.DataFrame,
    ambang_merah: float = 20.0,
    ambang_hijau: float = 90.0,
) -> pd.DataFrame:
    """Status buffer stok LUNA per (Cabang, Nama Barang).

    Kolom hasil: Cabang, Nama Barang, Stok Saat Ini, Stok Tertinggi Antar
    Cabang (baseline), Persen Stok (%), Status.
    """
    cols = ["Cabang", "Nama Barang", "Stok Saat Ini", "Stok Tertinggi Antar Cabang", "Persen Stok (%)", "Status"]
    luna = df[df["ADALAH_LUNA"]]
    if luna.empty:
        return pd.DataFrame(columns=cols)

    agg = luna.groupby(["Cabang", "Nama Barang"])["Kts (Semua Gdng)"].sum().reset_index()
    agg = agg.rename(columns={"Kts (Semua Gdng)": "Stok Saat Ini"})

    # Beberapa baris di sumber data punya stok negatif (anomali sistem —
    # biasanya transaksi keluar tercatat sebelum stok masuk). Untuk keperluan
    # status buffer, stok negatif diperlakukan sebagai 0 (kosong), bukan
    # dibiarkan menghasilkan persentase negatif yang membingungkan.
    agg["Stok Saat Ini"] = agg["Stok Saat Ini"].clip(lower=0)

    baseline = agg.groupby("Nama Barang")["Stok Saat Ini"].max().rename("Stok Tertinggi Antar Cabang")
    agg = agg.join(baseline, on="Nama Barang")

    agg["Persen Stok (%)"] = np.where(
        agg["Stok Tertinggi Antar Cabang"] > 0,
        agg["Stok Saat Ini"] / agg["Stok Tertinggi Antar Cabang"] * 100,
        0,
    )

    def klasifikasi(p: float) -> str:
        if p < ambang_merah:
            return "🔴 Merah"
        if p < ambang_hijau:
            return "🟡 Kuning"
        return "🟢 Hijau"

    agg["Status"] = agg["Persen Stok (%)"].apply(klasifikasi)
    agg = agg.sort_values(["Persen Stok (%)", "Cabang"]).reset_index(drop=True)
    return agg[cols]


def ringkasan_status_cabang(status_df: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan per cabang: jumlah produk LUNA di tiap status, dan porsi Merah
    (cabang dengan porsi Merah tertinggi = paling perlu segera dibuffer)."""
    cols = ["Cabang", "Jumlah Produk LUNA", "Merah", "Kuning", "Hijau", "Porsi Merah (%)"]
    if status_df.empty:
        return pd.DataFrame(columns=cols)

    piv = status_df.pivot_table(index="Cabang", columns="Status", values="Nama Barang", aggfunc="count", fill_value=0)
    for col in ["🔴 Merah", "🟡 Kuning", "🟢 Hijau"]:
        if col not in piv.columns:
            piv[col] = 0
    piv = piv.rename(columns={"🔴 Merah": "Merah", "🟡 Kuning": "Kuning", "🟢 Hijau": "Hijau"})
    piv["Jumlah Produk LUNA"] = piv["Merah"] + piv["Kuning"] + piv["Hijau"]
    piv["Porsi Merah (%)"] = np.where(piv["Jumlah Produk LUNA"] > 0, piv["Merah"] / piv["Jumlah Produk LUNA"] * 100, 0)
    piv = piv.reset_index().sort_values("Porsi Merah (%)", ascending=False).reset_index(drop=True)
    return piv[cols]


def nilai_stok_cabang(df: pd.DataFrame) -> pd.DataFrame:
    """Nilai total persediaan aksesoris (semua brand) per cabang, sebagai
    konteks tambahan di luar fokus LUNA."""
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
