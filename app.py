import os
import io
import streamlit as st
import pandas as pd
import numpy as np

import logic_persediaan as lp
import logic_penjualan as ljl
import logic_aksesoris as la

st.set_page_config(page_title="MFlash Dashboard Gadget dan Aksesoris", page_icon="flash_logo.png", layout="wide")

st.logo("flash_logo.png")

col_logo, col_judul = st.columns([1, 8])
with col_logo:
    st.image("flash_logo.png", width=90)
with col_judul:
    st.title("MFlash Dashboard Gadget dan Aksesoris")
    st.caption("Madinah Group Indonesia · 18 cabang service gadget")

BULAN_NAMA = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}

# ---------------------------------------------------------------------------
# Sidebar — SATU TEMPAT untuk unggah data persediaan & penjualan, dipakai
# bersama oleh SELURUH tab (Persediaan Aksesoris, Persediaan Parfum,
# Penjualan Aksesoris) supaya tidak perlu unggah ulang saat pindah tab.
# ---------------------------------------------------------------------------
st.sidebar.header("📁 Upload Data")
st.sidebar.caption(
    "Kedua berkas ini dipakai bersama oleh SEMUA tab di bawah — cukup unggah "
    "sekali di sini."
)

st.sidebar.markdown("**📊 Data Persediaan**")
st.sidebar.caption(
    "Sheet \"Daftar Barang dan Jasa\" — boleh berkas khusus aksesoris, atau berkas "
    "SEMUA kategori barang (dipakai untuk tab Persediaan Aksesoris & Persediaan Parfum)."
)
upl_persediaan = st.sidebar.file_uploader(
    "Unggah berkas persediaan", type=["xlsx", "xls", "csv"], key="upl_persediaan",
)

st.sidebar.markdown("**🧾 Data Penjualan**")
st.sidebar.caption(
    "Gabungan seluruh cabang, atau rincian satu cabang saja — boleh berkas khusus "
    "aksesoris, atau berkas SEMUA kategori barang (dipakai untuk tab Persediaan "
    "Aksesoris/Parfum bagian \"Produk Paling Diminati\", maupun kedua bagian di tab "
    "Penjualan Aksesoris)."
)
upl_penjualan = st.sidebar.file_uploader(
    "Unggah berkas penjualan", type=["gz", "csv", "xlsx", "xls"], key="upl_penjualan",
)

st.sidebar.divider()
# NOTE: kontrol ambang indikator (Merah/Kuning) sementara disembunyikan dari
# sidebar atas permintaan — dipakai default tetap di kode saja, supaya
# fokus dashboard murni ke kontrol stok menipis tanpa perlu pengaturan
# tambahan. Bisa dimunculkan lagi kapan saja kalau dibutuhkan.
# Merah: stok <= 25 · Kuning: stok 26-99 · Hijau: stok >= 100
batas_merah, batas_kuning = 25, 99

# ---------------------------------------------------------------------------
# Muat data
# ---------------------------------------------------------------------------
# Dicari berurutan — file PERTAMA yang ketemu di root repo yang dipakai.
# Boleh xlsx ATAU csv/csv.gz, tidak perlu nama & format persis — jadi Anda
# tinggal commit berkas datanya ke GitHub dengan salah satu nama ini, tidak
# perlu upload manual, dan otomatis kelihatan oleh SEMUA orang yang buka
# aplikasi ini (tidak per-sesi/per-orang seperti tombol upload).
DEFAULT_PERSEDIAAN_CANDIDATES = [
    "Persediaan_Aksesoris_Regional.xlsx",
    "persediaan.csv.gz",
    "persediaan.csv",
    "Persediaan_Barang_Regional.csv",
]
DEFAULT_PENJUALAN_CANDIDATES = [
    "penjualan.csv.gz",
    "penjualan.csv",
    "Penjualan_Aksesoris_Regional.xlsx",
    "Penjualan_Regional.csv",
]


def _cari_file_default(kandidat: list[str]) -> str | None:
    for nama in kandidat:
        if os.path.exists(nama):
            return nama
    return None


DEFAULT_PERSEDIAAN_PATH = _cari_file_default(DEFAULT_PERSEDIAAN_CANDIDATES)
DEFAULT_PENJUALAN_PATH = _cari_file_default(DEFAULT_PENJUALAN_CANDIDATES)

df_persediaan, err_persediaan = None, None
try:
    if upl_persediaan is not None:
        df_persediaan = lp.load_persediaan(upl_persediaan)
    elif DEFAULT_PERSEDIAAN_PATH:
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
    elif DEFAULT_PENJUALAN_PATH:
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
    elif DEFAULT_PENJUALAN_PATH:
        raw_aksesoris = la.read_raw(DEFAULT_PENJUALAN_PATH)
except Exception as e:
    err_aksesoris = str(e)


