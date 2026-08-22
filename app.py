import os
import io
import streamlit as st
import pandas as pd
import numpy as np

import logic_persediaan as lp
import logic_penjualan as ljl
import logic_aksesoris as la

st.set_page_config(page_title="MFlash Dashboard Aksesoris", page_icon="flash_logo.png", layout="wide")

st.logo("flash_logo.png")

col_logo, col_judul = st.columns([1, 8])
with col_logo:
    st.image("flash_logo.png", width=90)
with col_judul:
    st.title("MFlash Dashboard Aksesoris")
    st.caption("Madinah Group Indonesia · 18 cabang service gadget")

BULAN_NAMA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}

# ---------------------------------------------------------------------------
# Sidebar — sumber data untuk KEDUA dashboard, supaya bisa dimuat sekali dan
# tab tinggal berpindah tanpa perlu unggah ulang.
# ---------------------------------------------------------------------------
st.sidebar.header("📊 Data Persediaan Aksesoris")
st.sidebar.caption("Sheet \"Daftar Barang dan Jasa\" — Excel atau CSV sepadan")
upl_persediaan = st.sidebar.file_uploader(
    "Unggah berkas persediaan", type=["xlsx", "xls", "csv"], key="upl_persediaan",
)

st.sidebar.divider()

st.sidebar.header("🧾 Data Penjualan")
st.sidebar.caption(
    "Gabungan seluruh cabang, atau rincian satu cabang saja — dipakai untuk "
    "SELURUH bagian di tab Penjualan Aksesoris (Ringkasan Cabang/Produk/Sales "
    "maupun Revenue, HPP & Katalog LUNA)."
)
upl_penjualan = st.sidebar.file_uploader(
    "Unggah berkas penjualan", type=["gz", "csv", "xlsx", "xls"], key="upl_penjualan",
)

st.sidebar.divider()
# NOTE: kontrol ambang indikator (Merah/Kuning) sementara disembunyikan dari
# sidebar atas permintaan — dipakai default tetap di kode saja (2 / 7),
# supaya fokus dashboard murni ke kontrol stok menipis tanpa perlu
# pengaturan tambahan. Bisa dimunculkan lagi kapan saja kalau dibutuhkan.
batas_merah, batas_kuning = 2, 7

# ---------------------------------------------------------------------------
# Muat data
# ---------------------------------------------------------------------------
DEFAULT_PERSEDIAAN_PATH = "Persediaan_Aksesoris_Regional.xlsx"
DEFAULT_PENJUALAN_PATH = "penjualan.csv.gz"

df_persediaan, err_persediaan = None, None
try:
    if upl_persediaan is not None:
        df_persediaan = lp.load_persediaan(upl_persediaan)
    elif os.path.exists(DEFAULT_PERSEDIAAN_PATH):
        df_persediaan = lp.load_persediaan(DEFAULT_PERSEDIAAN_PATH)
except Exception as e:
    err_persediaan = str(e)


def _dua_salinan(uploaded_file):
    """Bikin dua salinan independen dari satu berkas unggahan, supaya bisa
    dibaca dua kali (oleh dua parser berbeda) tanpa isu posisi baca habis."""
    if uploaded_file is None:
        return None, None
    data = uploaded_file.getvalue()
    b1, b2 = io.BytesIO(data), io.BytesIO(data)
    b1.name = uploaded_file.name
    b2.name = uploaded_file.name
    return b1, b2


buf_penjualan_1, buf_penjualan_2 = _dua_salinan(upl_penjualan)

# --- Sumber untuk bagian "Ringkasan Cabang, Produk & Sales" ---
df_penjualan, err_penjualan, need_cabang_name = None, None, False
raw_penjualan = None
try:
    if buf_penjualan_1 is not None:
        raw_penjualan = ljl.read_raw(buf_penjualan_1)
    elif os.path.exists(DEFAULT_PENJUALAN_PATH):
        raw_penjualan = ljl.read_raw(DEFAULT_PENJUALAN_PATH)
except Exception as e:
    err_penjualan = str(e)

