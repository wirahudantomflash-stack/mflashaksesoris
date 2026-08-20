import streamlit as st
import pandas as pd

from logic import (
    read_raw, finalize_data, apply_filters,
    top_cabang, top_produk, top_sales_retail,
    format_rupiah_id, format_percent_id, format_int_id,
    MissingCabangColumn,
)

st.set_page_config(page_title="MFLASH — Top Performers", page_icon="🏆", layout="wide")

st.title("🏆 MFLASH — Top Cabang / Produk / Sales")
st.caption("Madinah Group Indonesia · 18 cabang service gadget")

# ---------------------------------------------------------------------------
# 1. Muat data
# ---------------------------------------------------------------------------
st.sidebar.header("Sumber data")

DEFAULT_PATH = "penjualan.csv.gz"
uploaded = st.sidebar.file_uploader(
    "Unggah penjualan.csv.gz — bisa data seluruh cabang, atau rincian satu cabang saja",
    type=["gz", "csv"],
    help=(
        "Boleh berkas gabungan seluruh cabang (ada kolom CABANG), atau berkas "
        "rincian satu cabang saja (tanpa kolom CABANG) — kalau tidak ada kolom "
        "CABANG, Anda akan diminta mengisi nama cabangnya di bawah ini."
    ),
)

raw_df = None
error_msg = None

try:
    if uploaded is not None:
        raw_df = read_raw(uploaded)
    else:
        import os
        if os.path.exists(DEFAULT_PATH):
            raw_df = read_raw(DEFAULT_PATH)
except Exception as e:
    error_msg = str(e)

if error_msg:
    st.error(f"Gagal membaca berkas: {error_msg}")
    st.stop()

if raw_df is None:
    st.info(
        "Belum ada data. Unggah **penjualan.csv.gz** (atau berkas rincian satu "
        "cabang) lewat panel di sebelah kiri, atau taruh berkas tersebut di root "
        "repo (sejajar dengan app.py) sebelum deploy."
    )
    st.stop()

# Kalau berkas tidak punya kolom CABANG (berkas rincian satu cabang), minta
# nama cabangnya dulu sebelum data difinalisasi.
df = None
if "CABANG" in raw_df.columns:
    df = finalize_data(raw_df)
else:
    st.sidebar.warning("Berkas ini tidak punya kolom CABANG — sepertinya rincian satu cabang saja.")
    nama_cabang = st.sidebar.text_input(
        "Nama cabang untuk berkas ini",
        placeholder="contoh: MFLASH TELUK JAMBE",
    )
    if not nama_cabang:
        st.info("Masukkan nama cabang di panel kiri untuk melanjutkan.")
        st.stop()
    df = finalize_data(raw_df, cabang_default=nama_cabang.strip())

st.sidebar.success(f"Data termuat: {len(df):,}".replace(",", ".") + " baris")

# ---------------------------------------------------------------------------
# 2. Filter
# ---------------------------------------------------------------------------
st.sidebar.header("Filter")

tahun_opsi = sorted([int(t) for t in df["TAHUN"].dropna().unique()])
bulan_nama = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}
bulan_opsi = sorted([int(b) for b in df["BULAN"].dropna().unique()])
cabang_opsi = sorted(df["CABANG"].dropna().unique().tolist())

sel_tahun = st.sidebar.multiselect("Tahun", tahun_opsi, default=tahun_opsi)
sel_bulan = st.sidebar.multiselect(
    "Bulan", bulan_opsi, default=bulan_opsi,
    format_func=lambda b: bulan_nama.get(b, str(b)),
)
sel_cabang = st.sidebar.multiselect("Cabang", cabang_opsi, default=cabang_opsi)

dff = apply_filters(
    df,
    tahun=sel_tahun if sel_tahun else None,
    bulan=sel_bulan if sel_bulan else None,
    cabang=sel_cabang if sel_cabang else None,
)

if dff.empty:
    st.warning(
        "Tidak ada data untuk kombinasi filter ini. "
        "Coba longgarkan pilihan tahun, bulan, atau cabang di sebelah kiri."
    )
    st.stop()

st.caption(
    f"Menampilkan {len(dff):,}".replace(",", ".") + f" baris · "
    f"{dff['NOTA_ID'].nunique():,}".replace(",", ".") + " nota unik (cabang + no faktur)"
)

st.divider()

# ---------------------------------------------------------------------------
# 3. Top 3 Cabang
# ---------------------------------------------------------------------------
st.header("Top 3 Cabang")

c1, c2 = st.columns([1, 3])
with c1:
    metrik_cabang = st.radio(
        "Urutkan berdasarkan", ["Omzet", "Laba", "Jumlah Nota"],
        key="metrik_cabang",
    )

