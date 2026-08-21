import os
import streamlit as st
import pandas as pd

import logic_stok as ls
import logic_penjualan as ljl
import logic_aksesoris as la

st.set_page_config(page_title="MFLASH — Dashboard Cabang", page_icon="🏬", layout="wide")

st.title("🏬 MFLASH — Dashboard Cabang")
st.caption("Madinah Group Indonesia · 18 cabang service gadget")

BULAN_NAMA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}

# ---------------------------------------------------------------------------
# Sidebar — sumber data untuk KEDUA dashboard, supaya bisa dimuat sekali dan
# tab tinggal berpindah tanpa perlu unggah ulang.
# ---------------------------------------------------------------------------
st.sidebar.header("📊 Data Persediaan/Stok")
st.sidebar.caption("Sheet \"Daftar Barang dan Jasa\" — Excel atau CSV sepadan")
upl_stok = st.sidebar.file_uploader(
    "Unggah berkas persediaan", type=["xlsx", "xls", "csv"], key="upl_stok",
)

st.sidebar.divider()

st.sidebar.header("🧾 Data Penjualan")
st.sidebar.caption("Gabungan seluruh cabang, atau rincian satu cabang saja")
upl_penjualan = st.sidebar.file_uploader(
    "Unggah berkas penjualan", type=["gz", "csv", "xlsx", "xls"], key="upl_penjualan",
)

st.sidebar.divider()

st.sidebar.header("💰 Data Penjualan Aksesoris")
st.sidebar.caption("Sheet \"Rincian Faktur Penjualan\" (khusus aksesoris) — Excel atau CSV sepadan")
upl_aksesoris = st.sidebar.file_uploader(
    "Unggah berkas penjualan aksesoris", type=["xlsx", "xls", "csv"], key="upl_aksesoris",
)

st.sidebar.divider()
st.sidebar.header("🚦 Ambang Status Stok LUNA")
ambang_merah = st.sidebar.slider("Batas Merah (di bawah ini)", 0, 100, 20, key="ambang_merah")
ambang_hijau = st.sidebar.slider("Batas Hijau (di atas/sama dengan ini)", 0, 100, 90, key="ambang_hijau")
if ambang_merah >= ambang_hijau:
    st.sidebar.warning("Batas Merah harus lebih kecil dari batas Hijau.")

# ---------------------------------------------------------------------------
# Muat data (dua sumber independen)
# ---------------------------------------------------------------------------
DEFAULT_STOK_PATH = "Persediaan_Aksesoris_Regional.xlsx"
DEFAULT_PENJUALAN_PATH = "penjualan.csv.gz"

df_stok, err_stok = None, None
try:
    if upl_stok is not None:
        df_stok = ls.load_persediaan(upl_stok)
    elif os.path.exists(DEFAULT_STOK_PATH):
        df_stok = ls.load_persediaan(DEFAULT_STOK_PATH)
except Exception as e:
    err_stok = str(e)

df_penjualan, err_penjualan, need_cabang_name = None, None, False
raw_penjualan = None
try:
    if upl_penjualan is not None:
        raw_penjualan = ljl.read_raw(upl_penjualan)
    elif os.path.exists(DEFAULT_PENJUALAN_PATH):
        raw_penjualan = ljl.read_raw(DEFAULT_PENJUALAN_PATH)
except Exception as e:
    err_penjualan = str(e)

if raw_penjualan is not None:
    if "CABANG" in raw_penjualan.columns:
        df_penjualan = ljl.finalize_data(raw_penjualan)
    else:
        need_cabang_name = True

DEFAULT_AKSESORIS_PATH = "Penjualan_Aksesoris_Regional_MFlash.csv"
df_aksesoris, err_aksesoris = None, None
try:
    if upl_aksesoris is not None:
        df_aksesoris = la.load_aksesoris(upl_aksesoris)
    elif os.path.exists(DEFAULT_AKSESORIS_PATH):
        df_aksesoris = la.load_aksesoris(DEFAULT_AKSESORIS_PATH)
except Exception as e:
    err_aksesoris = str(e)