if raw_penjualan is not None:
    if "CABANG" in raw_penjualan.columns:
        df_penjualan = ljl.finalize_data(raw_penjualan)
    else:
        need_cabang_name = True

# --- Sumber untuk bagian "Revenue, HPP & Katalog LUNA" — berkas yang SAMA ---
raw_aksesoris, err_aksesoris = None, None
try:
    if buf_penjualan_2 is not None:
        raw_aksesoris = la.read_raw(buf_penjualan_2)
    elif os.path.exists(DEFAULT_PENJUALAN_PATH):
        raw_aksesoris = la.read_raw(DEFAULT_PENJUALAN_PATH)
except Exception as e:
    err_aksesoris = str(e)


# ---------------------------------------------------------------------------
# TAB 1 — Dashboard Stok Semua Cabang (fokus buffer stok LUNA)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# TAB 1 — Dashboard Persediaan Aksesoris (LUNA vs Selain LUNA)
# ---------------------------------------------------------------------------
def _render_kelompok_stok(dff_kelompok, label_kelompok, key_prefix, batas_produk_tampil=None, tampilkan_heatmap=False):
    """Render indikator + ringkasan cabang/produk + detail + nilai persediaan
    untuk satu kelompok produk (LUNA atau selain LUNA). Mengembalikan tabel
    indikator supaya bisa dipakai lagi di bagian Analisa."""
    ind = lp.indikator_stok_luna(dff_kelompok, batas_merah=batas_merah, batas_kuning=batas_kuning)

    if ind.empty:
        st.info(f"Tidak ada data {label_kelompok} pada filter ini.")
        return ind

    total = len(ind)
    n_merah = (ind["Indikator"] == lp.MERAH).sum()
    n_kuning = (ind["Indikator"] == lp.KUNING).sum()
    n_hijau = (ind["Indikator"] == lp.HIJAU).sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Merah", lp.format_int_id(n_merah), lp.format_percent_id(n_merah / total * 100 if total else 0))
    c2.metric("🟡 Kuning", lp.format_int_id(n_kuning), lp.format_percent_id(n_kuning / total * 100 if total else 0))
    c3.metric("🟢 Hijau", lp.format_int_id(n_hijau), lp.format_percent_id(n_hijau / total * 100 if total else 0))

    rc_awal = lp.ringkasan_indikator_cabang(ind)
    prioritas = lp.cabang_prioritas(rc_awal, n=5)
    if not prioritas.empty:
        st.markdown("##### 🚨 Cabang Paling Perlu Perhatian")
        badge_cols = st.columns(len(prioritas))
        for col, (_, row) in zip(badge_cols, prioritas.iterrows()):
            with col:
                st.error(
                    f"**{row['Cabang']}**\n\n"
                    f"{lp.format_percent_id(row['Porsi Merah (%)'])} Merah\n\n"
                    f"({int(row['Merah'])} item)"
                )

    st.subheader("Ringkasan per Cabang")
    st.caption(
        "Diurutkan dari porsi Merah TERTINGGI — cabang paling perlu segera direstock ada di "
        "paling atas. Warna latar kolom \"Porsi Merah (%)\" makin pekat = makin kritis."
    )
    rc = lp.ringkasan_indikator_cabang(ind)
    st.bar_chart(rc.set_index("Cabang")[["Merah", "Kuning", "Hijau"]])
    rc_tampil = rc.drop(columns=["Jumlah SKU LUNA"])
    styled_rc = lp.styler_gradasi_merah(rc_tampil).format({"Porsi Merah (%)": lp.format_percent_id})
    st.dataframe(styled_rc, use_container_width=True, height=420)
    st.download_button(
        f"⬇️ Unduh CSV — Ringkasan Indikator per Cabang ({label_kelompok})", rc.to_csv(index=False).encode("utf-8-sig"),
        f"ringkasan_indikator_{key_prefix}_cabang.csv", "text/csv", key=f"{key_prefix}_dl_ringkasan_cabang",
    )

    if tampilkan_heatmap:
        st.subheader("🗺️ Peta Stok — Cabang × Produk")
        st.caption(
            "Sekali lihat langsung kelihatan pola di seluruh jaringan — warna sel mengikuti "
            "indikator (🔴🟡🟢), angka di dalamnya menunjukkan jumlah stok. Sel abu-abu \"-\" "
            "berarti produk itu tidak tercatat sama sekali di cabang tsb (bukan berarti stoknya 0)."
        )
        pivot_stok, pivot_ind = lp.pivot_heatmap_stok(ind)
        if pivot_stok.empty:
            st.info("Tidak ada data untuk peta stok pada filter ini.")
        else:
            st.dataframe(lp.styler_heatmap(pivot_stok, pivot_ind), use_container_width=True, height=520)

    rp_full = lp.ringkasan_indikator_produk(ind)
    if batas_produk_tampil is not None and len(rp_full) > batas_produk_tampil:
        st.subheader(f"Ringkasan per Produk (Top {batas_produk_tampil} dari {lp.format_int_id(len(rp_full))} produk unik)")
        top_n_produk = st.slider(
            "Tampilkan berapa produk teratas (diurutkan porsi Merah tertinggi)",
            10, min(200, len(rp_full)), batas_produk_tampil, key=f"{key_prefix}_top_n_produk",
        )
        rp = rp_full.head(top_n_produk)
        st.caption("Tabel di layar dibatasi supaya tetap ringan — unduhan CSV berisi SEMUA produk.")
    else:
        st.subheader("Ringkasan per Produk")
        rp = rp_full
    st.caption(
        "Produk yang Merah di BANYAK cabang sekaligus kemungkinan masalah pasokan dari "
        "pemasok, bukan cuma masalah satu cabang — diurutkan dari porsi Merah tertinggi."
    )
    tampil_rp = lp.styler_gradasi_merah(rp).format({"Porsi Merah (%)": lp.format_percent_id})
    st.dataframe(tampil_rp, use_container_width=True, height=380)
    st.download_button(
        f"⬇️ Unduh CSV — Ringkasan Indikator per Produk ({label_kelompok}, semua {lp.format_int_id(len(rp_full))} produk)",
        rp_full.to_csv(index=False).encode("utf-8-sig"),
        f"ringkasan_indikator_{key_prefix}_produk.csv", "text/csv", key=f"{key_prefix}_dl_ringkasan_produk",
    )

    st.subheader("Detail per SKU × Cabang")
    filter_indikator = st.multiselect(
        "Filter indikator", [lp.MERAH, lp.KUNING, lp.HIJAU],
        default=[lp.MERAH, lp.KUNING, lp.HIJAU], key=f"{key_prefix}_filter_indikator",
    )
    cari_produk = st.text_input("Cari nama produk", key=f"{key_prefix}_cari_produk")

    detail = ind[ind["Indikator"].isin(filter_indikator)] if filter_indikator else ind.iloc[0:0]
    if cari_produk:
        detail = detail[detail["Nama Barang"].str.upper().str.contains(cari_produk.upper(), na=False)]

    if detail.empty:
        st.info("Tidak ada produk yang cocok dengan filter indikator/pencarian ini.")
    else:
        tampil_detail = detail.copy()
        tampil_detail["Nilai Stok"] = detail["Nilai Stok"].map(lp.format_rupiah_id)
        st.dataframe(tampil_detail, use_container_width=True, height=420)
        st.download_button(
            f"⬇️ Unduh CSV — Detail Indikator Stok ({label_kelompok})", detail.to_csv(index=False).encode("utf-8-sig"),
            f"detail_indikator_{key_prefix}.csv", "text/csv", key=f"{key_prefix}_dl_detail",
        )

    st.divider()
    st.subheader(f"💼 Nilai Persediaan {label_kelompok} per Cabang")
    nv = lp.nilai_persediaan_cabang(dff_kelompok)
    if nv.empty:
        st.info("Tidak ada data pada filter ini.")
    else:
        st.bar_chart(nv.set_index("Cabang")["Nilai Persediaan"])
        tampil_nv = nv.drop(columns=["Jumlah SKU"]).copy()
        tampil_nv["Total Qty"] = tampil_nv["Total Qty"].map(lp.format_int_id)
        tampil_nv["Nilai Persediaan"] = tampil_nv["Nilai Persediaan"].map(lp.format_rupiah_id)
        st.dataframe(tampil_nv, use_container_width=True, height=420)
        st.download_button(
            f"⬇️ Unduh CSV — Nilai Persediaan {label_kelompok} per Cabang", nv.to_csv(index=False).encode("utf-8-sig"),
            f"nilai_persediaan_{key_prefix}_cabang.csv", "text/csv", key=f"{key_prefix}_dl_nilai",
        )

    return ind


