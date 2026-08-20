import os
import streamlit as st
import pandas as pd

import logic_pembelian as lp
import logic_penjualan as ljl

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

    st.header("Top 3 Cabang")
    c1, c2 = st.columns([1, 3])
    with c1:
        metrik_cabang = st.radio("Urutkan berdasarkan", ["Omzet", "Laba", "Jumlah Nota"], key="jl_metrik_cabang")
    tc = ljl.top_cabang(dff, metric=metrik_cabang, n=3)
    with c2:
        if tc.empty:
            st.info("Tidak ada data cabang pada filter ini.")
        else:
            medali = ["🥇", "🥈", "🥉"]
            cols = st.columns(len(tc))
            for i, (col, (_, row)) in enumerate(zip(cols, tc.iterrows())):
                with col:
                    st.metric(f"{medali[i]} {row['CABANG']}", ljl.format_rupiah_id(row["Omzet"]), f"Laba {ljl.format_rupiah_id(row['Laba'])}")
                    st.caption(f"Margin {ljl.format_percent_id(row['Margin (%)'])} · {ljl.format_int_id(row['Jumlah Nota'])} nota")
    if not tc.empty:
        tampil = tc.copy()
        for col in ["Omzet", "Modal", "Laba"]:
            tampil[col] = tc[col].map(ljl.format_rupiah_id)
        tampil["Margin (%)"] = tc["Margin (%)"].map(ljl.format_percent_id)
        tampil["Jumlah Nota"] = tc["Jumlah Nota"].map(ljl.format_int_id)
        st.dataframe(tampil, use_container_width=True)
        st.download_button("⬇️ Unduh CSV — Top Cabang", tc.to_csv(index=True).encode("utf-8-sig"), "top_cabang.csv", "text/csv", key="jl_dl_cabang")

    st.divider()
    st.header("Top 10 Produk Terlaris")
    metrik_produk = st.radio("Urutkan berdasarkan", ["Qty Terjual", "Omzet"], key="jl_metrik_produk", horizontal=True)
    tp = ljl.top_produk(dff, metric=metrik_produk, n=10)
    if tp.empty:
        st.info("Tidak ada data produk pada filter ini.")
    else:
        tampil = tp.copy()
        tampil["Qty Terjual"] = tp["Qty Terjual"].map(ljl.format_int_id)
        tampil["Omzet"] = tp["Omzet"].map(ljl.format_rupiah_id)
        tampil["Laba"] = tp["Laba"].map(ljl.format_rupiah_id)
        st.dataframe(tampil, use_container_width=True)
        st.download_button("⬇️ Unduh CSV — Top Produk", tp.to_csv(index=True).encode("utf-8-sig"), "top_produk.csv", "text/csv", key="jl_dl_produk")

    st.divider()
    st.header("Top 5 Sales Retail")
    kategori_penjualan_opsi = sorted(dff["KATEGORI PENJUALAN"].dropna().unique().tolist())
    default_retail = [k for k in kategori_penjualan_opsi if "RETAIL" in str(k).upper()] or kategori_penjualan_opsi
    c1, c2 = st.columns([2, 1])
    with c1:
        sel_kategori_retail = st.multiselect(
            "Kategori penjualan yang dianggap \"retail\"", kategori_penjualan_opsi, default=default_retail, key="jl_kategori_retail",
        )
    with c2:
        metrik_sales = st.radio("Urutkan berdasarkan", ["Omzet", "Laba", "Jumlah Nota"], key="jl_metrik_sales")
    if not sel_kategori_retail:
        st.info("Pilih minimal satu kategori penjualan untuk dianggap sebagai retail.")
    else:
        ts = ljl.top_sales_retail(dff, sel_kategori_retail, metric=metrik_sales, n=5)
        if ts.empty:
            st.info("Tidak ada transaksi retail pada filter ini.")
        else:
            tampil = ts.copy()
            tampil["Omzet"] = ts["Omzet"].map(ljl.format_rupiah_id)
            tampil["Laba"] = ts["Laba"].map(ljl.format_rupiah_id)
            tampil["Jumlah Nota"] = ts["Jumlah Nota"].map(ljl.format_int_id)
            st.dataframe(tampil, use_container_width=True)
            st.download_button(
                "⬇️ Unduh CSV — Top Sales Retail", ts.to_csv(index=True).encode("utf-8-sig"), "top_sales_retail.csv", "text/csv", key="jl_dl_sales",
            )

    st.divider()
    st.caption(
        "Aturan data: satu nota = CABANG + NO FAKTUR · HARGA BELI sudah total per baris "
        "(tidak dikalikan QTY) · baris kembar dihitung apa adanya · AKSESORIS dan "
        "ACCESORIES digabung jadi satu kategori."
    )


# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_pembelian, tab_penjualan = st.tabs(["📦 Dashboard Pembelian Cabang", "🧾 Dashboard Penjualan Cabang"])

with tab_pembelian:
    render_pembelian_tab()

with tab_penjualan:
    render_penjualan_tab()