# ---------------------------------------------------------------------------
# TAB 1 — Dashboard Stok Semua Cabang (fokus buffer stok LUNA)
# ---------------------------------------------------------------------------
def render_stok_tab():
    if err_stok:
        st.error(f"Gagal membaca berkas persediaan: {err_stok}")
        return
    if df_stok is None:
        st.info(
            "Belum ada data. Unggah berkas Excel/CSV **Persediaan Aksesoris Regional** "
            "(sheet **Daftar Barang dan Jasa**) lewat panel kiri, atau taruh berkasnya "
            "di root repo sebelum deploy."
        )
        return

    if ambang_merah >= ambang_hijau:
        st.error("Batas Merah harus lebih kecil dari batas Hijau — perbaiki dulu di panel kiri.")
        return

    st.subheader("Filter — Data Persediaan")
    cabang_opsi = sorted(df_stok["Cabang"].dropna().unique().tolist())
    sel_cabang = st.multiselect("Cabang", cabang_opsi, default=cabang_opsi, key="st_cabang")

    dff = ls.apply_filters(df_stok, cabang=sel_cabang if sel_cabang else None, hanya_aksesoris=True)

    if dff.empty:
        st.warning("Tidak ada data untuk kombinasi filter ini. Coba longgarkan pilihan cabang di atas.")
        return

    st.caption(f"Menampilkan {len(dff):,}".replace(",", ".") + " baris persediaan kategori aksesoris.")
    st.divider()

    # -----------------------------------------------------------------
    # Status buffer stok LUNA
    # -----------------------------------------------------------------
    st.header("🚦 Status Buffer Stok LUNA")
    st.caption(
        "Semua cabang wajib menyetok LUNA. Status dihitung dari stok cabang dibanding "
        "**stok tertinggi yang pernah tercatat di cabang manapun** untuk produk yang sama "
        "(karena sumber data tidak punya kolom target stok resmi) — "
        f"🔴 Merah: di bawah {ambang_merah}% · 🟡 Kuning: {ambang_merah}%–{ambang_hijau}% · "
        f"🟢 Hijau: {ambang_hijau}% ke atas."
    )
    st.caption(
        "Catatan: produk yang cuma tercatat di satu cabang otomatis 100% (Hijau) karena "
        "tidak ada pembanding cabang lain — bukan berarti stoknya benar-benar aman. "
        "Stok negatif pada sumber data (anomali sistem) diperlakukan sebagai 0."
    )

    status = ls.status_stok_luna(dff, ambang_merah=ambang_merah, ambang_hijau=ambang_hijau)

    if status.empty:
        st.info("Tidak ditemukan produk LUNA (nama mengandung \"LUNA\") pada filter ini.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        total = len(status)
        n_merah = (status["Status"] == "🔴 Merah").sum()
        n_kuning = (status["Status"] == "🟡 Kuning").sum()
        n_hijau = (status["Status"] == "🟢 Hijau").sum()
        c1.metric("Total Produk × Cabang", ls.format_int_id(total))
        c2.metric("🔴 Merah", ls.format_int_id(n_merah), f"{ls.format_percent_id(n_merah/total*100 if total else 0)}")
        c3.metric("🟡 Kuning", ls.format_int_id(n_kuning), f"{ls.format_percent_id(n_kuning/total*100 if total else 0)}")
        c4.metric("🟢 Hijau", ls.format_int_id(n_hijau), f"{ls.format_percent_id(n_hijau/total*100 if total else 0)}")

        st.subheader("Ringkasan per Cabang")
        st.caption("Diurutkan dari porsi Merah TERTINGGI — cabang paling perlu segera dibuffer ada di paling atas.")
        ring = ls.ringkasan_status_cabang(status)
        st.bar_chart(ring.set_index("Cabang")[["Merah", "Kuning", "Hijau"]])
        tampil_ring = ring.copy()
        tampil_ring["Porsi Merah (%)"] = ring["Porsi Merah (%)"].map(ls.format_percent_id)
        st.dataframe(tampil_ring, use_container_width=True, height=420)
        st.download_button(
            "⬇️ Unduh CSV — Ringkasan Status per Cabang", ring.to_csv(index=False).encode("utf-8-sig"),
            "ringkasan_status_stok_luna.csv", "text/csv", key="st_dl_ringkasan",
        )

        st.subheader("Detail per Produk × Cabang")
        filter_status = st.multiselect(
            "Filter status", ["🔴 Merah", "🟡 Kuning", "🟢 Hijau"],
            default=["🔴 Merah", "🟡 Kuning", "🟢 Hijau"], key="st_filter_status",
        )
        cari_produk = st.text_input("Cari nama produk", key="st_cari_produk")

        detail = status[status["Status"].isin(filter_status)] if filter_status else status.iloc[0:0]
        if cari_produk:
            detail = detail[detail["Nama Barang"].str.upper().str.contains(cari_produk.upper(), na=False)]

        if detail.empty:
            st.info("Tidak ada produk yang cocok dengan filter status/pencarian ini.")
        else:
            tampil_detail = detail.copy()
            tampil_detail["Persen Stok (%)"] = detail["Persen Stok (%)"].map(ls.format_percent_id)
            st.dataframe(tampil_detail, use_container_width=True, height=420)
            st.download_button(
                "⬇️ Unduh CSV — Detail Status Stok LUNA", detail.to_csv(index=False).encode("utf-8-sig"),
                "detail_status_stok_luna.csv", "text/csv", key="st_dl_detail",
            )

    st.divider()

    # -----------------------------------------------------------------
    # Nilai persediaan per cabang (konteks tambahan, semua brand)
    # -----------------------------------------------------------------
    st.header("💼 Nilai Persediaan Aksesoris per Cabang")
    st.caption("Konteks tambahan di luar fokus LUNA — seluruh brand aksesoris yang tercatat di persediaan.")
    nilai = ls.nilai_stok_cabang(dff)
    if nilai.empty:
        st.info("Tidak ada data pada filter ini.")
    else:
        st.bar_chart(nilai.set_index("Cabang")["Nilai Persediaan"])
        tampil_nilai = nilai.copy()
        tampil_nilai["Total Qty"] = nilai["Total Qty"].map(ls.format_int_id)
        tampil_nilai["Jumlah SKU"] = nilai["Jumlah SKU"].map(ls.format_int_id)
        tampil_nilai["Nilai Persediaan"] = nilai["Nilai Persediaan"].map(ls.format_rupiah_id)
        st.dataframe(tampil_nilai, use_container_width=True, height=420)
        st.download_button(
            "⬇️ Unduh CSV — Nilai Persediaan per Cabang", nilai.to_csv(index=False).encode("utf-8-sig"),
            "nilai_persediaan_cabang.csv", "text/csv", key="st_dl_nilai",
        )

    st.divider()

    # -----------------------------------------------------------------
    # Analisa & tindak lanjut
    # -----------------------------------------------------------------
    st.header("📌 Analisa & Tindak Lanjut")
    catatan = []
    if not status.empty:
        ring2 = ls.ringkasan_status_cabang(status)
        if not ring2.empty:
            prioritas = ring2.iloc[0]
            catatan.append(
                f"Cabang **{prioritas['Cabang']}** paling perlu segera dibuffer — "
                f"{ls.format_percent_id(prioritas['Porsi Merah (%)'])} dari produk LUNA-nya berstatus "
                f"🔴 Merah ({int(prioritas['Merah'])} dari {int(prioritas['Jumlah Produk LUNA'])} produk)."
            )
            aman = ring2.sort_values("Porsi Merah (%)").iloc[0]
            catatan.append(
                f"Cabang **{aman['Cabang']}** paling aman stok LUNA-nya — hanya "
                f"{ls.format_percent_id(aman['Porsi Merah (%)'])} produk berstatus Merah."
            )
        n_merah_total = (status["Status"] == "🔴 Merah").sum()
        if n_merah_total > 0:
            catatan.append(
                f"Total ada **{ls.format_int_id(n_merah_total)}** kombinasi produk×cabang berstatus "
                "🔴 Merah di seluruh jaringan — prioritaskan pengiriman ulang/pembelian ke pemasok LUNA "
                "untuk item-item ini dulu (lihat tab Dashboard Penjualan Aksesoris untuk data pembelian historis)."
            )
    else:
        catatan.append("Tidak ada data produk LUNA untuk dianalisa pada filter saat ini.")

    for c in catatan:
        st.markdown("- " + c)


# ---------------------------------------------------------------------------
# TAB 2 — Dashboard Penjualan Cabang
# ---------------------------------------------------------------------------
def render_penjualan_tab():
    if err_penjualan:
        st.error(f"Gagal membaca berkas penjualan: {err_penjualan}")
        return

    if raw_penjualan is None:
        st.info(
            "Belum ada data penjualan. Unggah **penjualan.csv.gz** (gabungan seluruh cabang, "
            "atau rincian satu cabang saja) lewat panel kiri, atau taruh berkasnya di root repo."
        )
        return

    df = df_penjualan
    if need_cabang_name:
        st.warning("Berkas ini tidak punya kolom CABANG — sepertinya rincian satu cabang saja.")
        nama_cabang = st.text_input(
            "Nama cabang untuk berkas ini", placeholder="contoh: MFLASH TELUK JAMBE", key="jl_nama_cabang",
        )
        if not nama_cabang:
            st.info("Masukkan nama cabang di atas untuk melanjutkan.")
            return
        df = ljl.finalize_data(raw_penjualan, cabang_default=nama_cabang.strip())

    if df is None:
        return

    st.markdown("## 🧾 Ringkasan Cabang, Produk & Sales")
    st.subheader("Filter — Data Penjualan")
    tahun_opsi = sorted([int(t) for t in df["TAHUN"].dropna().unique()])
    bulan_opsi = sorted([int(b) for b in df["BULAN"].dropna().unique()])
    cabang_opsi = sorted(df["CABANG"].dropna().unique().tolist())

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_tahun = st.multiselect("Tahun", tahun_opsi, default=tahun_opsi, key="jl_tahun")
    with c2:
        sel_bulan = st.multiselect(
            "Bulan", bulan_opsi, default=bulan_opsi, format_func=lambda b: BULAN_NAMA.get(b, str(b)), key="jl_bulan",
        )
    with c3:
        sel_cabang = st.multiselect("Cabang", cabang_opsi, default=cabang_opsi, key="jl_cabang")

    dff = ljl.apply_filters(
        df,
        tahun=sel_tahun if sel_tahun else None,
        bulan=sel_bulan if sel_bulan else None,
        cabang=sel_cabang if sel_cabang else None,
    )

    if dff.empty:
        st.warning("Tidak ada data untuk kombinasi filter ini. Coba longgarkan pilihan di atas.")
        return

    st.caption(
        f"Menampilkan {len(dff):,}".replace(",", ".") + " baris · "
        f"{dff['NOTA_ID'].nunique():,}".replace(",", ".") + " nota unik (cabang + no faktur)"
    )
    st.divider()

    st.header("Seluruh Cabang")
    metrik_cabang = st.radio("Urutkan berdasarkan", ["Omzet", "Laba", "Jumlah Nota"], key="jl_metrik_cabang", horizontal=True)
    tc = ljl.top_cabang(dff, metric=metrik_cabang, n=None)
    if tc.empty:
        st.info("Tidak ada data cabang pada filter ini.")
    else:
        st.bar_chart(tc.set_index("CABANG")[metrik_cabang])
        tampil = tc.copy()
        for col in ["Omzet", "Modal", "Laba"]:
            tampil[col] = tc[col].map(ljl.format_rupiah_id)
        tampil["Margin (%)"] = tc["Margin (%)"].map(ljl.format_percent_id)
        tampil["Jumlah Nota"] = tc["Jumlah Nota"].map(ljl.format_int_id)
        st.dataframe(tampil, use_container_width=True, height=460)
        st.download_button("⬇️ Unduh CSV — Seluruh Cabang", tc.to_csv(index=True).encode("utf-8-sig"), "seluruh_cabang.csv", "text/csv", key="jl_dl_cabang")

    st.divider()
    st.header("Semua Produk Aksesoris")
    st.caption("Difilter khusus kategori barang AKSESORIS (AKSESORIS/ACCESORIES digabung).")
    metrik_produk = st.radio("Urutkan berdasarkan", ["Qty Terjual", "Omzet"], key="jl_metrik_produk", horizontal=True)
    tp = ljl.top_produk(dff, metric=metrik_produk, n=None, hanya_aksesoris=True)
    if tp.empty:
        st.info("Tidak ada data produk aksesoris pada filter ini.")
    else:
        st.caption(f"{len(tp):,}".replace(",", ".") + " produk aksesoris berbeda.")
        tampil = tp.copy()
        tampil["Qty Terjual"] = tp["Qty Terjual"].map(ljl.format_int_id)
        tampil["Omzet"] = tp["Omzet"].map(ljl.format_rupiah_id)
        tampil["Laba"] = tp["Laba"].map(ljl.format_rupiah_id)
        st.dataframe(tampil, use_container_width=True, height=460)
        st.download_button("⬇️ Unduh CSV — Semua Produk Aksesoris", tp.to_csv(index=True).encode("utf-8-sig"), "semua_produk_aksesoris.csv", "text/csv", key="jl_dl_produk")

    st.divider()
    st.header("Seluruh Sales")
    kategori_penjualan_opsi = sorted(dff["KATEGORI PENJUALAN"].dropna().unique().tolist())
    c1, c2 = st.columns([2, 1])
    with c1:
        sel_kategori = st.multiselect(
            "Filter kategori penjualan (kosongkan / pilih semua untuk seluruh sales)",
            kategori_penjualan_opsi, default=kategori_penjualan_opsi, key="jl_kategori_sales",
        )
    with c2:
        metrik_sales = st.radio("Urutkan berdasarkan", ["Omzet", "Laba", "Jumlah Nota"], key="jl_metrik_sales")
    if not sel_kategori:
        st.info("Pilih minimal satu kategori penjualan.")
    else:
        ts = ljl.ranking_sales(dff, metric=metrik_sales, n=None, kategori_penjualan=sel_kategori)
        if ts.empty:
            st.info("Tidak ada transaksi pada filter ini.")
        else:
            st.caption(f"{len(ts):,}".replace(",", ".") + " sales berbeda.")
            tampil = ts.copy()
            tampil["Omzet"] = ts["Omzet"].map(ljl.format_rupiah_id)
            tampil["Laba"] = ts["Laba"].map(ljl.format_rupiah_id)
            tampil["Jumlah Nota"] = ts["Jumlah Nota"].map(ljl.format_int_id)
            st.dataframe(tampil, use_container_width=True, height=460)
            st.download_button(
                "⬇️ Unduh CSV — Seluruh Sales", ts.to_csv(index=True).encode("utf-8-sig"), "seluruh_sales.csv", "text/csv", key="jl_dl_sales",
            )

    st.divider()
    st.caption(
        "Aturan data: satu nota = CABANG + NO FAKTUR · HARGA BELI sudah total per baris "
        "(tidak dikalikan QTY) · baris kembar dihitung apa adanya · AKSESORIS dan "
        "ACCESORIES digabung jadi satu kategori."
    )


# ---------------------------------------------------------------------------
# TAB 3 — Dashboard Revenue Penjualan Aksesoris
# ---------------------------------------------------------------------------
def render_aksesoris_tab():
    if err_aksesoris:
        st.error(f"Gagal membaca berkas penjualan aksesoris: {err_aksesoris}")
        return
    if df_aksesoris is None:
        st.info(
            "Belum ada data. Unggah berkas Excel/CSV **Penjualan Aksesoris Regional** "
            "(sheet **Rincian Faktur Penjualan**) lewat panel kiri, atau taruh berkasnya "
            "di root repo sebelum deploy."
        )
        return

    df = df_aksesoris

    st.subheader("Filter — Data Penjualan Aksesoris")
    tahun_opsi = sorted([int(t) for t in df["TAHUN"].dropna().unique()])
    bulan_opsi = sorted([int(b) for b in df["BULAN"].dropna().unique()])
    cabang_opsi = sorted(df["CABANG"].dropna().unique().tolist())
    segmen_opsi = sorted(df["SEGMEN"].dropna().unique().tolist())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sel_tahun = st.multiselect("Tahun", tahun_opsi, default=tahun_opsi, key="ak_tahun")
    with c2:
        sel_bulan = st.multiselect(
            "Bulan", bulan_opsi, default=bulan_opsi, format_func=lambda b: BULAN_NAMA.get(b, str(b)), key="ak_bulan",
        )
    with c3:
        sel_cabang = st.multiselect("Cabang", cabang_opsi, default=cabang_opsi, key="ak_cabang")
    with c4:
        sel_segmen = st.multiselect("Segmen", segmen_opsi, default=segmen_opsi, key="ak_segmen")

    dff = la.apply_filters(
        df,
        tahun=sel_tahun if sel_tahun else None,
        bulan=sel_bulan if sel_bulan else None,
        cabang=sel_cabang if sel_cabang else None,
        segmen=sel_segmen if sel_segmen else None,
    )

    if dff.empty:
        st.warning("Tidak ada data untuk kombinasi filter ini. Coba longgarkan pilihan di atas.")
        return

    st.caption(
        f"Menampilkan {len(dff):,}".replace(",", ".") + " baris · "
        f"{dff['NOTA_ID'].nunique():,}".replace(",", ".") + " nota unik (cabang + no faktur)"
    )
    st.divider()

    # -----------------------------------------------------------------
    # 1. Dashboard Revenue
    # -----------------------------------------------------------------
    st.header("💰 Revenue Penjualan Aksesoris")

    rs = la.revenue_summary(dff)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Omzet", la.format_rupiah_id(rs["omzet"]))
    c2.metric("HPP (Harga Beli)", la.format_rupiah_id(rs["modal"]))
    c3.metric("Laba", la.format_rupiah_id(rs["laba"]))
    c4.metric("Margin", la.format_percent_id(rs["margin"]))
    c5.metric("Rata-rata / Nota", la.format_rupiah_id(rs["rata_per_nota"]))
    st.caption(
        f"{la.format_int_id(rs['jumlah_nota'])} nota · {la.format_int_id(rs['jumlah_item'])} item terjual · "
        f"HPP = total HARGA BELI per baris (sudah nilai total, tidak dikalikan QTY lagi)"
    )

    trend = la.revenue_trend_bulanan(dff)
    if not trend.empty:
        st.subheader("Tren Omzet & Laba Bulanan")
        st.caption(
            "Bulan berjalan yang belum lengkap tetap ditampilkan di grafik, tapi tidak "
            "dipakai sebagai dasar rata-rata pada bagian Proyeksi di bawah."
        )
        st.bar_chart(trend.set_index("Periode")[["Omzet", "Laba"]])
        tampil_trend = trend.copy()
        for col in ["Omzet", "Modal", "Laba"]:
            tampil_trend[col] = trend[col].map(la.format_rupiah_id)
        tampil_trend["Margin (%)"] = trend["Margin (%)"].map(la.format_percent_id)
        tampil_trend["Qty Terjual"] = trend["Qty Terjual"].map(la.format_int_id)
        tampil_trend["Jumlah Nota"] = trend["Jumlah Nota"].map(la.format_int_id)
        st.dataframe(tampil_trend, use_container_width=True)
        st.download_button(
            "⬇️ Unduh CSV — Tren Bulanan", trend.to_csv(index=False).encode("utf-8-sig"),
            "tren_revenue_aksesoris.csv", "text/csv", key="ak_dl_trend",
        )

    seg = la.revenue_per_segmen(dff)
    if not seg.empty:
        st.subheader("Omzet per Segmen Transaksi")
        st.caption("Service = dari transaksi Service HP/Laptop dll · Penjualan Unit = HP/Laptop baru & second.")
        st.bar_chart(seg.set_index("Segmen")["Omzet"])
        tampil_seg = seg.copy()
        tampil_seg["Omzet"] = seg["Omzet"].map(la.format_rupiah_id)
        tampil_seg["Laba"] = seg["Laba"].map(la.format_rupiah_id)
        tampil_seg["Margin (%)"] = seg["Margin (%)"].map(la.format_percent_id)
        tampil_seg["Jumlah Nota"] = seg["Jumlah Nota"].map(la.format_int_id)
        tampil_seg["Porsi Omzet (%)"] = seg["Porsi Omzet (%)"].map(la.format_percent_id)
        st.dataframe(tampil_seg, use_container_width=True)

    st.divider()

    # -----------------------------------------------------------------
    # 2. Top 10 Produk Terlaris & Profit
    # -----------------------------------------------------------------
    st.header("🏆 Top 10 Produk Aksesoris Terlaris & Profit")
    metrik_produk = st.radio(
        "Urutkan berdasarkan", ["Qty Terjual", "Omzet", "Laba"], key="ak_metrik_produk", horizontal=True,
    )
    tp = la.top_produk(dff, metric=metrik_produk, n=10)
    if tp.empty:
        st.info("Tidak ada data produk pada filter ini.")
    else:
        tampil_tp = tp.copy()
        tampil_tp["Qty Terjual"] = tp["Qty Terjual"].map(la.format_int_id)
        tampil_tp["Omzet"] = tp["Omzet"].map(la.format_rupiah_id)
        tampil_tp["Modal"] = tp["Modal"].map(la.format_rupiah_id)
        tampil_tp["Laba"] = tp["Laba"].map(la.format_rupiah_id)
        tampil_tp["Margin (%)"] = tp["Margin (%)"].map(la.format_percent_id)
        st.dataframe(tampil_tp, use_container_width=True)
        st.download_button(
            "⬇️ Unduh CSV — Top 10 Produk", tp.to_csv(index=True).encode("utf-8-sig"),
            "top_produk_aksesoris.csv", "text/csv", key="ak_dl_produk",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 3. Dashboard Omzet All Cabang
    # -----------------------------------------------------------------
    st.header("🏬 Omzet & HPP Seluruh Cabang")
    st.caption(
        "HPP (Harga Pokok Penjualan) = total HARGA BELI dari seluruh item aksesoris yang "
        "terjual di cabang tersebut — dipakai untuk melihat beban modal per cabang, "
        "bukan cuma omzet dan laba."
    )
    oc = la.omzet_cabang(dff)
    if oc.empty:
        st.info("Tidak ada data cabang pada filter ini.")
    else:
        tab_chart1, tab_chart2 = st.tabs(["Omzet vs HPP per Cabang", "HPP terhadap Omzet (%)"])
        with tab_chart1:
            st.bar_chart(oc.set_index("Cabang")[["Omzet", "HPP"]])
        with tab_chart2:
            st.bar_chart(oc.set_index("Cabang")["HPP terhadap Omzet (%)"])

        tampil_oc = oc.copy()
        tampil_oc["Omzet"] = oc["Omzet"].map(la.format_rupiah_id)
        tampil_oc["HPP"] = oc["HPP"].map(la.format_rupiah_id)
        tampil_oc["Laba"] = oc["Laba"].map(la.format_rupiah_id)
        tampil_oc["Margin (%)"] = oc["Margin (%)"].map(la.format_percent_id)
        tampil_oc["HPP terhadap Omzet (%)"] = oc["HPP terhadap Omzet (%)"].map(la.format_percent_id)
        tampil_oc["Jumlah Nota"] = oc["Jumlah Nota"].map(la.format_int_id)
        tampil_oc["Rata-rata / Nota"] = oc["Rata-rata / Nota"].map(la.format_rupiah_id)
        st.dataframe(tampil_oc, use_container_width=True, height=460)
        st.download_button(
            "⬇️ Unduh CSV — Omzet & HPP per Cabang", oc.to_csv(index=True).encode("utf-8-sig"),
            "omzet_hpp_cabang.csv", "text/csv", key="ak_dl_cabang",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 3b. Katalog Referensi Harga LUNA & Potensi Profit
    # -----------------------------------------------------------------
    st.header("🧾 Katalog Referensi Harga LUNA & Potensi Profit")
    st.caption(
        "Pricelist resmi LUNA (harga dealer & saran harga jual ke konsumen/SRP) — "
        "sebagai gambaran potensi profit per produk yang bisa didapat cabang, "
        "terlepas dari harga aktual di lapangan."
    )

    katalog = la.katalog_luna_aksesoris()
    kategori_katalog_opsi = sorted(katalog["Kategori"].unique().tolist())
    sel_kategori_katalog = st.multiselect(
        "Filter kategori katalog", kategori_katalog_opsi, default=kategori_katalog_opsi, key="ak_kategori_katalog",
    )
    katalog_f = katalog[katalog["Kategori"].isin(sel_kategori_katalog)] if sel_kategori_katalog else katalog.iloc[0:0]

    if katalog_f.empty:
        st.info("Pilih minimal satu kategori untuk menampilkan katalog.")
    else:
        margin_rata2_katalog = katalog_f["Potensi Margin (%)"].mean()
        margin_aktual = rs["margin"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Rata-rata Margin Potensial (katalog LUNA)", la.format_percent_id(margin_rata2_katalog))
        c2.metric("Margin Aktual Tercapai (data penjualan)", la.format_percent_id(margin_aktual))
        selisih = margin_aktual - margin_rata2_katalog
        c3.metric("Selisih", f"{'+' if selisih >= 0 else ''}{la.format_decimal_id(selisih)} poin")
        st.caption(
            "Margin aktual bisa lebih tinggi dari margin katalog murni kalau cabang "
            "menjual sesuai skema **Up Harga Bundling** dari Surat Edaran "
            "SE/001/IN-MF/IV/2026 (nilai tambahan tetap per tier, bukan mengikuti SRP "
            "per produk) — atau bisa lebih rendah kalau harga jual di lapangan belum "
            "mengikuti SRP resmi. Bandingkan sebagai bahan evaluasi, bukan kesimpulan pasti."
        )

        ring = la.ringkasan_margin_katalog(katalog_f)
        st.subheader("Rata-rata Margin Potensial per Kategori")
        st.bar_chart(ring.set_index("Kategori")["Rata-rata Margin (%)"])
        tampil_ring = ring.copy()
        tampil_ring["Rata-rata Dealer"] = ring["Rata-rata Dealer"].map(la.format_rupiah_id)
        tampil_ring["Rata-rata SRP"] = ring["Rata-rata SRP"].map(la.format_rupiah_id)
        tampil_ring["Rata-rata Margin (%)"] = ring["Rata-rata Margin (%)"].map(la.format_percent_id)
        st.dataframe(tampil_ring, use_container_width=True)

        with st.expander(f"Lihat detail katalog ({len(katalog_f)} produk)"):
            tampil_katalog = katalog_f.copy()
            tampil_katalog["Dealer"] = katalog_f["Dealer"].map(la.format_rupiah_id)
            tampil_katalog["SRP"] = katalog_f["SRP"].map(la.format_rupiah_id)
            tampil_katalog["Potensi Profit"] = katalog_f["Potensi Profit"].map(la.format_rupiah_id)
            tampil_katalog["Potensi Margin (%)"] = katalog_f["Potensi Margin (%)"].map(la.format_percent_id)
            st.dataframe(tampil_katalog, use_container_width=True, height=400)
            st.download_button(
                "⬇️ Unduh CSV — Katalog LUNA (Aksesoris)", katalog_f.to_csv(index=False).encode("utf-8-sig"),
                "katalog_luna_aksesoris.csv", "text/csv", key="ak_dl_katalog",
            )

        with st.expander("Lihat katalog bahan & mesin cutting (harga dealer saja, tanpa SRP)"):
            st.caption(
                "Produk ini (material tempered glass/hydrogel & mesin cutting) tidak "
                "punya SRP resmi karena harga jual ke konsumen ditentukan sendiri oleh "
                "tiap cabang per potongan sesuai model HP."
            )
            mat = la.katalog_luna_material()
            tampil_mat = mat.copy()
            tampil_mat["Dealer (per box)"] = mat["Dealer (per box)"].map(la.format_rupiah_id)
            tampil_mat["Estimasi Modal per Pcs"] = mat["Estimasi Modal per Pcs"].apply(
                lambda x: la.format_rupiah_id(x) if pd.notna(x) else "-"
            )
            st.dataframe(tampil_mat, use_container_width=True, height=320)

    st.divider()

    # -----------------------------------------------------------------
    # 4. Analisa & Proyeksi 5-10 Tahun
    # -----------------------------------------------------------------
    st.header("📈 Analisa Penjualan & Proyeksi 5–10 Tahun")

    rr = la.hitung_run_rate(dff)
    if rr["jumlah_bulan"] == 0:
        st.info("Data tidak cukup untuk membuat proyeksi (butuh minimal satu bulan penuh).")
    else:
        st.caption(
            f"Proyeksi dihitung dari rata-rata omzet **{rr['jumlah_bulan']} bulan penuh** "
            f"({la.format_rupiah_id(rr['omzet_bulanan'])}/bulan, margin {la.format_percent_id(rr['margin'])})."
            + (f" Bulan **{rr['bulan_tidak_lengkap']}** dikeluarkan dari rata-rata karena datanya belum lengkap."
               if rr["bulan_tidak_lengkap"] else "")
        )
        st.warning(
            "⚠️ Data historis yang tersedia baru mencakup kurang dari 1 tahun (Jan–Ags 2026). "
            "Proyeksi 5–10 tahun di bawah ini adalah **ekstrapolasi kasar** dari 3 skenario "
            "pertumbuhan tahunan, bukan model statistik yang memperhitungkan musiman atau siklus "
            "ekonomi — gunakan sebagai ilustrasi arah, bukan angka pasti untuk perencanaan keuangan."
        )

        proj = la.proyeksi_tahunan(rr["omzet_bulanan"])
        pivot = proj.pivot(index="Tahun ke-", columns="Skenario", values="Proyeksi Omzet Tahunan")
        st.subheader("Proyeksi Omzet Tahunan per Skenario")
        st.line_chart(pivot)
        tampil_proj = pivot.copy()
        for c in tampil_proj.columns:
            tampil_proj[c] = tampil_proj[c].map(la.format_rupiah_id)
        st.dataframe(tampil_proj, use_container_width=True)
        st.download_button(
            "⬇️ Unduh CSV — Proyeksi", proj.to_csv(index=False).encode("utf-8-sig"),
            "proyeksi_omzet_aksesoris.csv", "text/csv", key="ak_dl_proyeksi",
        )

    st.subheader("📌 Analisa & Rekomendasi")
    catatan = []

    if not seg.empty:
        seg_top = seg.iloc[0]
        catatan.append(
            f"Segmen **{seg_top['Segmen']}** menyumbang porsi omzet terbesar "
            f"({la.format_percent_id(seg_top['Porsi Omzet (%)'])}) dengan margin "
            f"{la.format_percent_id(seg_top['Margin (%)'])}. Ini sejalan dengan program **Bundling "
            "Aksesoris NexLink & LUNA** yang menambahkan aksesoris otomatis ke setiap transaksi "
            "Service — perluas cakupan tier bundling (mengikuti Surat Edaran SE/001/IN-MF/IV/2026) "
            "bisa jadi pengungkit utama pertumbuhan 5-10 tahun ke depan."
        )
        service_row = seg[seg["Segmen"] == "Service"]
        if not service_row.empty and service_row.iloc[0]["Margin (%)"] > seg["Margin (%)"].mean():
            catatan.append(
                "Margin dari segmen Service secara konsisten lebih tinggi dibanding rata-rata — "
                "menambah jumlah cabang atau memperluas tier bundling pada layanan Service berpotensi "
                "menaikkan profitabilitas lebih cepat dibanding menambah unit baru."
            )

    if not oc.empty:
        oc_sorted_asc = oc.sort_values("Omzet")
        terendah = oc_sorted_asc.iloc[0]
        tertinggi = oc.iloc[0]
        catatan.append(
            f"Cabang **{terendah['Cabang']}** memiliki omzet terendah "
            f"({la.format_rupiah_id(terendah['Omzet'])}) dibanding cabang tertinggi "
            f"**{tertinggi['Cabang']}** ({la.format_rupiah_id(tertinggi['Omzet'])}) — perlu ditelusuri "
            "apakah ini soal lokasi/traffic, kelengkapan stok aksesoris, atau kurangnya penawaran "
            "bundling oleh frontliner di cabang tersebut."
        )
        margin_rendah = oc.sort_values("Margin (%)").iloc[0]
        if margin_rendah["Margin (%)"] < oc["Margin (%)"].mean() - 10:
            catatan.append(
                f"Cabang **{margin_rendah['Cabang']}** punya margin jauh di bawah rata-rata "
                f"({la.format_percent_id(margin_rendah['Margin (%)'])}) — cek harga modal aksesorisnya, "
                "kemungkinan sering membeli dari pemasok non-LUNA dengan modal lebih mahal "
                "(lihat tab Dashboard Pembelian Cabang untuk detail kepatuhan ke pemasok target)."
            )

    if not tp.empty:
        produk_top = tp.iloc[0]
        catatan.append(
            f"Produk **{produk_top['NAMA BARANG']}** adalah yang paling laris — pastikan stoknya "
            "selalu tersedia di semua cabang, terutama untuk mendukung tier bundling di Surat Edaran."
        )

    if not katalog_f.empty:
        margin_katalog_final = katalog_f["Potensi Margin (%)"].mean()
        if rs["margin"] < margin_katalog_final:
            catatan.append(
                f"Margin aktual saat ini ({la.format_percent_id(rs['margin'])}) masih di bawah rata-rata "
                f"margin potensial dari katalog resmi LUNA ({la.format_percent_id(margin_katalog_final)}) — "
                "cek apakah harga jual ke konsumen di cabang sudah mengikuti SRP resmi, atau modal "
                "pembelian aksesoris masih sering dari pemasok non-LUNA yang lebih mahal."
            )
        else:
            catatan.append(
                f"Margin aktual saat ini ({la.format_percent_id(rs['margin'])}) sudah di atas rata-rata "
                f"margin potensial murni dari katalog LUNA ({la.format_percent_id(margin_katalog_final)}) — "
                "kemungkinan besar berkat skema Up Harga Bundling di Surat Edaran. Pertahankan dan "
                "pastikan seluruh cabang konsisten menerapkannya."
            )

    catatan.append(
        "Untuk pertumbuhan 5–10 tahun ke depan, tiga pengungkit paling realistis dari data ini: "
        "(1) **menaikkan attach rate bundling** di transaksi Service (segmen dengan margin tertinggi), "
        "(2) **menyamakan performa cabang lemah** dengan cabang terbaik lewat pelatihan/SOP penawaran "
        "aksesoris, dan (3) **konsolidasi pembelian ke pemasok bermodal rendah** (seperti target LUNA) "
        "untuk menaikkan margin tanpa menaikkan harga jual ke customer."
    )

    for c in catatan:
        st.markdown("- " + c)


# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_stok, tab_penjualan_aksesoris = st.tabs([
    "📊 Dashboard Stok Semua Cabang", "🧾 Dashboard Penjualan Aksesoris",
])

with tab_stok:
    render_stok_tab()

with tab_penjualan_aksesoris:
    render_penjualan_tab()

    st.divider()
    st.divider()
    st.markdown("## 💰 Revenue, HPP & Katalog LUNA")
    st.caption(
        "Bagian di bawah ini memakai berkas data penjualan aksesoris khusus "
        "(unggah terpisah di panel kiri) untuk analisa revenue, HPP, katalog LUNA, "
        "dan proyeksi 5–10 tahun."
    )

    render_aksesoris_tab()