def _catatan_kelompok(ind, label_kelompok):
    """Bikin 3 baris catatan analisa untuk satu kelompok (LUNA / selain LUNA)."""
    catatan = []
    if ind.empty:
        return catatan
    rc2 = lp.ringkasan_indikator_cabang(ind)
    if not rc2.empty:
        prioritas = rc2.iloc[0]
        catatan.append(
            f"[{label_kelompok}] Cabang **{prioritas['Cabang']}** paling perlu segera direstock — "
            f"{lp.format_percent_id(prioritas['Porsi Merah (%)'])} dari item yang dipantau berstatus "
            f"🔴 Merah ({int(prioritas['Merah'])} item)."
        )
        aman = rc2.sort_values("Porsi Merah (%)").iloc[0]
        catatan.append(
            f"[{label_kelompok}] Cabang **{aman['Cabang']}** paling aman stoknya — hanya "
            f"{lp.format_percent_id(aman['Porsi Merah (%)'])} SKU berstatus Merah."
        )
    n_merah_total = (ind["Indikator"] == lp.MERAH).sum()
    if n_merah_total > 0:
        catatan.append(
            f"[{label_kelompok}] Total ada **{lp.format_int_id(n_merah_total)}** kombinasi SKU×cabang "
            "berstatus 🔴 Merah di seluruh jaringan."
        )
    return catatan