tc = top_cabang(dff, metric=metrik_cabang, n=3)

with c2:
    if tc.empty:
        st.info("Tidak ada data cabang pada filter ini.")
    else:
        cols = st.columns(len(tc))
        medali = ["🥇", "🥈", "🥉"]
        for i, (col, (_, row)) in enumerate(zip(cols, tc.iterrows())):
            with col:
                st.metric(
                    f"{medali[i]} {row['CABANG']}",
                    format_rupiah_id(row["Omzet"]),
                    f"Laba {format_rupiah_id(row['Laba'])}",
                )
                st.caption(
                    f"Margin {format_percent_id(row['Margin (%)'])} · "
                    f"{format_int_id(row['Jumlah Nota'])} nota"
                )

if not tc.empty:
    tampil = tc.copy()
    for col in ["Omzet", "Modal", "Laba"]:
        tampil[col] = tampil[col].map(format_rupiah_id)
    tampil["Margin (%)"] = tc["Margin (%)"].map(format_percent_id)
    tampil["Jumlah Nota"] = tc["Jumlah Nota"].map(format_int_id)
    st.dataframe(tampil, use_container_width=True)
    st.download_button(
        "⬇️ Unduh CSV — Top Cabang",
        tc.to_csv(index=True).encode("utf-8-sig"),
        "top_cabang.csv", "text/csv",
        key="dl_cabang",
    )

st.divider()

# ---------------------------------------------------------------------------
# 4. Top 10 Produk Terlaris
# ---------------------------------------------------------------------------
st.header("Top 10 Produk Terlaris")

metrik_produk = st.radio(
    "Urutkan berdasarkan", ["Qty Terjual", "Omzet"],
    key="metrik_produk", horizontal=True,
)

tp = top_produk(dff, metric=metrik_produk, n=10)

if tp.empty:
    st.info("Tidak ada data produk pada filter ini.")
else:
    tampil = tp.copy()
    tampil["Qty Terjual"] = tp["Qty Terjual"].map(format_int_id)
    tampil["Omzet"] = tp["Omzet"].map(format_rupiah_id)
    tampil["Laba"] = tp["Laba"].map(format_rupiah_id)
    st.dataframe(tampil, use_container_width=True)
    st.download_button(
        "⬇️ Unduh CSV — Top Produk",
        tp.to_csv(index=True).encode("utf-8-sig"),
        "top_produk.csv", "text/csv",
        key="dl_produk",
    )

st.divider()

# ---------------------------------------------------------------------------
# 5. Top 5 Sales Retail
# ---------------------------------------------------------------------------
st.header("Top 5 Sales Retail")

kategori_penjualan_opsi = sorted(dff["KATEGORI PENJUALAN"].dropna().unique().tolist())
default_retail = [k for k in kategori_penjualan_opsi if "RETAIL" in str(k).upper()] or kategori_penjualan_opsi

c1, c2 = st.columns([2, 1])
with c1:
    sel_kategori_retail = st.multiselect(
        "Kategori penjualan yang dianggap \"retail\"",
        kategori_penjualan_opsi, default=default_retail,
        help="Sesuaikan kalau nilai kolom KATEGORI PENJUALAN di data Anda berbeda dari dugaan otomatis ini.",
    )
with c2:
    metrik_sales = st.radio(
        "Urutkan berdasarkan", ["Omzet", "Laba", "Jumlah Nota"],
        key="metrik_sales",
    )

if not sel_kategori_retail:
    st.info("Pilih minimal satu kategori penjualan untuk dianggap sebagai retail.")
else:
    ts = top_sales_retail(dff, sel_kategori_retail, metric=metrik_sales, n=5)
    if ts.empty:
        st.info("Tidak ada transaksi retail pada filter ini.")
    else:
        tampil = ts.copy()
        tampil["Omzet"] = ts["Omzet"].map(format_rupiah_id)
        tampil["Laba"] = ts["Laba"].map(format_rupiah_id)
        tampil["Jumlah Nota"] = ts["Jumlah Nota"].map(format_int_id)
        st.dataframe(tampil, use_container_width=True)
        st.download_button(
            "⬇️ Unduh CSV — Top Sales Retail",
            ts.to_csv(index=True).encode("utf-8-sig"),
            "top_sales_retail.csv", "text/csv",
            key="dl_sales",
        )

st.divider()
st.caption(
    "Aturan data: satu nota = CABANG + NO FAKTUR · HARGA BELI sudah total per baris "
    "(tidak dikalikan QTY) · baris kembar dihitung apa adanya · AKSESORIS dan "
    "ACCESORIES digabung jadi satu kategori."
)
