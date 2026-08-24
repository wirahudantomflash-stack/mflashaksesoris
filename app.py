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
st.sidebar.header("📊 Data Persediaan")
st.sidebar.caption(
    "Sheet \"Daftar Barang dan Jasa\" — boleh berkas khusus aksesoris, atau berkas "
    "SEMUA kategori barang (dipakai bersama untuk tab Persediaan Aksesoris & "
    "Persediaan Parfum, tinggal difilter kategorinya masing-masing)."
)
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
# sidebar atas permintaan — dipakai default tetap di kode saja, supaya
# fokus dashboard murni ke kontrol stok menipis tanpa perlu pengaturan
# tambahan. Bisa dimunculkan lagi kapan saja kalau dibutuhkan.
# Merah: stok <= 25 · Kuning: stok 26-99 · Hijau: stok >= 100
batas_merah, batas_kuning = 25, 99

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
        df_jual_stok = la.finalize_data(raw_aksesoris)
    else:
        nama_bersama = st.session_state.get("nama_cabang_bersama")
        if nama_bersama:
            df_jual_stok = la.finalize_data(raw_aksesoris, cabang_default=nama_bersama)
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
        "Aksesoris yang perlu dipilah LUNA vs Selain LUNA, jadi bagian ini tidak dipisah per brand. "
        "Cross-reference dengan data penjualan (\"Produk Paling Diminati\") juga belum tersedia "
        "karena berkas penjualan aksesoris yang ada belum mencakup transaksi Parfum."
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
    # 2. Indikator Stok & Peta Stok — Cabang × Produk (Parfum)
    # -----------------------------------------------------------------
    # Ambang khusus Parfum (BEDA dari Aksesoris) — skala stok Parfum jauh
    # lebih kecil (median 2, kuartil-3 = 6) dibanding Aksesoris (skala
    # ratusan), jadi memakai ambang 25/99 yang sama akan membuat hampir
    # semua produk Parfum otomatis Merah (86% dari 117 baris, diverifikasi)
    # dan menghilangkan sinyal yang berguna. Diturunkan dari sebaran data
    # Parfum riil, bukan sekadar dipakai ulang dari Aksesoris.
    batas_merah_pf, batas_kuning_pf = 1, 6

    st.header("🚦 2. Indikator Stok Parfum")
    st.caption(
        f"🔴 Merah: stok ≤ {batas_merah_pf} · 🟡 Kuning: stok {batas_merah_pf+1}–{batas_kuning_pf} · "
        f"🟢 Hijau: stok ≥ {batas_kuning_pf+1} (ambang dikalibrasi khusus untuk skala stok Parfum, "
        "beda dari Aksesoris). Stok negatif (anomali sistem) otomatis masuk kategori Merah."
    )

    ind_parfum = lp.indikator_stok_luna(dff_parfum, batas_merah=batas_merah_pf, batas_kuning=batas_kuning_pf)
    if ind_parfum.empty:
        st.info("Tidak ada data produk Parfum pada filter ini.")
    else:
        total = len(ind_parfum)
        n_merah = (ind_parfum["Indikator"] == lp.MERAH).sum()
        n_kuning = (ind_parfum["Indikator"] == lp.KUNING).sum()
        n_hijau = (ind_parfum["Indikator"] == lp.HIJAU).sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Merah", lp.format_int_id(n_merah), lp.format_percent_id(n_merah / total * 100 if total else 0))
        c2.metric("🟡 Kuning", lp.format_int_id(n_kuning), lp.format_percent_id(n_kuning / total * 100 if total else 0))
        c3.metric("🟢 Hijau", lp.format_int_id(n_hijau), lp.format_percent_id(n_hijau / total * 100 if total else 0))

        rc_parfum = lp.ringkasan_indikator_cabang(ind_parfum)
        prioritas_pf = lp.cabang_prioritas(rc_parfum, n=5)
        if not prioritas_pf.empty:
            st.markdown("##### 🚨 Cabang Paling Perlu Perhatian")
            badge_cols = st.columns(len(prioritas_pf))
            for col, (_, row) in zip(badge_cols, prioritas_pf.iterrows()):
                with col:
                    st.error(f"**{row['Cabang']}**\n\n{lp.format_percent_id(row['Porsi Merah (%)'])} Merah")

        st.subheader("Ringkasan per Cabang")
        rc_tampil_pf = rc_parfum.drop(columns=["Jumlah SKU LUNA"])
        styled_rc_pf = lp.styler_gradasi_merah(rc_tampil_pf).format({"Porsi Merah (%)": lp.format_percent_id})
        st.dataframe(styled_rc_pf, use_container_width=True, height=420)
        st.download_button(
            "⬇️ Unduh CSV — Ringkasan Indikator per Cabang (Parfum)", rc_parfum.to_csv(index=False).encode("utf-8-sig"),
            "ringkasan_indikator_parfum_cabang.csv", "text/csv", key="pf_dl_ringkasan",
        )

        st.subheader("🗺️ Peta Stok — Cabang × Produk (Parfum)")
        st.caption("Sel abu-abu \"-\" berarti produk itu tidak tercatat sama sekali di cabang tsb (bukan berarti stoknya 0).")
        pivot_stok_pf, pivot_ind_pf = lp.pivot_heatmap_stok(ind_parfum)
        if pivot_stok_pf.empty:
            st.info("Tidak ada data untuk peta stok pada filter ini.")
        else:
            st.dataframe(lp.styler_heatmap(pivot_stok_pf, pivot_ind_pf), use_container_width=True, height=520)

        st.subheader("Detail per SKU × Cabang")
        filter_indikator_pf = st.multiselect(
            "Filter indikator", [lp.MERAH, lp.KUNING, lp.HIJAU],
            default=[lp.MERAH, lp.KUNING, lp.HIJAU], key="pf_filter_indikator",
        )
        cari_produk_pf = st.text_input("Cari nama produk", key="pf_cari_produk")
        detail_pf = ind_parfum[ind_parfum["Indikator"].isin(filter_indikator_pf)] if filter_indikator_pf else ind_parfum.iloc[0:0]
        if cari_produk_pf:
            detail_pf = detail_pf[detail_pf["Nama Barang"].str.upper().str.contains(cari_produk_pf.upper(), na=False)]
        if detail_pf.empty:
            st.info("Tidak ada produk yang cocok dengan filter indikator/pencarian ini.")
        else:
            tampil_detail_pf = detail_pf.copy()
            tampil_detail_pf["Nilai Stok"] = detail_pf["Nilai Stok"].map(lp.format_rupiah_id)
            st.dataframe(tampil_detail_pf, use_container_width=True, height=420)
            st.download_button(
                "⬇️ Unduh CSV — Detail Indikator Stok Parfum", detail_pf.to_csv(index=False).encode("utf-8-sig"),
                "detail_indikator_parfum.csv", "text/csv", key="pf_dl_detail",
            )

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

    if not ind_parfum.empty:
        rc_pf2 = lp.ringkasan_indikator_cabang(ind_parfum)
        if not rc_pf2.empty:
            prioritas2 = rc_pf2.iloc[0]
            if prioritas2["Porsi Merah (%)"] > 0:
                catatan_pf.append(
                    f"Cabang **{prioritas2['Cabang']}** paling perlu segera direstock Parfum — "
                    f"{lp.format_percent_id(prioritas2['Porsi Merah (%)'])} dari SKU-nya berstatus 🔴 Merah."
                )
        rp_pf2 = lp.ringkasan_indikator_produk(ind_parfum)
        if not rp_pf2.empty:
            produk_kritis_pf = rp_pf2.iloc[0]
            if produk_kritis_pf["Porsi Merah (%)"] >= 50:
                catatan_pf.append(
                    f"Produk **{produk_kritis_pf['Nama Barang']}** berstatus Merah di "
                    f"{lp.format_percent_id(produk_kritis_pf['Porsi Merah (%)'])} dari cabang yang mencatatnya "
                    "— kemungkinan masalah pasokan, bukan cuma satu cabang."
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
tab_persediaan, tab_persediaan_parfum, tab_penjualan_aksesoris = st.tabs([
    "📊 Dashboard Persediaan Aksesoris", "🌸 Dashboard Persediaan Parfum", "🧾 Dashboard Penjualan Aksesoris",
])

with tab_persediaan:
    render_persediaan_tab()

with tab_persediaan_parfum:
    render_persediaan_parfum_tab()

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