def render_persediaan_tab():
    if err_persediaan:
        st.error(f"Gagal membaca berkas persediaan: {err_persediaan}")
        return
    if df_persediaan is None:
        st.info(
            "Belum ada data. Unggah berkas Excel/CSV **Persediaan Aksesoris Regional** "
            "(sheet **Daftar Barang dan Jasa**) lewat panel kiri, atau taruh berkasnya "
            "di root repo sebelum deploy."
        )
        return

    st.subheader("Filter — Data Persediaan")
    cabang_opsi = sorted(df_persediaan["Cabang"].dropna().unique().tolist())
    sel_cabang = st.multiselect("Cabang", cabang_opsi, default=cabang_opsi, key="pd_cabang")

    dasar = lp.apply_filters(df_persediaan, cabang=sel_cabang if sel_cabang else None, hanya_aksesoris=True, filter_luna=None)
    if dasar.empty:
        st.warning("Tidak ada data untuk kombinasi filter ini. Coba longgarkan pilihan cabang di atas.")
        return

    dff_luna = dasar[dasar["ADALAH_LUNA"]]
    dff_non_luna = dasar[~dasar["ADALAH_LUNA"]]

    st.caption(
        f"Menampilkan {len(dasar):,}".replace(",", ".") + " baris persediaan kategori aksesoris — "
        f"{len(dff_luna):,}".replace(",", ".") + " baris LUNA, "
        f"{len(dff_non_luna):,}".replace(",", ".") + " baris selain LUNA."
    )
    st.divider()

    # -----------------------------------------------------------------
    # 1. Stok Persediaan — Nama Barang LUNA
    # -----------------------------------------------------------------
    st.header("🔵 1. Stok Persediaan — Nama Barang LUNA")
    st.caption(
        "Nama barang mengandung kata \"LUNA\". Indikator dari jumlah stok aktual — "
        "🔴 Merah = kritis/habis, 🟡 Kuning = menipis, 🟢 Hijau = aman. "
        "Stok negatif (anomali sistem) otomatis masuk kategori Merah."
    )
    ind_luna = _render_kelompok_stok(dff_luna, "LUNA", "luna", tampilkan_heatmap=True)

    st.divider()

    # -----------------------------------------------------------------
    # 2. Stok Persediaan — Nama Barang Selain LUNA
    # -----------------------------------------------------------------
    st.header("⚪ 2. Stok Persediaan — Nama Barang Selain LUNA")
    st.caption(
        "Seluruh brand aksesoris lain di luar LUNA — sebagai pembanding. "
        "Ambang indikator warna sama seperti bagian LUNA di atas."
    )
    ind_non_luna = _render_kelompok_stok(dff_non_luna, "Selain LUNA", "nonluna", batas_produk_tampil=30)

    st.divider()

    # -----------------------------------------------------------------
    # Analisa & tindak lanjut (gabungan kedua kelompok)
    # -----------------------------------------------------------------
    st.header("📌 Analisa & Tindak Lanjut")
    catatan = []

    if not ind_luna.empty and not ind_non_luna.empty:
        porsi_merah_luna = (ind_luna["Indikator"] == lp.MERAH).mean() * 100
        porsi_merah_non = (ind_non_luna["Indikator"] == lp.MERAH).mean() * 100
        if porsi_merah_luna < porsi_merah_non:
            catatan.append(
                f"Secara keseluruhan, stok **LUNA** ({lp.format_percent_id(porsi_merah_luna)} Merah) lebih "
                f"terjaga dibanding brand **selain LUNA** ({lp.format_percent_id(porsi_merah_non)} Merah) — "
                "wajar mengingat LUNA adalah brand yang ditarget secara khusus."
            )
        else:
            catatan.append(
                f"Porsi Merah LUNA ({lp.format_percent_id(porsi_merah_luna)}) justru lebih tinggi atau setara "
                f"dengan brand selain LUNA ({lp.format_percent_id(porsi_merah_non)}) — perlu perhatian ekstra "
                "mengingat LUNA adalah brand yang wajib disetok semua cabang."
            )

    catatan += _catatan_kelompok(ind_luna, "LUNA")
    catatan += _catatan_kelompok(ind_non_luna, "Selain LUNA")

    if not catatan:
        catatan.append("Tidak ada data untuk dianalisa pada filter saat ini.")

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
        st.session_state["nama_cabang_bersama"] = nama_cabang.strip()

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
        st.error(f"Gagal membaca berkas penjualan: {err_aksesoris}")
        return
    if raw_aksesoris is None:
        st.info(
            "Belum ada data. Unggah berkas penjualan (Excel/CSV) lewat panel kiri di "
            "bagian \"🧾 Data Penjualan\" — berkas yang sama dipakai untuk bagian ini juga."
        )
        return

    df = None
    if "CABANG" in raw_aksesoris.columns:
        df = la.finalize_data(raw_aksesoris)
    else:
        nama_bersama = st.session_state.get("nama_cabang_bersama")
        if nama_bersama:
            df = la.finalize_data(raw_aksesoris, cabang_default=nama_bersama)
        else:
            st.info(
                "Berkas ini tidak punya kolom Cabang (rincian satu cabang saja). "
                "Masukkan nama cabangnya dulu di bagian **\"🧾 Ringkasan Cabang, Produk & Sales\"** "
                "di atas — nama itu akan dipakai juga di bagian ini."
            )
            return

    if df is None:
        return

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
    # 3b. Simulasi Insentif Penjualan Aksesoris
    # -----------------------------------------------------------------
    st.header("💸 Simulasi Insentif Penjualan Aksesoris")
    st.caption(
        "Estimasi Take Home Pay (THP) sales retail berdasarkan target penjualan aksesoris "
        "harian. Kolom **\"Penjualan Harian\"** bisa diedit langsung — baris bisa ditambah/"
        "dihapus lewat tombol +/− di pojok tabel."
    )

    with st.expander("⚙️ Asumsi Simulasi (bisa diubah)", expanded=True):
        p1, p2, p3 = st.columns(3)
        with p1:
            gp_persen = st.number_input("Asumsi Gross Profit (%)", min_value=0.0, max_value=100.0, value=40.0, step=1.0, key="sim_gp_persen")
            hari_kerja = st.number_input("Hari kerja per bulan", min_value=1, max_value=31, value=26, step=1, key="sim_hari_kerja")
        with p2:
            thp_min = st.number_input("THP Minimum (Rp)", min_value=0, value=5_000_000, step=500_000, format="%d", key="sim_thp_min")
            thp_max = st.number_input("THP Maksimum (Rp)", min_value=0, value=8_000_000, step=500_000, format="%d", key="sim_thp_max")
        with p3:
            harian_min = st.number_input("Penjualan Harian Minimum (Rp)", min_value=0, value=500_000, step=50_000, format="%d", key="sim_harian_min")
            harian_max = st.number_input("Penjualan Harian Maksimum (Rp)", min_value=0, value=2_000_000, step=50_000, format="%d", key="sim_harian_max")
        jumlah_baris = st.slider("Jumlah baris skenario default", 3, 15, 7, key="sim_jumlah_baris")

    if thp_min > thp_max:
        st.error("THP Minimum harus lebih kecil atau sama dengan THP Maksimum.")
    elif harian_min > harian_max:
        st.error("Penjualan Harian Minimum harus lebih kecil atau sama dengan Maksimum.")
    else:
        default_harian = np.linspace(harian_min, harian_max, jumlah_baris).round(-3)
        seed_df = pd.DataFrame({"Penjualan Harian": default_harian})

        edited = st.data_editor(
            seed_df, num_rows="dynamic", use_container_width=True, key="sim_editor",
            column_config={
                "Penjualan Harian": st.column_config.NumberColumn(
                    "Penjualan Harian (Rp)", min_value=0, step=50_000, format="%d",
                )
            },
        )

        harian_valid = edited["Penjualan Harian"].dropna()
        harian_valid = harian_valid[harian_valid > 0]

        if harian_valid.empty:
            st.info("Isi minimal satu baris \"Penjualan Harian\" di tabel atas untuk melihat hasil simulasi.")
        else:
            hasil = la.simulasi_insentif(
                harian_valid.tolist(), gp_persen=gp_persen, hari_kerja=int(hari_kerja),
                harian_min=harian_min, harian_max=harian_max, thp_min=thp_min, thp_max=thp_max,
            )
            gp_col = f"Gross Profit Bulanan ({gp_persen:.0f}%)"
            tampil_hasil = hasil.copy()
            tampil_hasil["Penjualan Harian"] = hasil["Penjualan Harian"].map(la.format_rupiah_id)
            tampil_hasil["Penjualan Bulanan"] = hasil["Penjualan Bulanan"].map(la.format_rupiah_id)
            tampil_hasil[gp_col] = hasil[gp_col].map(la.format_rupiah_id)
            tampil_hasil["Estimasi THP"] = hasil["Estimasi THP"].map(la.format_rupiah_id)
            tampil_hasil["THP thd Gross Profit (%)"] = hasil["THP thd Gross Profit (%)"].map(la.format_percent_id)
            st.dataframe(tampil_hasil, use_container_width=True, height=min(80 + 38 * len(hasil), 420))

            rasio_maks = hasil["THP thd Gross Profit (%)"].max()
            rasio_min = hasil["THP thd Gross Profit (%)"].min()
            st.caption(
                f"Kolom **\"THP thd Gross Profit (%)\"** menunjukkan seberapa besar porsi Gross Profit "
                f"kategori aksesoris yang habis KALAU insentif ini dianggap dibiayai murni dari GP "
                f"aksesoris saja — berkisar {la.format_percent_id(rasio_min)} sampai {la.format_percent_id(rasio_maks)} "
                "pada tabel di atas."
            )
            if rasio_maks > 70:
                st.warning(
                    f"⚠️ Di penjualan harian paling rendah, insentif setara **{la.format_percent_id(rasio_maks)}** "
                    "dari Gross Profit aksesoris — kalau THP memang murni dibiayai dari situ, hampir tidak "
                    "menyisakan margin untuk cabang di level penjualan terendah ini. Kemungkinan THP perlu "
                    "sebagian ditopang dari sumber lain (gaji pokok, komisi kategori lain), bukan cuma GP "
                    "aksesoris — sesuaikan asumsi di atas kalau perlu."
                )

            st.download_button(
                "⬇️ Unduh CSV — Simulasi Insentif", hasil.to_csv(index=False).encode("utf-8-sig"),
                "simulasi_insentif_aksesoris.csv", "text/csv", key="ak_dl_simulasi",
            )

    st.divider()

    # -----------------------------------------------------------------
    # 3c. Target Pencapaian Penjualan LUNA
    # -----------------------------------------------------------------
    st.header("🎯 Target Pencapaian Penjualan Aksesoris LUNA")

    t1, t2, t3 = st.columns(3)
    with t1:
        target_rp = st.number_input("Target (Rp)", min_value=0, value=2_000_000_000, step=100_000_000, format="%d", key="target_luna_rp")
    with t2:
        tanggal_mulai_target = st.date_input("Mulai program", value=pd.Timestamp("2026-08-01"), key="target_luna_mulai")
    with t3:
        durasi_bulan_target = st.number_input("Durasi (bulan)", min_value=1, max_value=60, value=12, step=1, key="target_luna_durasi")

    tprog = la.target_penjualan_luna(
        df, target=target_rp, tanggal_mulai=tanggal_mulai_target, durasi_bulan=int(durasi_bulan_target),
    )

    st.caption(
        f"Periode program: {tprog['tanggal_mulai'].strftime('%d %b %Y')} – "
        f"{tprog['tanggal_selesai'].strftime('%d %b %Y')} ({tprog['total_hari_program']} hari). "
        "Nama barang diidentifikasi mengandung kata \"LUNA\"."
    )

    if tprog["hari_berjalan"] == 0:
        st.info("Data faktur belum masuk periode program ini, atau program belum dimulai — indikator belum bisa dihitung.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tercapai", la.format_rupiah_id(tprog["tercapai"]))
        c2.metric("Target s/d Hari Ini", la.format_rupiah_id(tprog["target_sampai_hari_ini"]))
        c3.metric("% Pencapaian (vs target s/d hari ini)", la.format_percent_id(tprog["pct_pencapaian"]))
        c4.metric("% dari Target Penuh", la.format_percent_id(tprog["pct_dari_target_penuh"]))

        st.progress(min(tprog["pct_pencapaian"] / 100, 1.0) if tprog["pct_pencapaian"] else 0)

        st.caption(
            f"Tanggal acuan: **{tprog['tgl_acuan'].strftime('%d %b %Y')}** (tanggal faktur terakhir pada "
            f"data, bukan tanggal hari ini) — hari ke-{tprog['hari_berjalan']} dari "
            f"{tprog['total_hari_program']} hari program, sisa {la.format_int_id(tprog['sisa_hari'])} hari. "
            f"{la.format_int_id(tprog['jumlah_transaksi'])} baris transaksi LUNA tercatat dalam periode ini."
        )

        if tprog["pct_pencapaian"] < 80:
            st.warning(
                f"⚠️ Pencapaian baru **{la.format_percent_id(tprog['pct_pencapaian'])}** dari target yang "
                "seharusnya sudah dicapai sampai hari ini — di bawah jalur target. Perlu dorongan tambahan "
                "kalau ingin mengejar Rp " + la.format_int_id(tprog["target"]) + f" dalam {tprog['total_hari_program']} hari."
            )
        else:
            st.success(
                f"✅ Pencapaian **{la.format_percent_id(tprog['pct_pencapaian'])}** dari target yang "
                "seharusnya — di jalur yang baik."
            )

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
                "(lihat tab Dashboard Persediaan Aksesoris untuk cek ketersediaan stok LUNA di cabang ini)."
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
tab_persediaan, tab_penjualan_aksesoris = st.tabs([
    "📊 Dashboard Persediaan Aksesoris", "🧾 Dashboard Penjualan Aksesoris",
])

with tab_persediaan:
    render_persediaan_tab()

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
