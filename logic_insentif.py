"""
Simulasi Take Home Pay (THP) Sales Retail — mengacu ke berkas resmi
"Rules_Insentif_Sales_Retail.xlsx" (kategori "SALES RETAIL" dengan gaji
pokok, dan "RETAIL — Teknisi/Magang/Affiliate/Sales Non Gaji"), DITAMBAH
2 aturan tambahan yang dikonfirmasi terpisah oleh pengguna (belum ada di
berkas resminya):
  1. Laptop dengan harga satuan (@HARGA) > Rp 15.000.000 per unit dapat
     bonus flat Rp 350.000/unit — DIKECUALIKAN dari OMSET yang dipakai
     untuk tabel tier Bonus reguler (sama seperti aturan "Laptop Gaming"
     di berkas, tapi berbasis HARGA, bukan nama produk).
  2. Handphone: bonus dasar Rp 40.000/unit (sesuai berkas). Kalau total
     unit Handphone terjual dalam periode > 5 unit, SELURUH unit (bukan
     cuma kelebihannya) dapat Rp 40.000 + Rp 50.000 = Rp 90.000/unit —
     asumsi yang dikonfirmasi pengguna secara eksplisit (aturan bertingkat
     retroaktif ke seluruh volume, bukan cuma unit ke-6 dst). Kategori
     BARANG "HANDPHONE" dan "HP" digabung (keduanya sama-sama produk
     handphone, cuma variasi penulisan di data sumber).

OMSET yang dipakai untuk tabel tier Bonus reguler = Laptop (harga <= 15jt)
+ Aksesoris + Smartboard — SESUAI catatan di berkas: "Insentif : LAPTOP,
AKSESORIS, SMARTBOARD (BONUS HP 40rb, Laptop Gaming Diatur terpisah
Rp 350rb)". Kategori "SMARTBOARD" dicari dari NAMA BARANG (tidak ada
sebagai KATEGORI BARANG tersendiri di data sumber saat ini).

Kategori "CORP" di berkas SENGAJA TIDAK dipakai (dikonfirmasi pengguna).

⚠️ ASUMSI PENTING yang belum eksplisit di berkas, perlu dikonfirmasi kalau
keliru:
- **Lookup tier pakai FLOOR** (bracket TERTINGGI yang SUDAH TERCAPAI, bukan
  interpolasi maupun pembulatan ke atas) — mis. OMSET Rp 180 juta pakai
  bracket Rp 150 juta (8,5%), BUKAN bracket Rp 200 juta.
- **OMSET di bawah bracket terendah (Rp 25 juta) mendapat Bonus tier = 0**
  (belum ada bracket "di bawah 25 juta" di berkas).
- Kolom "THP" pada tabel "RETAIL Non Gaji" di berkas asli punya nilai aneh
  (mis. "43500000.145") — ini kelihatannya artefak formula Excel yang
  salah (kemungkinan menempelkan kolom % ke digit belakang koma), BUKAN
  angka sungguhan. THP di modul ini DIHITUNG ULANG dari definisi yang
  benar (Bonus saja, karena kategori ini tanpa gaji), bukan disalin
  mentah dari berkas.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

GAJI_POKOK_SALES_RETAIL = 2_600_000
BATAS_HARGA_LAPTOP_MAHAL = 15_000_000
BONUS_LAPTOP_MAHAL_PER_UNIT = 350_000
BONUS_HP_DASAR_PER_UNIT = 40_000
BATAS_UNIT_HP_BONUS_TAMBAHAN = 5
BONUS_HP_TAMBAHAN_PER_UNIT = 50_000  # ditambahkan ke bonus dasar -> jadi 90rb/unit kalau ambang terlampaui

# Tabel tier "SALES RETAIL" (dengan gaji pokok) — (OMSET minimum, % Bonus)
# diurutkan dari TERTINGGI ke TERENDAH supaya floor-lookup gampang (baris
# pertama yang OMSET_minimum <= omset_aktual adalah tier yang dipakai).
TIER_SALES_RETAIL = [
    (300_000_000, 0.11),
    (250_000_000, 0.11),
    (200_000_000, 0.105),
    (150_000_000, 0.085),
    (100_000_000, 0.08),
    (75_000_000, 0.075),
    (50_000_000, 0.07),
    (25_000_000, 0.05),
]

# Tabel tier "RETAIL Non Gaji" (Teknisi/Magang/Affiliate/Sales Non Gaji)
TIER_RETAIL_NON_GAJI = [
    (300_000_000, 0.145),
    (250_000_000, 0.145),
    (200_000_000, 0.14),
    (150_000_000, 0.135),
    (100_000_000, 0.13),
    (75_000_000, 0.125),
    (50_000_000, 0.12),
    (25_000_000, 0.11),
]


def cari_pct_bonus_tier(omset: float, tabel_tier: list[tuple[float, float]]) -> float:
    """Floor-lookup: cari % Bonus dari bracket OMSET TERTINGGI yang SUDAH
    TERCAPAI (omset_minimum_bracket <= omset). Kalau omset di bawah
    bracket terendah di tabel, return 0 (belum capai bracket manapun)."""
    for omset_minimum, pct in tabel_tier:
        if omset >= omset_minimum:
            return pct
    return 0.0


def _kategorikan_baris(kategori_barang: str, nama_barang: str, harga_satuan: float) -> str:
    """Klasifikasi satu baris transaksi ke salah satu dari 4 kelompok
    insentif: 'laptop_mahal', 'handphone', 'omset_tier' (Laptop reguler +
    Aksesoris + Smartboard), atau 'lainnya' (Jasa, Sparepart, dll — tidak
    masuk perhitungan Bonus sama sekali, tapi tetap dihitung di Total
    Omzet keseluruhan & rata-rata GP%)."""
    kat = str(kategori_barang).strip().upper()
    nama = str(nama_barang).strip().upper()
    if kat == "LAPTOP":
        return "laptop_mahal" if harga_satuan > BATAS_HARGA_LAPTOP_MAHAL else "omset_tier"
    if kat in ("HANDPHONE", "HP"):
        return "handphone"
    if kat == "AKSESORIS" or "SMARTBOARD" in nama:
        return "omset_tier"
    return "lainnya"


def simulasi_gaji_sales(
    df: pd.DataFrame,
    tanggal_mulai,
    tanggal_selesai,
    dengan_gaji: bool = True,
) -> pd.DataFrame:
    """Simulasi THP per (Cabang, Sales) untuk satu periode — Gaji Pokok +
    Bonus (tier LAPTOP+AKSESORIS+SMARTBOARD, bonus Laptop Mahal >15jt,
    bonus Handphone). Baris tanpa nama sales (YANG MENYERAHKAN/MENJUAL
    kosong) DIKECUALIKAN — bukan orang yang bisa disimulasikan gajinya.

    `dengan_gaji=True` -> kategori "SALES RETAIL" (Gaji Pokok Rp 2.600.000
    + tabel tier `TIER_SALES_RETAIL`). `dengan_gaji=False` -> kategori
    "RETAIL Non Gaji" (Gaji Pokok Rp 0 + tabel tier
    `TIER_RETAIL_NON_GAJI`, % lebih tinggi sebagai kompensasi).

    Kolom hasil: Cabang, Nama Sales, Omzet Laptop, Qty Laptop, Omzet
    Handphone, Qty Handphone, Omzet Aksesoris, Qty Aksesoris, Omzet
    Lainnya, Total Omzet, Rata-rata GP (%), Gaji Pokok, Bonus Tier,
    Bonus Laptop Mahal, Bonus Handphone, Total Bonus, THP."""
    cols = [
        "Cabang", "Nama Sales", "Omzet Laptop", "Qty Laptop", "Omzet Handphone", "Qty Handphone",
        "Omzet Aksesoris", "Qty Aksesoris", "Omzet Lainnya", "Total Omzet", "Rata-rata GP (%)",
        "Gaji Pokok", "Bonus Tier", "Bonus Laptop Mahal", "Bonus Handphone", "Total Bonus", "THP",
    ]
    if df.empty:
        return pd.DataFrame(columns=cols)

    tanggal_mulai = pd.Timestamp(tanggal_mulai)
    tanggal_selesai = pd.Timestamp(tanggal_selesai)
    d = df[(df["TGL FAKTUR"] >= tanggal_mulai) & (df["TGL FAKTUR"] <= tanggal_selesai)].copy()
    d = d[d["YANG MENYERAHKAN/MENJUAL"].notna() & (d["YANG MENYERAHKAN/MENJUAL"].astype(str).str.strip() != "")]
    if d.empty:
        return pd.DataFrame(columns=cols)

    d["_kelompok"] = [
        _kategorikan_baris(kat, nama, harga)
        for kat, nama, harga in zip(d["KATEGORI BARANG"], d["NAMA BARANG"], d["@HARGA"])
    ]
    # "Laptop" yang ditampilkan di breakdown = laptop reguler + laptop
    # mahal digabung (supaya total Omzet Laptop di tabel tetap utuh
    # mencerminkan SELURUH penjualan laptop, bukan cuma yang masuk tier).
    d["_kelompok_tampilan"] = np.where(
        d["_kelompok"] == "laptop_mahal", "Laptop",
        np.where(
            d["_kelompok"] == "handphone", "Handphone",
            np.where(d["_kelompok"] == "omset_tier",
                     np.where(d["KATEGORI BARANG"].astype(str).str.strip().str.upper() == "LAPTOP", "Laptop", "Aksesoris"),
                     "Lainnya"),
        ),
    )

    tabel_tier = TIER_SALES_RETAIL if dengan_gaji else TIER_RETAIL_NON_GAJI
    gaji_pokok_flat = GAJI_POKOK_SALES_RETAIL if dengan_gaji else 0

    rows = []
    for (cabang, sales), grp in d.groupby(["CABANG", "YANG MENYERAHKAN/MENJUAL"]):
        omzet_per_kelompok = grp.groupby("_kelompok_tampilan")["TOTAL HARGA"].sum()
        qty_per_kelompok = grp.groupby("_kelompok_tampilan")["QTY"].sum()

        omzet_laptop = float(omzet_per_kelompok.get("Laptop", 0))
        qty_laptop = float(qty_per_kelompok.get("Laptop", 0))
        omzet_handphone = float(omzet_per_kelompok.get("Handphone", 0))
        qty_handphone = float(qty_per_kelompok.get("Handphone", 0))
        omzet_aksesoris = float(omzet_per_kelompok.get("Aksesoris", 0))
        qty_aksesoris = float(qty_per_kelompok.get("Aksesoris", 0))
        omzet_lainnya = float(omzet_per_kelompok.get("Lainnya", 0))
        total_omzet = omzet_laptop + omzet_handphone + omzet_aksesoris + omzet_lainnya

        total_laba = float(grp["LABA"].sum())
        rata2_gp = (total_laba / total_omzet * 100) if total_omzet else 0

        omzet_tier = float(grp[grp["_kelompok"] == "omset_tier"]["TOTAL HARGA"].sum())
        pct_bonus = cari_pct_bonus_tier(omzet_tier, tabel_tier)
        bonus_tier = omzet_tier * pct_bonus

        qty_laptop_mahal = float(grp[grp["_kelompok"] == "laptop_mahal"]["QTY"].sum())
        bonus_laptop_mahal = qty_laptop_mahal * BONUS_LAPTOP_MAHAL_PER_UNIT

        qty_hp = float(grp[grp["_kelompok"] == "handphone"]["QTY"].sum())
        tarif_hp = (
            BONUS_HP_DASAR_PER_UNIT + BONUS_HP_TAMBAHAN_PER_UNIT
            if qty_hp > BATAS_UNIT_HP_BONUS_TAMBAHAN else BONUS_HP_DASAR_PER_UNIT
        )
        bonus_handphone = qty_hp * tarif_hp

        total_bonus = bonus_tier + bonus_laptop_mahal + bonus_handphone
        thp = gaji_pokok_flat + total_bonus

        rows.append({
            "Cabang": cabang, "Nama Sales": sales,
            "Omzet Laptop": omzet_laptop, "Qty Laptop": qty_laptop,
            "Omzet Handphone": omzet_handphone, "Qty Handphone": qty_handphone,
            "Omzet Aksesoris": omzet_aksesoris, "Qty Aksesoris": qty_aksesoris,
            "Omzet Lainnya": omzet_lainnya, "Total Omzet": total_omzet,
            "Rata-rata GP (%)": rata2_gp, "Gaji Pokok": gaji_pokok_flat,
            "Bonus Tier": bonus_tier, "Bonus Laptop Mahal": bonus_laptop_mahal,
            "Bonus Handphone": bonus_handphone, "Total Bonus": total_bonus, "THP": thp,
        })

    out = pd.DataFrame(rows, columns=cols)
    return out.sort_values("THP", ascending=False).reset_index(drop=True)


def format_rupiah_id(x) -> str:
    try:
        x = int(round(float(x)))
    except (ValueError, TypeError):
        return str(x)
    return f"Rp {x:,.0f}".replace(",", ".")


def format_int_id(x) -> str:
    try:
        x = int(round(float(x)))
    except (ValueError, TypeError):
        return str(x)
    return f"{x:,.0f}".replace(",", ".")


def format_percent_id(x, decimals: int = 1) -> str:
    try:
        x = float(x)
    except (ValueError, TypeError):
        return str(x)
    s = f"{x:,.{decimals}f}"
    s = s.replace(",", "#").replace(".", ",").replace("#", ".")
    return s + "%"
