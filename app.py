import os
import streamlit as st
import pandas as pd

import logic_pembelian as lp
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
st.sidebar.header("📦 Data Pembelian")
st.sidebar.caption("Sheet \"DB Pembelian\" — Excel atau CSV sepadan")
upl_pembelian = st.sidebar.file_uploader(
    "Unggah berkas pembelian", type=["xlsx", "xls", "csv"], key="upl_pembelian",
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
st.sidebar.header("🎯 Target Pemasok (untuk tab Pembelian)")
nama_pemasok_target = st.sidebar.text_input("Nama pemasok yang ditarget", value="LUNA", key="target_pemasok").strip().upper()
target_rp = st.sidebar.number_input(
    "Target pembelian ke pemasok ini (Rp)",
    min_value=0, value=2_000_000_000, step=50_000_000, format="%d", key="target_rp",
)

# ---------------------------------------------------------------------------
# Muat data (dua sumber independen)
# ---------------------------------------------------------------------------
DEFAULT_PEMBELIAN_PATH = "Purchase_Aksesoris_Regional.xlsx"
DEFAULT_PENJUALAN_PATH = "penjualan.csv.gz"

df_pembelian, err_pembelian = None, None
try:
    if upl_pembelian is not None:
        df_pembelian = lp.load_pembelian(upl_pembelian)
    elif os.path.exists(DEFAULT_PEMBELIAN_PATH):
        df_pembelian = lp.load_pembelian(DEFAULT_PEMBELIAN_PATH)
except Exception as e:
    err_pembelian = str(e)

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
# TAB 1 — Dashboard Pembelian Cabang
# ---------------------------------------------------------------------------
def render_pembelian_tab():
    if err_pembelian:
        st.error(f"Gagal membaca berkas pembelian: {err_pembelian}")
        return
    if df_pembelian is None:
        st.info(
            "Belum ada data pembelian. Unggah berkas Excel (sheet **DB Pembelian**) "
            "lewat panel kiri, atau taruh berkasnya di root repo sebelum deploy."
        )
        return

    st.subheader("Filter — Data Pembelian")
    tahun_opsi = sorted([int(t) for t in df_pembelian["TAHUN"].dropna().unique()])
    bulan_opsi = sorted([int(b) for b in df_pembelian["BULAN"].dropna().unique()])
    cabang_opsi = sorted(df_pembelian["CABANG"].dropna().unique().tolist())

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_tahun = st.multiselect("Tahun", tahun_opsi, default=tahun_opsi, key="pb_tahun")
    with c2:
        sel_bulan = st.multiselect(
            "Bulan", bulan_opsi, default=bulan_opsi, format_func=lambda b: BULAN_NAMA.get(b, str(b)), key="pb_bulan",
        )
    with c3:
        sel_cabang = st.multiselect("Cabang", cabang_opsi, default=cabang_opsi, key="pb_cabang")

    sel_kebutuhan = None
    if "KATEGORI KEBUTUHAN" in df_pembelian.columns:
        kebutuhan_opsi = sorted(df_pembelian["KATEGORI KEBUTUHAN"].dropna().unique().tolist())
        sel_kebutuhan = st.multiselect("Kategori Kebutuhan", kebutuhan_opsi, default=kebutuhan_opsi, key="pb_kebutuhan")

    dff = lp.apply_filters(
        df_pembelian,
        tahun=sel_tahun if sel_tahun else None,
        bulan=sel_bulan if sel_bulan else None,
        cabang=sel_cabang if sel_cabang else None,
        kebutuhan=sel_kebutuhan if sel_kebutuhan else None,
    )

    if dff.empty:
        st.warning("Tidak ada data untuk kombinasi filter ini. Coba longgarkan pilihan di atas.")
        return

    st.caption(
        f"Menampilkan {len(dff):,}".replace(",", ".") + " baris pembelian aksesoris · "
        f"total {lp.format_rupiah_id(dff['Total Harga'].sum())}"
    )
    st.divider()

    st.header("Porsi Pemasok — Terbesar ke Terkecil")
    pp = lp.porsi_pemasok(dff)
    if pp.empty:
        st.info("Tidak ada data pemasok pada filter ini.")
    else:
        top_n = st.slider("Tampilkan berapa pemasok teratas di grafik", 5, min(30, len(pp)), min(15, len(pp)), key="pb_topn")
        st.bar_chart(pp.head(top_n).set_index("Pemasok")["Total Pembelian"])

        tampil = pp.copy()
        tampil["Total Pembelian"] = pp["Total Pembelian"].map(lp.format_rupiah_id)
        tampil["Jumlah Transaksi"] = pp["Jumlah Transaksi"].map(lp.format_int_id)
        tampil["Porsi (%)"] = pp["Porsi (%)"].map(lp.format_percent_id)
        tampil["Kumulatif (%)"] = pp["Kumulatif (%)"].map(lp.format_percent_id)
        st.dataframe(tampil, use_container_width=True, height=420)
        st.download_button(
            "⬇️ Unduh CSV — Porsi Pemasok (lengkap)",
            pp.to_csv(index=True).encode("utf-8-sig"),
            "porsi_pemasok.csv", "text/csv", key="pb_dl_pemasok",
        )

    st.divider()
    st.header(f"Fokus Target — {nama_pemasok_target}")
    st.caption(
        f"Aturan: semua cabang wajib membeli aksesoris di {nama_pemasok_target}; "
        f"boleh beli di pemasok lain hanya kalau produknya tidak tersedia di {nama_pemasok_target}."
    )

    prog = lp.luna_progress(dff, target=target_rp, supplier_key=nama_pemasok_target)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tercapai", lp.format_rupiah_id(prog["tercapai"]))
    c2.metric("Target", lp.format_rupiah_id(prog["target"]))
    c3.metric("% Pencapaian", lp.format_percent_id(prog["pct_target"]))
    c4.metric("Sisa Target", lp.format_rupiah_id(prog["sisa"]))
    st.progress(min(prog["pct_target"] / 100, 1.0) if prog["target"] else 0)
    st.caption(
        f"Porsi belanja ke {nama_pemasok_target} baru {lp.format_percent_id(prog['pct_dari_total_aksesoris'])} "
        f"dari total belanja aksesoris pada filter ini ({lp.format_rupiah_id(prog['total_aksesoris'])}). "
        f"Data mencakup {prog['hari_berjalan']} hari "
        f"({prog['tgl_min'].strftime('%d %b %Y') if pd.notna(prog['tgl_min']) else '-'} – "
        f"{prog['tgl_max'].strftime('%d %b %Y') if pd.notna(prog['tgl_max']) else '-'}), "
        f"rata-rata {lp.format_rupiah_id(prog['run_rate_harian'])}/hari ke {nama_pemasok_target}."
    )

    st.subheader(f"Kepatuhan per Cabang (porsi belanja ke {nama_pemasok_target})")
    st.caption("Diurutkan dari porsi TERKECIL — cabang yang paling perlu didorong ada di paling atas.")
    pk = lp.per_cabang_kepatuhan(dff, supplier_key=nama_pemasok_target)
    if pk.empty:
        st.info("Tidak ada data cabang pada filter ini.")
    else:
        tampil_pk = pk.copy()
        tampil_pk["Total Belanja Aksesoris"] = pk["Total Belanja Aksesoris"].map(lp.format_rupiah_id)
        tampil_pk[f"Belanja ke {nama_pemasok_target}"] = pk[f"Belanja ke {nama_pemasok_target}"].map(lp.format_rupiah_id)
        tampil_pk[f"Porsi ke {nama_pemasok_target} (%)"] = pk[f"Porsi ke {nama_pemasok_target} (%)"].map(lp.format_percent_id)
        st.dataframe(tampil_pk, use_container_width=True, height=420)
        st.download_button(
            f"⬇️ Unduh CSV — Kepatuhan per Cabang ({nama_pemasok_target})",
            pk.to_csv(index=True).encode("utf-8-sig"),
            "kepatuhan_cabang.csv", "text/csv", key="pb_dl_kepatuhan",
        )

    st.subheader("Sinyal Awal: Kemungkinan Bisa Dialihkan ke " + nama_pemasok_target)
    st.caption(
        f"Pembelian dari pemasok LAIN untuk barang yang nama persis-nya pernah dibeli dari "
        f"{nama_pemasok_target}. Bukan bukti pelanggaran (stok bisa saja sedang kosong), tapi layak ditelusuri."
    )
    kk = lp.kandidat_kebocoran(dff, supplier_key=nama_pemasok_target)
    if kk.empty:
        st.info(f"Tidak ditemukan barang yang tumpang tindih dengan katalog {nama_pemasok_target} pada filter ini.")
    else:
        tampil_kk = kk.copy()
        tampil_kk["Total Harga"] = kk["Total Harga"].map(lp.format_rupiah_id)
        st.dataframe(tampil_kk, use_container_width=True, height=320)
        st.caption(f"Total {len(kk)} baris, senilai {lp.format_rupiah_id(kk['Total Harga'].sum())}.")
        st.download_button(
            "⬇️ Unduh CSV — Sinyal Kemungkinan Bisa Dialihkan",
            kk.to_csv(index=False).encode("utf-8-sig"),
            "kandidat_kebocoran.csv", "text/csv", key="pb_dl_kebocoran",
        )

    st.divider()
    st.header("📌 Analisa & Tindak Lanjut")
    catatan = []
    if prog["pct_target"] < 50:
        catatan.append(
            f"Pencapaian ke {nama_pemasok_target} baru **{lp.format_percent_id(prog['pct_target'])}** dari target "
            f"{lp.format_rupiah_id(prog['target'])}. Dengan rata-rata **{lp.format_rupiah_id(prog['run_rate_harian'])}/hari**, "
            "laju ini kemungkinan tidak mengejar target tanpa dorongan tambahan ke cabang-cabang."
        )
    else:
        catatan.append(
            f"Pencapaian ke {nama_pemasok_target} sudah **{lp.format_percent_id(prog['pct_target'])}** dari target — "
            "di jalur yang cukup baik."
        )
    if not pk.empty:
        terendah = pk.iloc[0]
        catatan.append(
            f"Cabang dengan porsi terendah: **{terendah['Cabang']}** "
            f"({lp.format_percent_id(terendah[f'Porsi ke {nama_pemasok_target} (%)'])}) — prioritaskan cabang ini."
        )
        tertinggi = pk.iloc[-1]
        catatan.append(
            f"Cabang dengan porsi tertinggi: **{tertinggi['Cabang']}** "
            f"({lp.format_percent_id(tertinggi[f'Porsi ke {nama_pemasok_target} (%)'])}) — contoh praktik baik."
        )
    if not pp.empty:
        top1 = pp.iloc[0]
        if top1["Pemasok"] != nama_pemasok_target:
            catatan.append(
                f"Pemasok porsi terbesar saat ini justru **{top1['Pemasok']}** ({lp.format_percent_id(top1['Porsi (%)'])}), "
                f"bukan {nama_pemasok_target}. Cek apakah kategorinya di luar katalog {nama_pemasok_target}."
            )
    if not kk.empty:
        catatan.append(
            f"Ada **{len(kk)} baris** (senilai {lp.format_rupiah_id(kk['Total Harga'].sum())}) berpotensi dialihkan — lihat tabel sinyal di atas."
        )
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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Omzet", la.format_rupiah_id(rs["omzet"]))
    c2.metric("Laba", la.format_rupiah_id(rs["laba"]))
    c3.metric("Margin", la.format_percent_id(rs["margin"]))
    c4.metric("Rata-rata / Nota", la.format_rupiah_id(rs["rata_per_nota"]))
    st.caption(
        f"{la.format_int_id(rs['jumlah_nota'])} nota · {la.format_int_id(rs['jumlah_item'])} item terjual "
        f"· modal {la.format_rupiah_id(rs['modal'])}"
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
    st.header("🏬 Omzet Seluruh Cabang")
    oc = la.omzet_cabang(dff)
    if oc.empty:
        st.info("Tidak ada data cabang pada filter ini.")
    else:
        st.bar_chart(oc.set_index("Cabang")["Omzet"])
        tampil_oc = oc.copy()
        tampil_oc["Omzet"] = oc["Omzet"].map(la.format_rupiah_id)
        tampil_oc["Modal"] = oc["Modal"].map(la.format_rupiah_id)
        tampil_oc["Laba"] = oc["Laba"].map(la.format_rupiah_id)
        tampil_oc["Margin (%)"] = oc["Margin (%)"].map(la.format_percent_id)
        tampil_oc["Jumlah Nota"] = oc["Jumlah Nota"].map(la.format_int_id)
        tampil_oc["Rata-rata / Nota"] = oc["Rata-rata / Nota"].map(la.format_rupiah_id)
        st.dataframe(tampil_oc, use_container_width=True, height=460)
        st.download_button(
            "⬇️ Unduh CSV — Omzet per Cabang", oc.to_csv(index=True).encode("utf-8-sig"),
            "omzet_cabang.csv", "text/csv", key="ak_dl_cabang",
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
tab_pembelian, tab_penjualan, tab_aksesoris = st.tabs([
    "📦 Dashboard Pembelian Cabang", "🧾 Dashboard Penjualan Cabang", "💰 Dashboard Revenue Aksesoris",
])

with tab_pembelian:
    render_pembelian_tab()

with tab_penjualan:
    render_penjualan_tab()

with tab_aksesoris:
    render_aksesoris_tab()