# ---------------------------------------------------------------------------
# Ringkasan Eksekutif — versi ringkas gaya kartu di paling atas halaman,
# merangkum data yang detailnya ada di ketiga dashboard di bawah. Memakai
# fungsi logic_aksesoris.py yang sama (omzet_per_kelompok, kontribusi_cabang_
# gabungan, analisa_bundling_brand, target_penjualan_brand) — bukan hitungan
# terpisah, supaya angkanya selalu konsisten dengan bagian detail di bawahnya.
# ---------------------------------------------------------------------------
def render_ringkasan_eksekutif():
    st.markdown("## 📌 Ringkasan Eksekutif")

    if raw_aksesoris is None:
        st.info("Unggah data Persediaan & Penjualan di panel kiri untuk melihat ringkasan ini.")
        return

    df_re = None
    if "CABANG" in raw_aksesoris.columns:
        df_re = la.finalize_data(raw_aksesoris)
    else:
        nama_bersama_re = st.session_state.get("nama_cabang_bersama")
        if nama_bersama_re:
            df_re = la.finalize_data(raw_aksesoris, cabang_default=nama_bersama_re)
        else:
            st.info(
                "Berkas penjualan rincian satu cabang saja — isi dulu nama cabangnya di bagian "
                "\"Dashboard Penjualan Aksesoris\" di bawah, ringkasan ini akan otomatis terisi."
            )
            return

    df_aks_re = la.hanya_kategori(df_re, "AKSESORIS")
    df_parfum_re = la.hanya_kategori(df_re, "PARFUM")

    aks_stok_re = lp.apply_filters(df_persediaan, hanya_aksesoris=True, filter_luna=None) if df_persediaan is not None else pd.DataFrame()
    parfum_stok_re = lp.apply_filters(df_persediaan, kategori="PARFUM", filter_luna=None) if df_persediaan is not None else pd.DataFrame()

    opk_re = la.omzet_per_kelompok(df_aks_re, df_parfum_re, keyword_brand="LUNA")
    kc_re = la.kontribusi_cabang_gabungan(df_aks_re, df_parfum_re)

    # Nilai stok per kelompok (LUNA / Selain LUNA / Parfum) — sumber sama
    # dengan bagian "Nilai Persediaan" di Dashboard Persediaan Aksesoris & Parfum.
    nilai_stok_kelompok = {}
    if not aks_stok_re.empty:
        nilai_stok_kelompok["Aksesoris LUNA"] = aks_stok_re[aks_stok_re["ADALAH_LUNA"]]["Nilai Total"].sum()
        nilai_stok_kelompok["Aksesoris Selain LUNA"] = aks_stok_re[~aks_stok_re["ADALAH_LUNA"]]["Nilai Total"].sum()
    if not parfum_stok_re.empty:
        nilai_stok_kelompok["Parfum"] = parfum_stok_re["Nilai Total"].sum()

    c1, c2, c3 = st.columns(3)
    if not opk_re.empty:
        for col, (_, row) in zip([c1, c2, c3], opk_re.iterrows()):
            with col:
                margin_pct = (row["Laba"] / row["Omzet"] * 100) if row["Omzet"] else 0
                st.metric(row["Kelompok"], la.format_rupiah_id(row["Omzet"]), f"Margin {la.format_percent_id(margin_pct)}")
                st.caption(f"{la.format_int_id(row['Jumlah Item Terjual'])} pcs terjual")

    if nilai_stok_kelompok:
        s1, s2, s3 = st.columns(3)
        for col, kelompok in zip([s1, s2, s3], ["Aksesoris LUNA", "Aksesoris Selain LUNA", "Parfum"]):
            with col:
                nilai = nilai_stok_kelompok.get(kelompok)
                if nilai is not None:
                    st.metric(f"Nilai Stok — {kelompok}", la.format_rupiah_id(nilai))

    st.markdown("&nbsp;", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.caption("Omzet per kelompok")
        if not opk_re.empty:
            st.bar_chart(opk_re.set_index("Kelompok")["Omzet"], height=220)
    with g2:
        st.caption("Kontribusi cabang (terendah → tertinggi)")
        if not kc_re.empty:
            st.bar_chart(kc_re.set_index("Cabang")["Total Omzet"], height=220)

    b1, b2 = st.columns(2)
    with b1:
        st.caption("Bundling LUNA pada transaksi Service")
        bund_re, _ = la.analisa_bundling_brand(
            df_aks_re[df_aks_re["NAMA BARANG"].astype(str).str.upper().str.contains("LUNA", na=False)],
            df_re, keyword="LUNA",
        )
        if bund_re["jumlah_nota_service"]:
            m1, m2, m3 = st.columns(3)
            m1.metric("Pakai LUNA", la.format_percent_id(bund_re["pct_bundling_brand"]))
            m2.metric("Brand lain", la.format_percent_id(100 - bund_re["pct_bundling_brand"] - bund_re["pct_tanpa_aksesoris"]))
            m3.metric("Tanpa aksesoris", la.format_percent_id(bund_re["pct_tanpa_aksesoris"]))
    with b2:
        st.caption("Target pencapaian")
        target_luna_re = la.target_penjualan_luna(df_aks_re, target=2_000_000_000, tanggal_mulai="2026-08-20", durasi_bulan=12)
        target_umair_re = la.target_penjualan_brand(df_parfum_re, keyword="UMAIR", target=100_000_000, tanggal_mulai="2026-01-01", durasi_bulan=6)
        st.caption(f"LUNA · Rp 2 M / 12 bln — {la.format_percent_id(target_luna_re['pct_pencapaian'])}")
        st.progress(min(target_luna_re["pct_pencapaian"] / 100, 1.0) if target_luna_re["pct_pencapaian"] else 0)
        st.caption(f"UMAIR · Rp 100 jt / 6 bln — {la.format_percent_id(target_umair_re['pct_pencapaian'])}")
        st.progress(min(target_umair_re["pct_pencapaian"] / 100, 1.0) if target_umair_re["pct_pencapaian"] else 0)

    st.caption(
        "Detail lengkap tiap angka di atas ada di bagian \"🔍 Analisa Mendalam\" dan \"🎯 Target Pencapaian\" "
        "pada Dashboard Penjualan Aksesoris di bawah."
    )


# ---------------------------------------------------------------------------
# TAB 1 — Dashboard Stok Semua Cabang (fokus buffer stok LUNA)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# TAB 1 — Dashboard Persediaan Aksesoris (versi ringkas, mudah dikontrol)
# ---------------------------------------------------------------------------

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
    # 1. Nilai Persediaan Aksesoris — LUNA vs Selain LUNA
    # -----------------------------------------------------------------
    st.header("💰 1. Nilai Persediaan Aksesoris — LUNA vs Selain LUNA")

    nv_banding = lp.nilai_persediaan_perbandingan(dff_luna, dff_non_luna)
    if nv_banding.empty:
        st.info("Tidak ada data pada filter ini.")
    else:
        total_luna = nv_banding["Nilai LUNA"].sum()
        total_non = nv_banding["Nilai Selain LUNA"].sum()
        total_semua = total_luna + total_non
        c1, c2, c3 = st.columns(3)
        c1.metric("Nilai Persediaan LUNA", lp.format_rupiah_id(total_luna), lp.format_percent_id(total_luna / total_semua * 100 if total_semua else 0) + " dari total")
        c2.metric("Nilai Persediaan Selain LUNA", lp.format_rupiah_id(total_non), lp.format_percent_id(total_non / total_semua * 100 if total_semua else 0) + " dari total")
        c3.metric("Total Nilai Persediaan", lp.format_rupiah_id(total_semua))

        st.bar_chart(nv_banding.set_index("Cabang")[["Nilai LUNA", "Nilai Selain LUNA"]])

        tampil_nv = nv_banding.copy()
        tampil_nv["Nilai LUNA"] = nv_banding["Nilai LUNA"].map(lp.format_rupiah_id)
        tampil_nv["Nilai Selain LUNA"] = nv_banding["Nilai Selain LUNA"].map(lp.format_rupiah_id)
        tampil_nv["Total Nilai"] = nv_banding["Total Nilai"].map(lp.format_rupiah_id)
        tampil_nv["Porsi LUNA (%)"] = nv_banding["Porsi LUNA (%)"].map(lp.format_percent_id)
        st.dataframe(tampil_nv, use_container_width=True, height=420)
        st.download_button(
            "⬇️ Unduh CSV — Nilai Persediaan LUNA vs Selain LUNA", nv_banding.to_csv(index=False).encode("utf-8-sig"),
            "nilai_persediaan_luna_vs_selain.csv", "text/csv", key="pd_dl_nilai_banding",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 2 & 3. Produk Favorit per Cabang + Kebutuhan Konsumen Belum Terpenuhi
    # -----------------------------------------------------------------
    st.header("🏆 2. Produk Paling Diminati per Cabang (Wajib Distok)")
    st.caption(
        "Diranking dari **jumlah terjual** (bukan indikator warna) — sumbernya data penjualan "
        "aksesoris, disandingkan dengan stok saat ini. Butuh data di panel kiri bagian "
        "\"🧾 Data Penjualan\" — kalau berkasnya rincian satu cabang saja, isi dulu nama "
        "cabangnya di tab **Dashboard Penjualan Aksesoris** (bagian atas), nama itu otomatis "
        "dipakai juga di sini."
    )

    mode_tampilan = st.radio(
        "Tampilan", ["Per Cabang", "Semua Cabang (Gabungan)"], horizontal=True, key="pd_mode_tampilan",
        help="\"Semua Cabang\" menjumlahkan qty terjual, potensi omzet & laba lintas cabang — "
             "untuk melihat produk mana yang paling mendesak dibenahi secara jaringan, bukan per cabang.",
    )

    df_jual_stok = None
    if raw_aksesoris is None:
        st.info("Data penjualan belum diunggah — bagian ini butuh data penjualan untuk tahu produk mana yang paling laku.")
    elif "CABANG" in raw_aksesoris.columns:
        df_jual_stok = la.hanya_kategori(la.finalize_data(raw_aksesoris), "AKSESORIS")
    else:
        nama_bersama = st.session_state.get("nama_cabang_bersama")
        if nama_bersama:
            df_jual_stok = la.hanya_kategori(la.finalize_data(raw_aksesoris, cabang_default=nama_bersama), "AKSESORIS")
        else:
            st.info(
                "Berkas penjualan ini rincian satu cabang saja (tanpa kolom Cabang). Isi dulu "
                "nama cabangnya di tab **Dashboard Penjualan Aksesoris** (bagian "
                "\"Ringkasan Cabang, Produk & Sales\"), baru bagian ini akan terisi."
            )

    produk_favorit = pd.DataFrame()

    if df_jual_stok is not None and mode_tampilan == "Per Cabang":
        top_n_favorit = st.slider("Top berapa produk per cabang", 3, 10, 5, key="pd_top_n_favorit")
        produk_favorit_semua = lp.produk_favorit_per_cabang(df_jual_stok, dasar, top_n=top_n_favorit)

        if produk_favorit_semua.empty:
            st.info("Tidak ada data penjualan aksesoris pada filter cabang saat ini.")
        else:
            cabang_favorit_opsi = ["— Semua Cabang —"] + sorted(produk_favorit_semua["Cabang"].unique().tolist())
            cabang_favorit_pilihan = st.selectbox(
                "Pilih Cabang", cabang_favorit_opsi, key="pd_pilih_cabang_favorit",
                help="Pilih satu cabang untuk fokus, atau \"— Semua Cabang —\" untuk melihat semuanya sekaligus.",
            )
            produk_favorit = (
                produk_favorit_semua if cabang_favorit_pilihan == "— Semua Cabang —"
                else produk_favorit_semua[produk_favorit_semua["Cabang"] == cabang_favorit_pilihan]
            )

            tampil_pf = produk_favorit.copy()
            for c in ["Potensi Omzet", "Potensi Laba"]:
                tampil_pf[c] = produk_favorit[c].map(lp.format_rupiah_id)
            tampil_pf["Rata-rata Terjual/Bulan"] = produk_favorit["Rata-rata Terjual/Bulan"].map(lambda x: lp.format_decimal_id(x, 1))
            tampil_pf["Stok Saat Ini"] = produk_favorit["Stok Saat Ini"].map(lp.format_int_id)
            tampil_pf["Estimasi Kebutuhan Restock"] = produk_favorit["Estimasi Kebutuhan Restock"].map(lp.format_int_id)
            st.dataframe(tampil_pf, use_container_width=True, height=460)
            st.download_button(
                "⬇️ Unduh CSV — Produk Favorit per Cabang (semua cabang, tidak terpengaruh pilihan di atas)",
                produk_favorit_semua.to_csv(index=False).encode("utf-8-sig"),
                "produk_favorit_per_cabang.csv", "text/csv", key="pd_dl_produk_favorit",
            )

    elif df_jual_stok is not None and mode_tampilan == "Semua Cabang (Gabungan)":
        c1, c2 = st.columns(2)
        with c1:
            top_n_gabungan = st.slider("Top berapa produk (gabungan semua cabang)", 5, 30, 10, key="pd_top_n_gabungan")
        with c2:
            urutkan_dari = st.selectbox(
                "Urutkan berdasarkan", ["Qty Terjual", "Potensi Omzet", "Potensi Laba"], key="pd_urutkan_gabungan",
            )
        produk_favorit = lp.produk_favorit_semua_cabang(df_jual_stok, dasar, top_n=top_n_gabungan, urutkan_dari=urutkan_dari)

        if produk_favorit.empty:
            st.info("Tidak ada data penjualan aksesoris pada filter cabang saat ini.")
        else:
            tampil_pf = produk_favorit.copy()
            for c in ["Potensi Omzet", "Potensi Laba"]:
                tampil_pf[c] = produk_favorit[c].map(lp.format_rupiah_id)
            tampil_pf["Rata-rata Terjual/Bulan"] = produk_favorit["Rata-rata Terjual/Bulan"].map(lambda x: lp.format_decimal_id(x, 1))
            tampil_pf["Stok Semua Cabang"] = produk_favorit["Stok Semua Cabang"].map(lp.format_int_id)
            tampil_pf["Estimasi Kebutuhan Restock"] = produk_favorit["Estimasi Kebutuhan Restock"].map(lp.format_int_id)
            st.dataframe(tampil_pf, use_container_width=True, height=460)
            st.caption(
                "**\"Jumlah Cabang Stok Kosong/Rendah\"** = berapa dari total cabang yang aktif "
                "menjual produk ini stoknya sekarang ≤ 2 unit — makin besar angkanya, makin "
                "mendesak dibenahi secara jaringan (bukan cuma satu cabang)."
            )
            st.download_button(
                "⬇️ Unduh CSV — Produk Favorit Semua Cabang (Gabungan)", produk_favorit.to_csv(index=False).encode("utf-8-sig"),
                "produk_favorit_semua_cabang.csv", "text/csv", key="pd_dl_produk_favorit_gabungan",
            )

    if not produk_favorit.empty:
        st.divider()
        st.header("📢 3. Kebutuhan Konsumen yang Belum Terpenuhi")
        kebutuhan = lp.kebutuhan_belum_terpenuhi(produk_favorit)
        n_total = len(produk_favorit)
        n_kurang = len(kebutuhan)
        label_unit = "kombinasi cabang×produk" if mode_tampilan == "Per Cabang" else "produk"
        st.caption(
            f"Produk favorit (sudah terbukti laku) tapi stoknya kosong/sangat rendah — inilah "
            f"yang paling menggambarkan permintaan konsumen yang belum terlayani. "
            f"**{lp.format_int_id(n_kurang)} dari {lp.format_int_id(n_total)}** {label_unit} "
            f"({lp.format_percent_id(n_kurang/n_total*100 if n_total else 0)}) berstatus wajib direstock."
        )
        if kebutuhan.empty:
            st.success("✅ Semua produk favorit stoknya masih memadai.")
        else:
            tampil_kbt = kebutuhan.copy()
            for c in ["Potensi Omzet", "Potensi Laba"]:
                tampil_kbt[c] = kebutuhan[c].map(lp.format_rupiah_id)
            tampil_kbt["Rata-rata Terjual/Bulan"] = kebutuhan["Rata-rata Terjual/Bulan"].map(lambda x: lp.format_decimal_id(x, 1))
            kolom_stok = "Stok Saat Ini" if mode_tampilan == "Per Cabang" else "Stok Semua Cabang"
            tampil_kbt[kolom_stok] = kebutuhan[kolom_stok].map(lp.format_int_id)
            tampil_kbt["Estimasi Kebutuhan Restock"] = kebutuhan["Estimasi Kebutuhan Restock"].map(lp.format_int_id)

            total_potensi_omzet = kebutuhan["Potensi Omzet"].sum()
            total_potensi_laba = kebutuhan["Potensi Laba"].sum()
            c1, c2 = st.columns(2)
            c1.metric("Total Potensi Omzet (kalau semua terpenuhi)", lp.format_rupiah_id(total_potensi_omzet))
            c2.metric("Total Potensi Laba (kalau semua terpenuhi)", lp.format_rupiah_id(total_potensi_laba))

            st.dataframe(tampil_kbt, use_container_width=True, height=420)
            st.download_button(
                "⬇️ Unduh CSV — Kebutuhan Konsumen Belum Terpenuhi", kebutuhan.to_csv(index=False).encode("utf-8-sig"),
                "kebutuhan_belum_terpenuhi.csv", "text/csv", key="pd_dl_kebutuhan",
            )

    st.divider()

    # -----------------------------------------------------------------
    # 4. Analisa Lokasi Cabang MFlash
    # -----------------------------------------------------------------
    st.header("📍 4. Analisa Lokasi Cabang MFlash")
    st.caption(
        "Lokasi 18 cabang MFlash (dicari langsung dari data lokasi asli — alamat, koordinat, "
        "dan rating), disandingkan dengan nilai persediaan aksesoris per cabang."
    )

    lokasi = lp.data_lokasi_cabang()
    if not nv_banding.empty:
        lokasi_gabung = lokasi.merge(nv_banding, on="Cabang", how="left")
    else:
        lokasi_gabung = lokasi.copy()
        lokasi_gabung["Total Nilai"] = np.nan

    peta_df = lokasi_gabung.rename(columns={"Lat": "lat", "Lon": "lon"})[["lat", "lon"]]
    st.map(peta_df, size=60)

    st.subheader("Sebaran Wilayah")
    ring_wilayah = lp.ringkasan_wilayah(nv_banding) if not nv_banding.empty else pd.DataFrame()
    if not ring_wilayah.empty:
        st.bar_chart(ring_wilayah.set_index("Wilayah")["Jumlah Cabang"])
        tampil_wil = ring_wilayah.copy()
        tampil_wil["Total Nilai Persediaan"] = ring_wilayah["Total Nilai Persediaan"].map(lp.format_rupiah_id)
        tampil_wil["Rata-rata Nilai / Cabang"] = ring_wilayah["Rata-rata Nilai / Cabang"].map(lp.format_rupiah_id)
        st.dataframe(tampil_wil, use_container_width=True)

    with st.expander(f"Lihat detail lokasi ({len(lokasi_gabung)} cabang)"):
        tampil_lokasi = lokasi_gabung.copy()
        if "Total Nilai" in tampil_lokasi.columns:
            tampil_lokasi["Total Nilai"] = tampil_lokasi["Total Nilai"].apply(
                lambda x: lp.format_rupiah_id(x) if pd.notna(x) else "-"
            )
        st.dataframe(
            tampil_lokasi[["Cabang", "Wilayah", "Alamat", "Rating", "Jumlah Ulasan", "Total Nilai"]] if "Total Nilai" in tampil_lokasi.columns else tampil_lokasi,
            use_container_width=True, height=460,
        )
        st.download_button(
            "⬇️ Unduh CSV — Lokasi Cabang", lokasi_gabung.to_csv(index=False).encode("utf-8-sig"),
            "lokasi_cabang.csv", "text/csv", key="pd_dl_lokasi",
        )

    st.divider()

    # -----------------------------------------------------------------
    # Peta Stok — Cabang × Produk (SATU-SATUNYA tempat pakai indikator 🔴🟡🟢)
    # -----------------------------------------------------------------
    st.header("🗺️ Peta Stok — Cabang × Produk (LUNA)")
    st.caption(
        "🔴🟡🟢 hanya dipakai di sini. Merah = stok ≤ 25, Kuning = stok 26–99, Hijau = stok ≥ 100. "
        "Khusus produk LUNA (87 nama produk, masih kebaca dalam satu grid) — sel abu-abu \"-\" "
        "berarti produk itu tidak tercatat sama sekali di cabang tsb (bukan berarti stoknya 0)."
    )
    ind_luna_heatmap = lp.indikator_stok_luna(dff_luna, batas_merah=batas_merah, batas_kuning=batas_kuning)
    if ind_luna_heatmap.empty:
        st.info("Tidak ada data produk LUNA pada filter ini.")
    else:
        pivot_stok, pivot_ind = lp.pivot_heatmap_stok(ind_luna_heatmap)
        if pivot_stok.empty:
            st.info("Tidak ada data untuk peta stok pada filter ini.")
        else:
            st.dataframe(lp.styler_heatmap(pivot_stok, pivot_ind), use_container_width=True, height=520)

    st.divider()

    # -----------------------------------------------------------------
    # Analisa & tindak lanjut
    # -----------------------------------------------------------------
    st.header("📌 Analisa & Tindak Lanjut")
    catatan = []

    if not nv_banding.empty:
        top_nilai = nv_banding.iloc[0]
        catatan.append(
            f"Cabang **{top_nilai['Cabang']}** punya nilai persediaan aksesoris terbesar "
            f"({lp.format_rupiah_id(top_nilai['Total Nilai'])}), dengan porsi LUNA "
            f"{lp.format_percent_id(top_nilai['Porsi LUNA (%)'])}."
        )
        porsi_luna_rerata = nv_banding["Porsi LUNA (%)"].mean()
        catatan.append(
            f"Rata-rata porsi nilai persediaan LUNA terhadap total di seluruh cabang: "
            f"**{lp.format_percent_id(porsi_luna_rerata)}**."
        )

    if not produk_favorit.empty:
        n_total = len(produk_favorit)
        n_kurang = len(lp.kebutuhan_belum_terpenuhi(produk_favorit))
        if n_kurang > 0:
            catatan.append(
                f"**{lp.format_percent_id(n_kurang/n_total*100)}** dari produk paling diminati di "
                "seluruh cabang berstatus wajib direstock — sebagian besar produk terlaris justru "
                "kehabisan stok, sinyal kuat permintaan konsumen yang belum terlayani optimal."
            )

    if not ring_wilayah.empty:
        wil_top = ring_wilayah.iloc[0]
        catatan.append(
            f"Wilayah **{wil_top['Wilayah']}** punya nilai persediaan aksesoris tertinggi "
            f"({lp.format_rupiah_id(wil_top['Total Nilai Persediaan'])}) dari "
            f"{int(wil_top['Jumlah Cabang'])} cabang di wilayah tsb."
        )

    if not catatan:
        catatan.append("Tidak ada data untuk dianalisa pada filter saat ini.")

    for c in catatan:
        st.markdown("- " + c)


# ---------------------------------------------------------------------------
# TAB 1b — Dashboard Persediaan Parfum
# ---------------------------------------------------------------------------
def render_persediaan_parfum_tab():
    if err_persediaan:
        st.error(f"Gagal membaca berkas persediaan: {err_persediaan}")
        return
    if df_persediaan is None:
        st.info(
            "Belum ada data. Unggah berkas Excel/CSV **Persediaan** (sheet **Daftar Barang dan "
            "Jasa** — boleh berkas semua kategori) lewat panel kiri, atau taruh berkasnya di "
            "root repo sebelum deploy."
        )
        return

    st.subheader("Filter — Data Persediaan Parfum")
    cabang_opsi_pf = sorted(df_persediaan["Cabang"].dropna().unique().tolist())
    sel_cabang_pf = st.multiselect("Cabang", cabang_opsi_pf, default=cabang_opsi_pf, key="pf_cabang")

    dff_parfum = lp.apply_filters(df_persediaan, cabang=sel_cabang_pf if sel_cabang_pf else None, kategori="PARFUM", filter_luna=None)

    if dff_parfum.empty:
        st.warning(
            "Tidak ada baris berkategori **PARFUM** pada berkas/filter ini. Kalau berkas yang "
            "diunggah khusus aksesoris saja (tanpa kategori Parfum), unggah berkas persediaan "
            "SEMUA kategori barang di panel kiri."
        )
        return

    st.caption(
        f"Menampilkan {len(dff_parfum):,}".replace(",", ".") + " baris persediaan kategori PARFUM, "
        f"{dff_parfum['Nama Barang'].nunique()} nama produk unik."
    )
    st.caption(
        "ℹ️ Kategori Parfum di data MFlash hampir seluruhnya satu brand (UMAIR) — beda dari "
        "Aksesoris yang perlu dipilah LUNA vs Selain LUNA, jadi bagian ini tidak dipisah per brand."
    )
    st.divider()

    # -----------------------------------------------------------------
    # 1. Nilai Persediaan Parfum per Cabang
    # -----------------------------------------------------------------
    st.header("💰 1. Nilai Persediaan Parfum per Cabang")
    nv_parfum = lp.nilai_persediaan_cabang(dff_parfum)
    if nv_parfum.empty:
        st.info("Tidak ada data pada filter ini.")
    else:
        total_nilai_parfum = nv_parfum["Nilai Persediaan"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total Nilai Persediaan Parfum", lp.format_rupiah_id(total_nilai_parfum))
        c2.metric("Total Qty", lp.format_int_id(nv_parfum["Total Qty"].sum()))

        st.bar_chart(nv_parfum.set_index("Cabang")["Nilai Persediaan"])
        tampil_nv_pf = nv_parfum.copy()
        tampil_nv_pf["Total Qty"] = nv_parfum["Total Qty"].map(lp.format_int_id)
        tampil_nv_pf["Nilai Persediaan"] = nv_parfum["Nilai Persediaan"].map(lp.format_rupiah_id)
        st.dataframe(tampil_nv_pf.drop(columns=["Jumlah SKU"]), use_container_width=True, height=420)
        st.download_button(
            "⬇️ Unduh CSV — Nilai Persediaan Parfum per Cabang", nv_parfum.to_csv(index=False).encode("utf-8-sig"),
            "nilai_persediaan_parfum_cabang.csv", "text/csv", key="pf_dl_nilai",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 1b. Produk Paling Diminati per Cabang — Parfum (Stok vs Terjual)
    # -----------------------------------------------------------------
    st.header("🏆 2. Produk Paling Diminati per Cabang (Wajib Distok)")
    st.caption(
        "Menyandingkan data PENJUALAN (produk mana yang laku) dengan data STOK saat ini — "
        "supaya kelihatan produk favorit yang stoknya justru kosong/rendah."
    )

    df_jual_parfum = None
    if raw_aksesoris is None:
        st.info("Data penjualan belum diunggah — bagian ini butuh data penjualan untuk tahu produk mana yang paling laku.")
    elif "CABANG" in raw_aksesoris.columns:
        df_jual_parfum = la.hanya_kategori(la.finalize_data(raw_aksesoris), "PARFUM")
    else:
        nama_bersama_pf = st.session_state.get("nama_cabang_bersama")
        if nama_bersama_pf:
            df_jual_parfum = la.hanya_kategori(la.finalize_data(raw_aksesoris, cabang_default=nama_bersama_pf), "PARFUM")
        else:
            st.info(
                "Berkas penjualan ini rincian satu cabang saja (tanpa kolom Cabang). Isi dulu "
                "nama cabangnya di tab **Dashboard Penjualan Aksesoris**, baru bagian ini akan terisi."
            )

    if df_jual_parfum is not None and df_jual_parfum.empty:
        st.info("Tidak ada baris transaksi kategori PARFUM pada berkas penjualan ini.")
    elif df_jual_parfum is not None:
        top_n_favorit_pf = st.slider("Top berapa produk per cabang", 3, 10, 5, key="pf_top_n_favorit")
        produk_favorit_pf_semua = lp.produk_favorit_per_cabang(df_jual_parfum, dff_parfum, top_n=top_n_favorit_pf)

        if produk_favorit_pf_semua.empty:
            st.info("Tidak ada data penjualan Parfum pada filter cabang saat ini.")
        else:
            cabang_favorit_pf_opsi = ["— Semua Cabang —"] + sorted(produk_favorit_pf_semua["Cabang"].unique().tolist())
            cabang_favorit_pf_pilihan = st.selectbox(
                "Pilih Cabang", cabang_favorit_pf_opsi, key="pf_pilih_cabang_favorit",
            )
            produk_favorit_pf = (
                produk_favorit_pf_semua if cabang_favorit_pf_pilihan == "— Semua Cabang —"
                else produk_favorit_pf_semua[produk_favorit_pf_semua["Cabang"] == cabang_favorit_pf_pilihan]
            )
            tampil_pf_fav = produk_favorit_pf.copy()
            for c in ["Potensi Omzet", "Potensi Laba"]:
                tampil_pf_fav[c] = produk_favorit_pf[c].map(lp.format_rupiah_id)
            tampil_pf_fav["Rata-rata Terjual/Bulan"] = produk_favorit_pf["Rata-rata Terjual/Bulan"].map(lambda x: lp.format_decimal_id(x, 1))
            tampil_pf_fav["Stok Saat Ini"] = produk_favorit_pf["Stok Saat Ini"].map(lp.format_int_id)
            tampil_pf_fav["Estimasi Kebutuhan Restock"] = produk_favorit_pf["Estimasi Kebutuhan Restock"].map(lp.format_int_id)
            st.dataframe(tampil_pf_fav, use_container_width=True, height=420)
            st.download_button(
                "⬇️ Unduh CSV — Produk Favorit Parfum per Cabang", produk_favorit_pf_semua.to_csv(index=False).encode("utf-8-sig"),
                "produk_favorit_parfum_cabang.csv", "text/csv", key="pf_dl_produk_favorit",
            )

            kebutuhan_pf = lp.kebutuhan_belum_terpenuhi(produk_favorit_pf)
            if not kebutuhan_pf.empty:
                st.subheader("📢 Kebutuhan Konsumen Belum Terpenuhi (Parfum)")
                st.caption("Produk favorit yang stoknya kosong/rendah — sinyal permintaan yang belum terlayani.")
                tampil_keb_pf = kebutuhan_pf.copy()
                for c in ["Potensi Omzet", "Potensi Laba"]:
                    tampil_keb_pf[c] = kebutuhan_pf[c].map(lp.format_rupiah_id)
                tampil_keb_pf["Stok Saat Ini"] = kebutuhan_pf["Stok Saat Ini"].map(lp.format_int_id)
                st.dataframe(tampil_keb_pf, use_container_width=True, height=300)

    st.divider()

    # -----------------------------------------------------------------
    # 3. Analisa & Tindak Lanjut
    # -----------------------------------------------------------------
    st.header("📌 Analisa & Tindak Lanjut")
    catatan_pf = []

    if not nv_parfum.empty:
        top_nilai_pf = nv_parfum.iloc[0]
        catatan_pf.append(
            f"Cabang **{top_nilai_pf['Cabang']}** punya nilai persediaan Parfum terbesar "
            f"({lp.format_rupiah_id(top_nilai_pf['Nilai Persediaan'])})."
        )

    if not catatan_pf:
        catatan_pf.append("Tidak ada data Parfum untuk dianalisa pada filter saat ini.")

    for c in catatan_pf:
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

    # PENTING: berkas penjualan sekarang bisa berisi SEMUA kategori barang
    # (JASA, SPAREPART, dll — bukan cuma aksesoris). Seluruh bagian di bawah
    # ini (revenue, HPP, katalog LUNA, target) HARUS difilter ke AKSESORIS
    # saja, atau angka Omzet akan salah besar (ikut menjumlahkan kategori lain).
    df_semua_kategori = df  # disimpan untuk lintas-kategori (mis. target UMAIR Parfum)
    df = la.hanya_kategori(df, "AKSESORIS")
    if df.empty:
        st.warning(
            "Tidak ada baris berkategori AKSESORIS pada berkas ini. Cek lagi berkas yang "
            "diunggah — mungkin filenya untuk kategori lain."
        )
        return

    # -----------------------------------------------------------------
    # 0. Dashboard & Scoreboard Penjualan Aksesoris — Tertarget vs Non
    #    Tertarget (Parfum sengaja TIDAK disertakan di bagian ini).
    # -----------------------------------------------------------------
    st.header("🏆 Dashboard & Scoreboard Penjualan Aksesoris")
    st.caption(
        "**Aksesoris Tertarget** = LUNA KECUALI Hydrogel · **Aksesoris Non Tertarget** = Selain LUNA "
        "(termasuk LUNA Hydrogel). Parfum tidak disertakan di bagian ini."
    )

    periode_dsb_opsi = list(la.PERIODE_SAMURAI.keys())
    default_idx_samurai39 = periode_dsb_opsi.index("Samurai 39 (Jul–Sep 2026)") if "Samurai 39 (Jul–Sep 2026)" in periode_dsb_opsi else 0
    d1, d2 = st.columns(2)
    with d1:
        periode_dsb_pilihan = st.selectbox("Periode", periode_dsb_opsi, index=default_idx_samurai39, key="dsb_periode")
    with d2:
        target_total_dsb = st.number_input("1️⃣ Total Target Penjualan Aksesoris (Rp)", min_value=0, value=3_500_000_000, step=100_000_000, format="%d", key="dsb_target_total")
    tgl_mulai_dsb, tgl_selesai_dsb = la.PERIODE_SAMURAI[periode_dsb_pilihan]
    st.caption(f"Periode: {tgl_mulai_dsb.strftime('%d %b %Y')} – {tgl_selesai_dsb.strftime('%d %b %Y')}.")

    daftar_cabang_dsb = sorted(df["CABANG"].dropna().unique().tolist())
    n_cabang_dsb = len(daftar_cabang_dsb) or 1
    seed_target_dsb = pd.DataFrame({
        "Cabang": daftar_cabang_dsb, "Target": [target_total_dsb / n_cabang_dsb] * n_cabang_dsb,
    })
    with st.expander("✏️ Sesuaikan Target per Cabang (opsional, default dibagi rata)", expanded=False):
        edited_target_dsb = st.data_editor(
            seed_target_dsb, use_container_width=True, hide_index=True, key="dsb_target_editor",
            column_config={"Target": st.column_config.NumberColumn("Target (Rp)", min_value=0, step=100_000, format="%d")},
        )
    target_per_cabang_dsb = dict(zip(edited_target_dsb["Cabang"], edited_target_dsb["Target"]))

    scoreboard = la.scoreboard_cabang_aksesoris(
        df, target_total=target_total_dsb, tanggal_mulai=tgl_mulai_dsb, tanggal_selesai=tgl_selesai_dsb,
        target_per_cabang=target_per_cabang_dsb,
    )

    if scoreboard.empty:
        st.info("Tidak ada data penjualan aksesoris pada periode ini.")
    else:
        total_omzet_dsb = scoreboard["Total Omzet"].sum()
        total_target_dsb_aktual = scoreboard["Target"].sum()
        total_laba_dsb = scoreboard["Laba"].sum()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Omzet Aksesoris", la.format_rupiah_id(total_omzet_dsb))
        m2.metric("Total Target", la.format_rupiah_id(total_target_dsb_aktual))
        m3.metric("% Pencapaian Jaringan", la.format_percent_id(total_omzet_dsb / total_target_dsb_aktual * 100 if total_target_dsb_aktual else 0))
        m4.metric("Margin Jaringan", la.format_percent_id(total_laba_dsb / total_omzet_dsb * 100 if total_omzet_dsb else 0))

        st.markdown("##### 2️⃣ Scoreboard Penjualan per Cabang (Omzet Tertinggi → Terendah)")
        st.caption("Warna indikator % Pencapaian: 🔴 <85% · 🟡 85–99% · 🟢 ≥100%.")
        styled_scoreboard = scoreboard.style.map(
            la.warna_indikator_pencapaian, subset=["% Pencapaian"],
        ).format({
            "Omzet Tertarget": la.format_rupiah_id, "Omzet Non Tertarget": la.format_rupiah_id,
            "Total Omzet": la.format_rupiah_id, "Laba": la.format_rupiah_id, "Margin (%)": la.format_percent_id,
            "Target": la.format_rupiah_id, "% Pencapaian": la.format_percent_id,
            "Rata-rata Omzet / Hari": la.format_rupiah_id,
        })
        st.dataframe(styled_scoreboard, use_container_width=True, height=650)
        st.download_button(
            "⬇️ Unduh CSV — Scoreboard Penjualan per Cabang", scoreboard.to_csv(index=False).encode("utf-8-sig"),
            "scoreboard_penjualan_aksesoris.csv", "text/csv", key="dsb_dl_scoreboard",
        )

        st.markdown("##### 3️⃣ Rata-rata Penjualan per Hari per Cabang")
        st.bar_chart(scoreboard.set_index("Cabang")["Rata-rata Omzet / Hari"])

        st.markdown("##### 4️⃣ Monitoring Margin Cabang — Aksesoris di Bawah 40%")
        margin_rendah = scoreboard[scoreboard["Margin (%)"] < 40].sort_values("Margin (%)", ascending=True).reset_index(drop=True)
        if margin_rendah.empty:
            st.success("✅ Semua cabang sudah bermargin ≥ 40% pada periode ini.")
        else:
            st.warning(f"⚠️ {len(margin_rendah)} dari {len(scoreboard)} cabang bermargin di bawah 40%.")
            tampil_margin = margin_rendah[["Cabang", "Total Omzet", "Laba", "Margin (%)"]].copy()
            tampil_margin["Total Omzet"] = margin_rendah["Total Omzet"].map(la.format_rupiah_id)
            tampil_margin["Laba"] = margin_rendah["Laba"].map(la.format_rupiah_id)
            tampil_margin["Margin (%)"] = margin_rendah["Margin (%)"].map(la.format_percent_id)
            st.dataframe(tampil_margin, use_container_width=True, height=min(80 + 38 * len(margin_rendah), 400))

        produk_scoreboard = la.produk_terlaris_aksesoris_scoreboard(df, tgl_mulai_dsb, tgl_selesai_dsb)

        st.markdown("##### 5️⃣ Produk Terlaris Aksesoris (Qty Tertinggi → Terendah)")
        if produk_scoreboard.empty:
            st.info("Tidak ada data produk pada periode ini.")
        else:
            top_n_produk_dsb = st.slider("Tampilkan berapa produk teratas", 5, 50, 20, key="dsb_top_n_produk")
            top_produk = produk_scoreboard.head(top_n_produk_dsb).copy()
            top_produk["Omzet"] = top_produk["Omzet"].map(la.format_rupiah_id)
            top_produk["Laba"] = top_produk["Laba"].map(la.format_rupiah_id)
            top_produk["Margin (%)"] = top_produk["Margin (%)"].map(la.format_percent_id)
            top_produk["Qty Terjual"] = produk_scoreboard.head(top_n_produk_dsb)["Qty Terjual"].map(la.format_int_id)
            st.dataframe(top_produk, use_container_width=True, height=min(80 + 38 * len(top_produk), 500))
            st.download_button(
                "⬇️ Unduh CSV — Seluruh Produk Terlaris Aksesoris", produk_scoreboard.to_csv(index=False).encode("utf-8-sig"),
                "produk_terlaris_aksesoris.csv", "text/csv", key="dsb_dl_produk",
            )

        st.markdown("##### 6️⃣ Monitoring Stok Persediaan — Tertarget vs Non Tertarget")
        if df_persediaan is None:
            st.info("Unggah data Persediaan di panel kiri untuk melihat bagian ini.")
        else:
            aks_stok_dsb = lp.apply_filters(df_persediaan, hanya_aksesoris=True, filter_luna=None)
            stok_tertarget_vs_non = lp.nilai_persediaan_tertarget_vs_non(aks_stok_dsb)
            if stok_tertarget_vs_non.empty:
                st.info("Tidak ada data stok aksesoris.")
            else:
                s1, s2 = st.columns(2)
                s1.metric("Total Nilai Stok Tertarget", la.format_rupiah_id(stok_tertarget_vs_non["Nilai Tertarget"].sum()))
                s2.metric("Total Nilai Stok Non Tertarget", la.format_rupiah_id(stok_tertarget_vs_non["Nilai Non Tertarget"].sum()))
                tampil_stok = stok_tertarget_vs_non.copy()
                for c in ["Nilai Tertarget", "Nilai Non Tertarget", "Total Nilai"]:
                    tampil_stok[c] = stok_tertarget_vs_non[c].map(la.format_rupiah_id)
                for c in ["Qty Tertarget", "Qty Non Tertarget"]:
                    tampil_stok[c] = stok_tertarget_vs_non[c].map(la.format_int_id)
                st.dataframe(tampil_stok, use_container_width=True, height=530)
                st.download_button(
                    "⬇️ Unduh CSV — Monitoring Stok Tertarget vs Non Tertarget", stok_tertarget_vs_non.to_csv(index=False).encode("utf-8-sig"),
                    "monitoring_stok_tertarget_vs_non.csv", "text/csv", key="dsb_dl_stok",
                )

        st.markdown("##### 7️⃣ Monitoring Margin Produk Aksesoris (Tertinggi → Terendah)")
        if produk_scoreboard.empty:
            st.info("Tidak ada data produk pada periode ini.")
        else:
            produk_margin = produk_scoreboard.sort_values("Margin (%)", ascending=False).reset_index(drop=True)
            top_n_margin_dsb = st.slider("Tampilkan berapa produk teratas (margin)", 5, 50, 20, key="dsb_top_n_margin")
            tampil_margin_produk = produk_margin.head(top_n_margin_dsb).copy()
            tampil_margin_produk["Omzet"] = tampil_margin_produk["Omzet"].map(la.format_rupiah_id)
            tampil_margin_produk["Laba"] = tampil_margin_produk["Laba"].map(la.format_rupiah_id)
            tampil_margin_produk["Margin (%)"] = tampil_margin_produk["Margin (%)"].map(la.format_percent_id)
            tampil_margin_produk["Qty Terjual"] = produk_margin.head(top_n_margin_dsb)["Qty Terjual"].map(la.format_int_id)
            st.dataframe(tampil_margin_produk, use_container_width=True, height=min(80 + 38 * len(tampil_margin_produk), 500))
            st.download_button(
                "⬇️ Unduh CSV — Seluruh Produk (Urut Margin)", produk_margin.to_csv(index=False).encode("utf-8-sig"),
                "monitoring_margin_produk_aksesoris.csv", "text/csv", key="dsb_dl_margin_produk",
            )

    st.divider()
    st.divider()

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
    # 3a1. Analisa Mendalam: LUNA, Selain LUNA & Parfum UMAIR
    # -----------------------------------------------------------------
    st.header("🔍 Analisa Mendalam: LUNA, Selain LUNA & Parfum UMAIR")
    st.caption(
        "Menyandingkan data STOK (persediaan) dan PENJUALAN untuk tiga kelompok, plus deteksi "
        "kepatuhan program Bundling Aksesoris (Surat Edaran SE/001/IN-MF/IV/2026) pada transaksi Service."
    )

    if df_persediaan is None:
        st.info("Unggah data Persediaan di panel kiri untuk melihat bagian Stok pada analisa ini.")
        aks_stok_dasar = pd.DataFrame()
    else:
        aks_stok_dasar = lp.apply_filters(df_persediaan, hanya_aksesoris=True, filter_luna=None)
        if sel_cabang:
            aks_stok_dasar = aks_stok_dasar[aks_stok_dasar["Cabang"].isin(sel_cabang)]

    # df_semua_kategori DIFILTER dulu (tahun/bulan/cabang) supaya deteksi bundling
    # konsisten dengan filter yang dipilih pengguna di atas — bukan selalu semua data.
    df_semua_kategori_f = df_semua_kategori
    if sel_cabang:
        df_semua_kategori_f = df_semua_kategori_f[df_semua_kategori_f["CABANG"].isin(sel_cabang)]
    if sel_tahun:
        df_semua_kategori_f = df_semua_kategori_f[df_semua_kategori_f["TAHUN"].isin(sel_tahun)]
    if sel_bulan:
        df_semua_kategori_f = df_semua_kategori_f[df_semua_kategori_f["BULAN"].isin(sel_bulan)]

    def _render_analisa_brand(nama_kelompok: str, df_stok_kelompok: pd.DataFrame, df_jual_kelompok: pd.DataFrame, keyword_bundling: str, key_prefix: str):
        rs = la.ringkasan_stok_dan_terjual_brand(df_stok_kelompok, df_jual_kelompok)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nilai Stok", la.format_rupiah_id(rs["nilai_stok"]))
        c2.metric("Qty Stok", la.format_int_id(rs["qty_stok"]))
        c3.metric("Omzet Terjual", la.format_rupiah_id(rs["omzet_terjual"]))
        c4.metric("Qty Terjual", la.format_int_id(rs["qty_terjual"]))
        c5, c6 = st.columns(2)
        c5.metric("Rata-rata Qty Terjual / Hari", la.format_decimal_id(rs["rata2_qty_per_hari"], 1))
        c6.metric("Rata-rata Omzet Terjual / Hari", la.format_rupiah_id(rs["rata2_omzet_per_hari"]))
        st.caption(f"Dihitung dari {la.format_int_id(rs['jumlah_hari_data'])} hari dengan transaksi tercatat.")

        bund, temuan = la.analisa_bundling_brand(df_jual_kelompok, df_semua_kategori_f, keyword=keyword_bundling)
        st.markdown(f"##### 🎁 Bundling {keyword_bundling} pada Transaksi Service")
        b1, b2, b3 = st.columns(3)
        b1.metric(f"Qty {keyword_bundling} Terbundling", la.format_int_id(bund["qty_terbundling"]))
        b2.metric(f"Nota Service dgn {keyword_bundling}", la.format_int_id(bund["jumlah_service_dgn_brand"]), la.format_percent_id(bund["pct_bundling_brand"]))
        b3.metric("Nota Service TANPA Aksesoris", la.format_int_id(bund["jumlah_service_tanpa_aksesoris"]), la.format_percent_id(bund["pct_tanpa_aksesoris"]), delta_color="inverse")
        st.caption(
            f"Dari {la.format_int_id(bund['jumlah_nota_service'])} nota Service: "
            f"{la.format_int_id(bund['jumlah_service_dgn_brand'])} pakai {keyword_bundling}, "
            f"{la.format_int_id(bund['jumlah_service_dgn_aksesoris_lain'])} pakai aksesoris brand LAIN "
            "(sesuai pengecualian SE kalau brand target kosong — bukan pelanggaran), dan "
            f"**{la.format_int_id(bund['jumlah_service_tanpa_aksesoris'])} SAMA SEKALI TIDAK ADA "
            "aksesoris** (temuan pelanggaran murni terhadap kebijakan bundling)."
        )

        if not temuan.empty:
            with st.expander(f"📋 Temuan: {len(temuan):,}".replace(",", ".") + " Nota Service Tanpa Bundling Aksesoris (Cabang & No. Nota)"):
                cabang_temuan_opsi = sorted(temuan["Cabang"].unique().tolist())
                cabang_temuan_pilih = st.multiselect("Filter cabang", cabang_temuan_opsi, default=cabang_temuan_opsi, key=f"{key_prefix}_temuan_cabang")
                temuan_tampil = temuan[temuan["Cabang"].isin(cabang_temuan_pilih)] if cabang_temuan_pilih else temuan.iloc[0:0]
                ringkasan_per_cabang_temuan = temuan_tampil.groupby("Cabang").size().reset_index(name="Jumlah Nota Tanpa Bundling").sort_values("Jumlah Nota Tanpa Bundling", ascending=False)
                st.dataframe(ringkasan_per_cabang_temuan, use_container_width=True, height=200)
                st.dataframe(temuan_tampil[["Cabang", "NO FAKTUR", "TGL FAKTUR"]], use_container_width=True, height=350)
                st.download_button(
                    f"⬇️ Unduh CSV — Temuan Nota Tanpa Bundling ({keyword_bundling})",
                    temuan.to_csv(index=False).encode("utf-8-sig"),
                    f"temuan_tanpa_bundling_{key_prefix}.csv", "text/csv", key=f"{key_prefix}_dl_temuan",
                )

    st.subheader("1️⃣ Aksesoris LUNA")
    luna_stok = aks_stok_dasar[aks_stok_dasar["ADALAH_LUNA"]] if not aks_stok_dasar.empty else aks_stok_dasar
    luna_jual = dff[dff["NAMA BARANG"].astype(str).str.upper().str.contains("LUNA", na=False)]
    _render_analisa_brand("Aksesoris LUNA", luna_stok, luna_jual, "LUNA", "an_luna")

    st.divider()
    st.subheader("2️⃣ Aksesoris Selain LUNA (Vivan, Robot, Anker, dll)")
    selain_luna_stok = aks_stok_dasar[~aks_stok_dasar["ADALAH_LUNA"]] if not aks_stok_dasar.empty else aks_stok_dasar
    st.caption(f"{selain_luna_stok['Nama Barang'].nunique() if not selain_luna_stok.empty else 0} nama produk unik di luar brand LUNA.")
    rincian_selain_luna = la.rincian_produk_brand(selain_luna_stok)
    if rincian_selain_luna.empty:
        st.info("Tidak ada data stok aksesoris selain LUNA pada filter ini.")
    else:
        cari_produk_sl = st.text_input("Cari nama produk / brand (mis. \"VIVAN\", \"ROBOT\", \"ANKER\")", key="an_selain_luna_cari")
        rincian_tampil = rincian_selain_luna
        if cari_produk_sl:
            rincian_tampil = rincian_selain_luna[rincian_selain_luna["Nama Barang"].str.upper().str.contains(cari_produk_sl.upper(), na=False)]
        st.caption(f"Menampilkan {len(rincian_tampil):,}".replace(",", ".") + f" dari {len(rincian_selain_luna):,}".replace(",", ".") + " baris (Cabang × Produk).")
        tampil_rsl = rincian_tampil.copy()
        tampil_rsl["Nilai Stok"] = rincian_tampil["Nilai Stok"].map(la.format_rupiah_id)
        st.dataframe(tampil_rsl, use_container_width=True, height=460)
        st.download_button(
            "⬇️ Unduh CSV — Rincian Semua Barang Aksesoris Selain LUNA (lengkap)",
            rincian_selain_luna.to_csv(index=False).encode("utf-8-sig"),
            "rincian_aksesoris_selain_luna.csv", "text/csv", key="an_dl_selain_luna",
        )

    st.divider()
    st.subheader("3️⃣ Parfum UMAIR")
    st.caption(
        "Kategori PARFUM (terpisah dari AKSESORIS) — mencakup seluruh varian UMAIR "
        "(mis. Quantum, ADN, Firdaus, dll), bukan cuma satu varian."
    )
    if df_persediaan is None:
        parfum_umair_stok = pd.DataFrame()
    else:
        parfum_stok_dasar = lp.apply_filters(df_persediaan, kategori="PARFUM", filter_luna=None)
        if sel_cabang:
            parfum_stok_dasar = parfum_stok_dasar[parfum_stok_dasar["Cabang"].isin(sel_cabang)]
        parfum_umair_stok = parfum_stok_dasar[parfum_stok_dasar["Nama Barang"].astype(str).str.upper().str.contains("UMAIR", na=False)]
    df_parfum_jual_an = la.hanya_kategori(df_semua_kategori, "PARFUM")
    if sel_cabang:
        df_parfum_jual_an = df_parfum_jual_an[df_parfum_jual_an["CABANG"].isin(sel_cabang)]
    if sel_tahun:
        df_parfum_jual_an = df_parfum_jual_an[df_parfum_jual_an["TAHUN"].isin(sel_tahun)]
    if sel_bulan:
        df_parfum_jual_an = df_parfum_jual_an[df_parfum_jual_an["BULAN"].isin(sel_bulan)]
    umair_jual = df_parfum_jual_an[df_parfum_jual_an["NAMA BARANG"].astype(str).str.upper().str.contains("UMAIR", na=False)]
    _render_analisa_brand("Parfum UMAIR", parfum_umair_stok, umair_jual, "UMAIR", "an_umair")

    st.divider()

    # -----------------------------------------------------------------
    # 3a2. Grafik Penjualan LUNA vs Selain LUNA vs Parfum & Kontribusi Cabang
    # -----------------------------------------------------------------
    st.header("📊 Penjualan Aksesoris LUNA vs Selain LUNA vs Parfum")
    st.caption(
        "Aksesoris LUNA/Selain LUNA dari data yang sudah difilter kategori AKSESORIS; "
        "Parfum diambil terpisah dari kategori PARFUM pada berkas penjualan yang sama "
        "(kedua kategori beda, sehingga dibandingkan berdampingan di sini)."
    )

    df_parfum_untuk_grafik = la.hanya_kategori(df_semua_kategori, "PARFUM")
    if sel_cabang:
        df_parfum_untuk_grafik = df_parfum_untuk_grafik[df_parfum_untuk_grafik["CABANG"].isin(sel_cabang)]
    if sel_tahun:
        df_parfum_untuk_grafik = df_parfum_untuk_grafik[df_parfum_untuk_grafik["TAHUN"].isin(sel_tahun)]
    if sel_bulan:
        df_parfum_untuk_grafik = df_parfum_untuk_grafik[df_parfum_untuk_grafik["BULAN"].isin(sel_bulan)]

    opk = la.omzet_per_kelompok(dff, df_parfum_untuk_grafik, keyword_brand="LUNA")
    if opk.empty or opk["Omzet"].sum() == 0:
        st.info("Tidak ada data untuk grafik ini pada filter saat ini.")
    else:
        st.bar_chart(opk.set_index("Kelompok")["Omzet"])
        tampil_opk = opk.copy()
        tampil_opk["Omzet"] = opk["Omzet"].map(la.format_rupiah_id)
        tampil_opk["Laba"] = opk["Laba"].map(la.format_rupiah_id)
        tampil_opk["Jumlah Nota"] = opk["Jumlah Nota"].map(la.format_int_id)
        tampil_opk["Jumlah Item Terjual"] = opk["Jumlah Item Terjual"].map(la.format_int_id)
        st.dataframe(tampil_opk, use_container_width=True)
        st.download_button(
            "⬇️ Unduh CSV — Omzet per Kelompok (LUNA/Selain LUNA/Parfum)", opk.to_csv(index=False).encode("utf-8-sig"),
            "omzet_per_kelompok.csv", "text/csv", key="ak_dl_kelompok",
        )

    st.subheader("📶 Indikator Kontribusi Cabang (Terendah → Tertinggi)")
    st.caption(
        "Total omzet Aksesoris + Parfum per cabang, diurutkan dari kontribusi PALING RENDAH "
        "ke PALING BESAR — cabang di paling atas grafik yang paling perlu didorong."
    )
    kc = la.kontribusi_cabang_gabungan(dff, df_parfum_untuk_grafik)
    if kc.empty:
        st.info("Tidak ada data untuk diagram ini pada filter saat ini.")
    else:
        st.bar_chart(kc.set_index("Cabang")["Total Omzet"])
        tampil_kc = kc.copy()
        tampil_kc["Omzet Aksesoris"] = kc["Omzet Aksesoris"].map(la.format_rupiah_id)
        tampil_kc["Omzet Parfum"] = kc["Omzet Parfum"].map(la.format_rupiah_id)
        tampil_kc["Total Omzet"] = kc["Total Omzet"].map(la.format_rupiah_id)
        tampil_kc["Porsi Kontribusi (%)"] = kc["Porsi Kontribusi (%)"].map(la.format_percent_id)
        st.dataframe(tampil_kc, use_container_width=True, height=460)
        st.caption(
            f"Kontribusi terendah: **{kc.iloc[0]['Cabang']}** ({la.format_percent_id(kc.iloc[0]['Porsi Kontribusi (%)'])}) · "
            f"tertinggi: **{kc.iloc[-1]['Cabang']}** ({la.format_percent_id(kc.iloc[-1]['Porsi Kontribusi (%)'])})."
        )
        st.download_button(
            "⬇️ Unduh CSV — Kontribusi Cabang (Aksesoris + Parfum)", kc.to_csv(index=False).encode("utf-8-sig"),
            "kontribusi_cabang.csv", "text/csv", key="ak_dl_kontribusi_cabang",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 3a3. Pencapaian per Periode Samurai & Perbandingan Antar Periode
    # -----------------------------------------------------------------
    st.header("📅 Pencapaian Omzet & Gross Profit per Periode Samurai")
    st.caption(
        "Periode internal: Samurai 37 (Jan–Mar 2026), Samurai 38 (Apr–Jun 2026), "
        "Samurai 39 (Jul–Sep 2026), Samurai 40 (Okt–Des 2026) — dihitung dari data "
        "AKSESORIS (LUNA vs Selain LUNA), tidak terpengaruh filter tahun/bulan di atas "
        "karena periode Samurai sudah menentukan rentang tanggalnya sendiri."
    )

    periode_pilihan = st.selectbox(
        "Pilih periode untuk lihat pencapaiannya", list(la.PERIODE_SAMURAI.keys()), key="ak_periode_samurai",
    )
    hasil_periode = la.pencapaian_kelompok_periode(df, periode_pilihan, keyword_brand="LUNA")

    if hasil_periode.empty:
        st.info(f"Belum ada data penjualan aksesoris pada periode **{periode_pilihan}**.")
    else:
        p1, p2 = st.columns(2)
        for col, (_, row) in zip([p1, p2], hasil_periode.iterrows()):
            with col:
                st.metric(f"{row['Kelompok']} — Omzet", la.format_rupiah_id(row["Omzet"]))
                st.caption(
                    f"Gross Profit {la.format_rupiah_id(row['Gross Profit'])} · "
                    f"Margin {la.format_percent_id(row['Margin (%)'])} · "
                    f"{la.format_int_id(row['Jumlah Item Terjual'])} pcs"
                )
        tampil_hp = hasil_periode.copy()
        tampil_hp["Omzet"] = hasil_periode["Omzet"].map(la.format_rupiah_id)
        tampil_hp["Gross Profit"] = hasil_periode["Gross Profit"].map(la.format_rupiah_id)
        tampil_hp["Margin (%)"] = hasil_periode["Margin (%)"].map(la.format_percent_id)
        tampil_hp["Jumlah Nota"] = hasil_periode["Jumlah Nota"].map(la.format_int_id)
        tampil_hp["Jumlah Item Terjual"] = hasil_periode["Jumlah Item Terjual"].map(la.format_int_id)
        st.dataframe(tampil_hp, use_container_width=True)

    st.subheader("📊 Perbandingan Antar Periode Samurai")
    perbandingan_samurai = la.perbandingan_antar_periode_samurai(df, keyword_brand="LUNA")
    if perbandingan_samurai.empty:
        st.info("Belum ada data untuk perbandingan antar periode.")
    else:
        pivot_omzet = perbandingan_samurai.pivot(index="Periode", columns="Kelompok", values="Omzet")
        pivot_gp = perbandingan_samurai.pivot(index="Periode", columns="Kelompok", values="Gross Profit")

        pg1, pg2 = st.columns(2)
        with pg1:
            st.caption("Omzet per periode")
            st.bar_chart(pivot_omzet)
        with pg2:
            st.caption("Gross Profit per periode")
            st.bar_chart(pivot_gp)

        tampil_pb = perbandingan_samurai.copy()
        tampil_pb["Omzet"] = perbandingan_samurai["Omzet"].map(la.format_rupiah_id)
        tampil_pb["Gross Profit"] = perbandingan_samurai["Gross Profit"].map(la.format_rupiah_id)
        tampil_pb["Margin (%)"] = perbandingan_samurai["Margin (%)"].map(la.format_percent_id)
        st.dataframe(tampil_pb, use_container_width=True, height=250)
        st.caption(
            "Periode yang belum tercantum berarti belum ada data penjualan pada rentang "
            "tanggalnya (mis. Samurai 40 kalau data terbaru belum sampai Oktober 2026)."
        )
        st.download_button(
            "⬇️ Unduh CSV — Perbandingan Antar Periode Samurai", perbandingan_samurai.to_csv(index=False).encode("utf-8-sig"),
            "perbandingan_periode_samurai.csv", "text/csv", key="ak_dl_samurai",
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
    # 3b. Matrix Insentif Resmi (Skema v3 — Tiering Sales Retail + Manager)
    # -----------------------------------------------------------------
    st.header("💸 Matrix Insentif Aksesoris")
    st.caption(
        "Berdasarkan referensi resmi terbaru: **Skema Tiering Sales Retail** (GP 30%, insentif "
        "50% dari GP, Gaji Bulanan tetap, THP dihitung langsung per tier) dan **Matrix Insentif "
        "Per Item** (insentif tetap per unit terjual berdasarkan rentang harga jual)."
    )

    st.subheader("📋 Skema Tiering Insentif — Sales Retail")
    st.caption(
        f"10 tier Omzet/Pekan Rp750rb–Rp7,5jt. **Gaji Bulanan tetap "
        f"{la.format_rupiah_id(la.GAJI_BULANAN_SALES_RETAIL)}**, THP = Gaji Bulanan + Insentif/Bulan "
        "— dihitung langsung dari skema resmi, bukan hasil kalibrasi manual."
    )
    sr_tiering = la.matrix_tiering_sales_retail()
    sr_tiering["Status Target (Rp5–8jt)"] = sr_tiering["THP"].apply(
        lambda x: "✅ Dalam target" if 5_000_000 <= x <= 8_000_000 else ("⬇️ Di bawah target" if x < 5_000_000 else "⬆️ Di atas target")
    )
    tampil_sr = sr_tiering.copy()
    for col in ["Tiering Omzet / Pekan", "Omzet / Bulan", "Estimasi GP (30%)", "Insentif / Pekan", "Insentif / Bulan", "Gaji Bulanan", "THP"]:
        tampil_sr[col] = sr_tiering[col].map(la.format_rupiah_id)
    tampil_sr["% Insentif dari GP"] = (sr_tiering["% Insentif dari GP"] * 100).map(lambda x: la.format_percent_id(x, 0))
    st.dataframe(tampil_sr, use_container_width=True, height=420)

    n_luar_target = (~sr_tiering["Status Target (Rp5–8jt)"].str.startswith("✅")).sum()
    if n_luar_target > 0:
        st.caption(
            f"ℹ️ {n_luar_target} dari {len(sr_tiering)} tier berada di luar rentang target Rp5–8jt "
            "(tier terendah & tertinggi sedikit melenceng dari target — bagian dari skema resmi ini, "
            "bukan sesuatu yang dikalibrasi ulang oleh dashboard)."
        )
    st.download_button(
        "⬇️ Unduh CSV — Skema Tiering Sales Retail", sr_tiering.to_csv(index=False).encode("utf-8-sig"),
        "skema_tiering_sales_retail.csv", "text/csv", key="ak_dl_tiering_sr",
    )

    with st.expander("🎁 Matrix Insentif Per Item", expanded=False):
        mi = la.matrix_insentif_per_item()
        tampil_mi = mi.copy()
        tampil_mi["Harga Acuan"] = mi["Harga Acuan"].map(la.format_rupiah_id)
        tampil_mi["Gross Profit"] = mi["Gross Profit"].map(la.format_rupiah_id)
        tampil_mi["Insentif / Item"] = mi["Insentif / Item"].map(la.format_rupiah_id)
        tampil_mi["% Insentif vs GP"] = mi["% Insentif vs GP"].map(lambda x: la.format_percent_id(x, 1))
        tampil_mi["Sisa GP"] = mi["Sisa GP"].map(la.format_rupiah_id)
        st.dataframe(tampil_mi, use_container_width=True)
        st.info(
            f"🧊 **Pengecualian — Produk HYDROGEL**: insentif TETAP "
            f"**{la.format_rupiah_id(la.INSENTIF_HYDROGEL_PER_PCS)}/pcs**, berapa pun harga jualnya "
            "— tidak mengikuti tingkat harga pada tabel di atas."
        )
        st.download_button(
            "⬇️ Unduh CSV — Matrix Insentif Per Item", mi.to_csv(index=False).encode("utf-8-sig"),
            "matrix_insentif_per_item.csv", "text/csv", key="ak_dl_matrix_item",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 3c. Target Pencapaian Penjualan LUNA
    # -----------------------------------------------------------------
    st.header("🎯 Target Pencapaian Penjualan Aksesoris")

    mode_target = st.radio(
        "Target untuk", ["Target LUNA", "Target Semua Aksesoris"], horizontal=True, key="target_mode_pilihan",
    )
    keyword_target = "LUNA" if mode_target == "Target LUNA" else None
    label_target = "LUNA" if keyword_target else "Semua Aksesoris"

    gunakan_samurai = st.checkbox(
        "Gunakan Periode Samurai (kuartalan)", value=True, key="target_luna_pakai_samurai",
        help="Matikan untuk atur tanggal mulai & durasi secara manual (mis. periode 12 bulan lintas kuartal).",
    )

    periode_samurai_target_opsi = [
        "Samurai 39 (Jul–Sep 2026)", "Samurai 40 (Okt–Des 2026)", "Samurai 41 (Jan–Mar 2027)",
        "Samurai 42 (Apr–Jun 2027)", "Samurai 43 (Jul–Sep 2027)", "Samurai 44 (Okt–Des 2027)",
    ]

    if gunakan_samurai:
        t1, t2 = st.columns(2)
        with t1:
            target_rp = st.number_input("Target Omzet Aksesoris (Rp)", min_value=0, value=2_000_000_000, step=100_000_000, format="%d", key="target_luna_rp")
        with t2:
            periode_pilihan_target = st.selectbox("Pilih Periode Samurai", periode_samurai_target_opsi, key="target_luna_periode_samurai")
        tanggal_mulai_target, _tgl_selesai_periode = la.PERIODE_SAMURAI[periode_pilihan_target]
        durasi_bulan_target = 3
        st.caption(f"Periode: {tanggal_mulai_target.strftime('%d %b %Y')} – {_tgl_selesai_periode.strftime('%d %b %Y')} (3 bulan).")
    else:
        t1, t2, t3 = st.columns(3)
        with t1:
            target_rp = st.number_input("Target Omzet Aksesoris (Rp)", min_value=0, value=2_000_000_000, step=100_000_000, format="%d", key="target_luna_rp_manual")
        with t2:
            tanggal_mulai_target = st.date_input("Mulai program", value=pd.Timestamp("2026-08-20"), key="target_luna_mulai")
        with t3:
            durasi_bulan_target = st.number_input("Durasi (bulan)", min_value=1, max_value=60, value=12, step=1, key="target_luna_durasi")

    tprog = la.target_penjualan_brand(
        df, keyword=keyword_target, target=target_rp, tanggal_mulai=tanggal_mulai_target,
        durasi_bulan=int(durasi_bulan_target), tahap_list=[],
    )

    st.caption(
        f"Periode program: {tprog['tanggal_mulai'].strftime('%d %b %Y')} – "
        f"{tprog['tanggal_selesai'].strftime('%d %b %Y')} ({tprog['total_hari_program']} hari). "
        + (
            "Nama barang diidentifikasi mengandung kata \"LUNA\"."
            if keyword_target else
            "Seluruh produk kategori AKSESORIS dihitung (tidak dibatasi brand tertentu)."
        )
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

    st.subheader(f"📋 Monitoring Pencapaian per Cabang — {label_target}")
    st.caption(
        "Target per cabang bisa diedit langsung di tabel bawah ini (default dibagi RATA dari Target Total ÷ "
        f"jumlah cabang). Kolom \"Result\" dihitung otomatis dari data penjualan {label_target} aktual tiap "
        "cabang pada periode ini. Warna: 🔴 <85% · 🟡 85–99% · 🟢 ≥100%."
    )

    daftar_cabang_target = sorted(df["CABANG"].dropna().unique().tolist())
    n_cabang_target = len(daftar_cabang_target) or 1
    seed_target_utama = pd.DataFrame({
        "Cabang": daftar_cabang_target,
        "Target": [target_rp / n_cabang_target] * n_cabang_target,
    })
    edited_target_utama = st.data_editor(
        seed_target_utama, use_container_width=True, hide_index=True, key="target_utama_editor",
        column_config={"Target": st.column_config.NumberColumn("Target (Rp)", min_value=0, step=100_000, format="%d")},
    )
    target_per_cabang_utama = dict(zip(edited_target_utama["Cabang"], edited_target_utama["Target"]))
    total_target_edit = edited_target_utama["Target"].sum()
    if abs(total_target_edit - target_rp) > 1:
        st.caption(
            f"ℹ️ Total target hasil edit ({la.format_rupiah_id(total_target_edit)}) berbeda dari "
            f"Target (Rp) di atas ({la.format_rupiah_id(target_rp)}) — dipakai angka hasil edit ini."
        )

    per_cabang_luna = la.target_brand_per_cabang(
        df, target_total=target_rp, tanggal_mulai=tanggal_mulai_target,
        durasi_bulan=int(durasi_bulan_target), keyword=keyword_target,
        target_per_cabang=target_per_cabang_utama,
    )
    if per_cabang_luna.empty:
        st.info("Tidak ada data cabang untuk periode ini.")
    else:
        per_cabang_luna = per_cabang_luna.sort_values("% Actual", ascending=True).reset_index(drop=True)
        pcl_dgn_total = la.tambah_baris_total(per_cabang_luna)
        styled_pcl = pcl_dgn_total.style.map(
            la.warna_indikator_pencapaian, subset=["% Actual"],
        ).format({
            "Target": la.format_rupiah_id, "Result": la.format_rupiah_id, "Expected": la.format_rupiah_id,
            "% Actual": la.format_percent_id, "% Expected": la.format_percent_id, "GAP": la.format_rupiah_id,
            "Target Kejar Per Hari": la.format_rupiah_id, "Sisa Hari": la.format_int_id,
        })
        st.dataframe(styled_pcl, use_container_width=True, height=530)
        st.caption(
            f"Cabang paling tertinggal: **{per_cabang_luna.iloc[0]['Cabang']}** "
            f"({la.format_percent_id(per_cabang_luna.iloc[0]['% Actual'])} actual) · "
            f"paling unggul: **{per_cabang_luna.iloc[-1]['Cabang']}** "
            f"({la.format_percent_id(per_cabang_luna.iloc[-1]['% Actual'])} actual)."
        )
        st.download_button(
            f"⬇️ Unduh CSV — Monitoring Pencapaian {label_target} per Cabang", pcl_dgn_total.to_csv(index=False).encode("utf-8-sig"),
            f"monitoring_target_{'luna' if keyword_target else 'semua_aksesoris'}_per_cabang.csv", "text/csv", key="ak_dl_target_per_cabang",
        )

    st.divider()

    # -----------------------------------------------------------------
    # 3c2. Monitoring Pencapaian Cabang — Tahap 1
    # -----------------------------------------------------------------
    st.subheader("📍 Monitoring Pencapaian Cabang — Bertahap (menuju Rp 2 Miliar)")
    st.caption(
        "Tanggal 20 Agustus 2026 adalah tanggal produk LUNA barang masuk/mulai didistribusikan ke "
        "seluruh cabang, tapi transaksi riil di tiap cabang bisa mulai beberapa hari setelahnya "
        "(mis. 20–26 Agustus 2026) — sesuaikan \"Tanggal Mulai Tahap 1\" di bawah kalau perlu. "
        "Pencapaian tiap tahap dihitung "
        "KUMULATIF dari tanggal mulai tahap tsb sampai tanggal evaluasi. **Semua tahap khusus LUNA "
        "SELAIN varian Hydrogel** (LUNA Hydrogel punya skema/target tersendiri). Warna: 🔴 <85% · "
        "🟡 85–99% · 🟢 ≥100%. Tahap 1 adalah tahap pertama dari rangkaian tahap menuju target total "
        "Rp 2.000.000.000 — tahap berikutnya (Tahap 2, 3, dst) bisa ditambahkan di bagian bawah begitu "
        "sudah ditentukan."
    )

    tgl_data_terakhir = df["TGL FAKTUR"].max()
    default_tgl_evaluasi = tgl_data_terakhir if pd.notna(tgl_data_terakhir) else pd.Timestamp("2026-08-20")

    dt1, dt2 = st.columns(2)
    with dt1:
        tahap1_tgl_mulai = st.date_input(
            "Tanggal Mulai Tahap 1 (bisa disesuaikan ke tanggal transaksi riil, mis. 20–26 Agustus 2026)",
            value=pd.Timestamp("2026-08-20"), key="tahap1_tgl_mulai",
        )
    with dt2:
        tahap1_tgl_evaluasi = st.date_input(
            "Tanggal Evaluasi untuk seluruh tahap (default: tanggal data terakhir)",
            value=default_tgl_evaluasi, key="tahap1_tgl_evaluasi",
        )
    if pd.Timestamp(tahap1_tgl_mulai) > pd.Timestamp(tahap1_tgl_evaluasi):
        st.warning("⚠️ Tanggal Mulai Tahap 1 lebih besar dari Tanggal Evaluasi — Result akan tampil 0 untuk semua cabang.")

    daftar_cabang_tahap = sorted(la.TARGET_TAHAP1_LUNA_PER_CABANG.keys())

    def _render_tahap_block(nama_tahap: str, target_per_cabang: dict, tanggal_mulai_tahap, key_prefix: str):
        """Render satu blok tahap: tabel monitoring + total + warna + unduh
        + rincian produk per cabang. Mengembalikan (target_total, result_total)."""
        hasil = la.monitoring_tahap_per_cabang(
            df, target_per_cabang, tanggal_mulai=tanggal_mulai_tahap,
            tanggal_evaluasi=tahap1_tgl_evaluasi, keyword="LUNA", keyword_kecuali="HYDROGEL",
        )
        if hasil.empty:
            st.info(f"Tidak ada data untuk {nama_tahap} pada periode ini.")
            return 0.0, 0.0

        hasil = hasil.sort_values("% Actual", ascending=True).reset_index(drop=True)
        dgn_total = la.tambah_baris_total(hasil)
        styled = dgn_total.style.map(la.warna_indikator_pencapaian, subset=["% Actual"]).format({
            "Target": la.format_rupiah_id, "Result": la.format_rupiah_id,
            "% Actual": la.format_percent_id, "GAP": la.format_rupiah_id,
        })
        st.dataframe(styled, use_container_width=True, height=min(80 + 38 * len(dgn_total), 560))
        total_row = dgn_total.iloc[-1]
        st.caption(
            f"Total jaringan {nama_tahap}: {la.format_rupiah_id(total_row['Result'])} dari "
            f"{la.format_rupiah_id(total_row['Target'])} target ({la.format_percent_id(total_row['% Actual'])})."
        )
        st.download_button(
            f"⬇️ Unduh CSV — Monitoring {nama_tahap} per Cabang", dgn_total.to_csv(index=False).encode("utf-8-sig"),
            f"monitoring_{key_prefix}_per_cabang.csv", "text/csv", key=f"{key_prefix}_dl",
        )

        st.markdown(f"###### 🔍 Rincian Produk per Cabang — {nama_tahap}")
        st.caption("Pilih cabang untuk lihat rincian jenis barang LUNA (selain Hydrogel) apa saja yang terjual, dan berapa kuantitasnya.")
        cabang_pilihan_detail = st.selectbox("Pilih cabang", daftar_cabang_tahap, key=f"{key_prefix}_cabang_detail")
        detail_produk = la.detail_produk_brand_cabang(
            df, cabang_pilihan_detail, tanggal_mulai_tahap, tahap1_tgl_evaluasi,
            keyword="LUNA", keyword_kecuali="HYDROGEL",
        )
        if detail_produk.empty:
            st.info(f"Belum ada penjualan LUNA (selain Hydrogel) di cabang **{cabang_pilihan_detail}** pada periode {nama_tahap}.")
        else:
            tampil_detail = detail_produk.copy()
            tampil_detail["Qty"] = detail_produk["Qty"].map(la.format_int_id)
            tampil_detail["Omzet"] = detail_produk["Omzet"].map(la.format_rupiah_id)
            st.dataframe(tampil_detail, use_container_width=True, height=min(80 + 38 * len(detail_produk), 350))
            st.caption(
                f"Total {la.format_int_id(detail_produk['Qty'].sum())} pcs dari "
                f"{len(detail_produk)} jenis produk di cabang {cabang_pilihan_detail}."
            )

        return float(total_row["Target"]), float(total_row["Result"])

    st.markdown("#### Tahap 1")
    st.caption(
        "Target per cabang bisa disesuaikan langsung di tabel bawah ini — sudah terisi dengan nilai "
        "acuan resmi (total Rp 300.006.600), tapi bisa diedit kalau ada revisi."
    )
    seed_tahap1 = pd.DataFrame({
        "Cabang": list(la.TARGET_TAHAP1_LUNA_PER_CABANG.keys()),
        "Target": list(la.TARGET_TAHAP1_LUNA_PER_CABANG.values()),
    })
    edited_tahap1 = st.data_editor(
        seed_tahap1, use_container_width=True, hide_index=True, key="tahap1_target_editor",
        column_config={"Target": st.column_config.NumberColumn("Target (Rp)", min_value=0, step=100_000, format="%d")},
    )
    target_per_cabang_tahap1 = dict(zip(edited_tahap1["Cabang"], edited_tahap1["Target"]))
    st.caption(f"Total target Tahap 1 (hasil edit): {la.format_rupiah_id(edited_tahap1['Target'].sum())}")

    target_kumulatif, result_kumulatif = _render_tahap_block(
        "Tahap 1", target_per_cabang_tahap1, tahap1_tgl_mulai, "tahap1",
    )

    st.divider()

    # -----------------------------------------------------------------
    # Tahap berikutnya (dinamis) — ditambahkan sampai maksimal Rp 2 Miliar
    # -----------------------------------------------------------------
    st.markdown("#### ➕ Tahap Berikutnya")
    st.caption(
        "Tambahkan tahap lanjutan (Tahap 2, 3, dst) begitu targetnya sudah ditentukan — "
        "total seluruh tahap (termasuk Tahap 1) idealnya tidak melebihi Rp 2.000.000.000."
    )
    jumlah_tahap_tambahan = st.number_input(
        "Jumlah tahap tambahan", min_value=0, max_value=6, value=0, step=1, key="jumlah_tahap_tambahan",
    )

    for i in range(int(jumlah_tahap_tambahan)):
        nomor_tahap = i + 2
        with st.expander(f"Tahap {nomor_tahap}", expanded=True):
            n1, n2 = st.columns(2)
            with n1:
                nama_tahap_i = st.text_input("Nama Tahap", value=f"Tahap {nomor_tahap}", key=f"tahap{nomor_tahap}_nama")
            with n2:
                tanggal_mulai_i = st.date_input(
                    "Tanggal Mulai Tahap Ini", value=pd.Timestamp("2026-08-20"), key=f"tahap{nomor_tahap}_mulai",
                )
            target_total_i = st.number_input(
                f"Target Total {nama_tahap_i} (Rp)", min_value=0, value=300_000_000, step=1_000_000,
                format="%d", key=f"tahap{nomor_tahap}_target_total",
            )
            st.caption("Sesuaikan target per cabang di tabel bawah kalau tidak ingin dibagi rata (baris bisa diedit langsung):")
            seed_target_i = pd.DataFrame({
                "Cabang": daftar_cabang_tahap,
                "Target": [target_total_i / len(daftar_cabang_tahap)] * len(daftar_cabang_tahap),
            })
            edited_target_i = st.data_editor(
                seed_target_i, use_container_width=True, hide_index=True, key=f"tahap{nomor_tahap}_editor",
                column_config={"Target": st.column_config.NumberColumn("Target (Rp)", min_value=0, step=100_000, format="%d")},
            )
            target_per_cabang_i = dict(zip(edited_target_i["Cabang"], edited_target_i["Target"]))

            t_i, r_i = _render_tahap_block(nama_tahap_i, target_per_cabang_i, tanggal_mulai_i, f"tahap{nomor_tahap}")
            target_kumulatif += t_i
            result_kumulatif += r_i

    st.divider()

    # -----------------------------------------------------------------
    # Ringkasan Kumulatif Seluruh Tahap
    # -----------------------------------------------------------------
    st.markdown("#### 📊 Ringkasan Kumulatif Seluruh Tahap")
    BATAS_MAKSIMAL_LUNA = 2_000_000_000
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Target Kumulatif (Seluruh Tahap)", la.format_rupiah_id(target_kumulatif))
    k2.metric("Result Kumulatif", la.format_rupiah_id(result_kumulatif))
    k3.metric("% Pencapaian Kumulatif", la.format_percent_id(result_kumulatif / target_kumulatif * 100 if target_kumulatif else 0))
    sisa_menuju_2m = max(BATAS_MAKSIMAL_LUNA - target_kumulatif, 0)
    k4.metric("Sisa Ruang Target (menuju Rp 2 M)", la.format_rupiah_id(sisa_menuju_2m))
    st.progress(min(target_kumulatif / BATAS_MAKSIMAL_LUNA, 1.0) if BATAS_MAKSIMAL_LUNA else 0)
    if target_kumulatif > BATAS_MAKSIMAL_LUNA:
        st.warning(
            f"⚠️ Total target seluruh tahap ({la.format_rupiah_id(target_kumulatif)}) sudah MELEBIHI "
            f"batas maksimal Rp 2.000.000.000 — kelebihan {la.format_rupiah_id(target_kumulatif - BATAS_MAKSIMAL_LUNA)}. "
            "Pertimbangkan mengurangi target salah satu tahap."
        )
    else:
        st.caption(
            f"Total target seluruh tahap masih dalam batas — sisa ruang "
            f"{la.format_rupiah_id(sisa_menuju_2m)} untuk tahap-tahap berikutnya."
        )

    st.divider()

    # -----------------------------------------------------------------
    # 3d. Target Pencapaian Penjualan Parfum UMAIR
    # -----------------------------------------------------------------
    st.header("🌸 Target Pencapaian Penjualan Parfum UMAIR")
    st.caption(
        "Kategori PARFUM diambil dari berkas penjualan yang sama (tidak dibatasi oleh filter "
        "AKSESORIS di atas — Parfum kategori terpisah). Nama barang diidentifikasi mengandung kata \"UMAIR\"."
    )

    df_parfum_jual = la.hanya_kategori(df_semua_kategori, "PARFUM")

    if df_parfum_jual.empty:
        st.info(
            "Tidak ada baris berkategori PARFUM pada berkas penjualan ini — target belum bisa "
            "dihitung. Pastikan berkas yang diunggah mencakup transaksi Parfum."
        )
    else:
        u1, u2, u3 = st.columns(3)
        with u1:
            target_umair_rp = st.number_input("Target Penjualan Parfum UMAIR (Rp)", min_value=0, value=100_000_000, step=10_000_000, format="%d", key="target_umair_rp")
        with u2:
            tanggal_mulai_umair = st.date_input("Mulai program", value=pd.Timestamp("2026-01-01"), key="target_umair_mulai")
        with u3:
            durasi_bulan_umair = st.number_input("Durasi (bulan, maksimal)", min_value=1, max_value=24, value=6, step=1, key="target_umair_durasi")

        tprog_umair = la.target_penjualan_brand(
            df_parfum_jual, keyword="UMAIR", target=target_umair_rp,
            tanggal_mulai=tanggal_mulai_umair, durasi_bulan=int(durasi_bulan_umair),
        )

        st.caption(
            f"Periode program: {tprog_umair['tanggal_mulai'].strftime('%d %b %Y')} – "
            f"{tprog_umair['tanggal_selesai'].strftime('%d %b %Y')} ({tprog_umair['total_hari_program']} hari, "
            f"maksimal {int(durasi_bulan_umair)} bulan)."
        )

        if tprog_umair["hari_berjalan"] == 0:
            st.info("Data faktur belum masuk periode program ini, atau program belum dimulai — indikator belum bisa dihitung.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tercapai", la.format_rupiah_id(tprog_umair["tercapai"]))
            c2.metric("Target s/d Hari Ini", la.format_rupiah_id(tprog_umair["target_sampai_hari_ini"]))
            c3.metric("% Pencapaian (vs target s/d hari ini)", la.format_percent_id(tprog_umair["pct_pencapaian"]))
            c4.metric("% dari Target Penuh", la.format_percent_id(tprog_umair["pct_dari_target_penuh"]))

            st.progress(min(tprog_umair["pct_pencapaian"] / 100, 1.0) if tprog_umair["pct_pencapaian"] else 0)

            st.caption(
                f"Tanggal acuan: **{tprog_umair['tgl_acuan'].strftime('%d %b %Y')}** — hari ke-"
                f"{tprog_umair['hari_berjalan']} dari {tprog_umair['total_hari_program']} hari program "
                f"(maksimal {int(durasi_bulan_umair)} bulan), sisa {la.format_int_id(tprog_umair['sisa_hari'])} hari. "
                f"{la.format_int_id(tprog_umair['jumlah_transaksi'])} baris transaksi UMAIR tercatat."
            )

            if tprog_umair["sisa_hari"] == 0 and tprog_umair["pct_dari_target_penuh"] < 100:
                st.warning(
                    f"⏰ Periode maksimal {int(durasi_bulan_umair)} bulan sudah/hampir habis — pencapaian "
                    f"baru **{la.format_percent_id(tprog_umair['pct_dari_target_penuh'])}** dari target penuh."
                )
            elif tprog_umair["pct_pencapaian"] < 80:
                st.warning(
                    f"⚠️ Pencapaian baru **{la.format_percent_id(tprog_umair['pct_pencapaian'])}** dari target "
                    "yang seharusnya sudah dicapai sampai hari ini — di bawah jalur target."
                )
            else:
                st.success(
                    f"✅ Pencapaian **{la.format_percent_id(tprog_umair['pct_pencapaian'])}** dari target yang "
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
# Layout — SATU HALAMAN (bukan tab terpisah), ketiga dashboard ditampilkan
# berurutan dari atas ke bawah dengan pemisah jelas.
# ---------------------------------------------------------------------------
render_ringkasan_eksekutif()

st.markdown("---")
st.markdown("---")

st.markdown("# 📊 Dashboard Persediaan Aksesoris")
render_persediaan_tab()

st.markdown("---")
st.markdown("---")

st.markdown("# 🌸 Dashboard Persediaan Parfum")
render_persediaan_parfum_tab()

st.markdown("---")
st.markdown("---")

st.markdown("# 🧾 Dashboard Penjualan Aksesoris")
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
