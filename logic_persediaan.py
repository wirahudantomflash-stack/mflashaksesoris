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
3. Ambang batas default (bisa diubah dari dashboard):
   - 🔴 Merah  : stok ≤ 2  (termasuk 0 dan anomali negatif — kritis, perlu
                 restock segera)
   - 🟡 Kuning : stok 3–7  (menipis, perlu diawasi)
   - 🟢 Hijau  : stok ≥ 8  (aman)
   Ambang ini diturunkan dari sebaran stok LUNA riil di data (median 3,
   kuartil-3 sekitar 10) — bukan angka sembarang, tapi tetap best-effort
   karena sumber data tidak punya kolom "par level" / target stok resmi.

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


def apply_filters(df: pd.DataFrame, cabang=None, hanya_aksesoris: bool = True, hanya_luna: bool = True) -> pd.DataFrame:
    out = df
    if hanya_aksesoris:
        out = out[out["KATEGORI_NORM"] == "AKSESORIS"]
    if hanya_luna:
        out = out[out["ADALAH_LUNA"]]
    if cabang:
        out = out[out["Cabang"].isin(cabang)]
    return out


def klasifikasi_stok(qty: float, batas_merah: float = 2, batas_kuning: float = 7) -> str:
    if qty <= batas_merah:
        return MERAH
    if qty <= batas_kuning:
        return KUNING
    return HIJAU


def indikator_stok_luna(df: pd.DataFrame, batas_merah: float = 2, batas_kuning: float = 7) -> pd.DataFrame:
    """Indikator stok per (Cabang, Nama Barang) untuk item LUNA.

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
