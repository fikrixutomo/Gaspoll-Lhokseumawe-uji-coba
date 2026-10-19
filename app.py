import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import io

# ---------------------------------------------------
# 1. KONFIGURASI HALAMAN & TAMPILAN
# ---------------------------------------------------
st.set_page_config(
    page_title="Dashboard Analisis Tunggakan GASPOLL",
    page_icon="🚗",
    layout="wide"
)

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("<h1>🚗</h1>", unsafe_allow_html=True)
with col_title:
    st.title("Dashboard Analisis GASPOLL — ACEH")
st.markdown("---")

# ---------------------------------------------------
# 2. PEMUATAN DATA AMAN & HEMAT MEMORI
# ---------------------------------------------------
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    file_list = [
        f for f in file_list 
        if "Kode Plat" not in f 
        and "Query result" not in f 
        and "filtered" not in f
    ]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            # Gunakan pemisah ";" terlebih dahulu sesuai format data GASPOL
            df_temp = pd.read_csv(file, sep=";", on_bad_lines='skip', low_memory=True)
            # Jika salah pemisah (terbaca 1 kolom), baca ulang dengan koma
            if df_temp.shape[1] <= 1:
                df_temp = pd.read_csv(file, sep=",", on_bad_lines='skip', low_memory=True)
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca file {file}: {e}")
            
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        
        rename_dict = {}
        if 'samsat_asal_nama' in df_combined.columns and 'nama_samsat' not in df_combined.columns:
            rename_dict['samsat_asal_nama'] = 'nama_samsat'
        if 'status_nomor_hp_valid' in df_combined.columns and 'flag_nomor_hp_valid' not in df_combined.columns:
            rename_dict['status_nomor_hp_valid'] = 'flag_nomor_hp_valid'
            
        if rename_dict:
            df_combined = df_combined.rename(columns=rename_dict)
            
        return df_combined
    else:
        return pd.DataFrame()

df = load_and_combine_data()

# ---------------------------------------------------
# 3. PANEL FILTER SIDEBAR LENGKAP
# ---------------------------------------------------
if df.empty:
    st.error("⚠️ Data CSV tidak ditemukan atau gagal dibaca. Pastikan file CSV ada di folder yang sama.")
else:
    st.sidebar.header("🔍 Filter Data Utama")
    
    # 1. Cabang
    if 'nama_cabang' in df.columns:
        val_cabang = ["Semua Cabang / Wilayah"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Cabang / Wilayah:", val_cabang)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    # 2. Samsat
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            val_samsat = ["Semua Samsat"] + sorted([str(x) for x in df_sub['nama_samsat'].dropna().unique()])
        else:
            val_samsat = ["Semua Samsat"] + sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
        selected_samsat = st.sidebar.selectbox("Samsat:", val_samsat)
    else:
        selected_samsat = "Semua Samsat"

    # 3. Masa Tunggakan
    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        val_tunggakan = ["Semua Kelompok"] + sorted([str(x) for x in df['kelompok_selisih_hari_tunggakan'].dropna().unique()])
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", val_tunggakan)
    else:
        selected_tunggakan = "Semua Kelompok"

    # 4. Status HP
    if 'flag_nomor_hp_valid' in df.columns:
        val_hp = ["Semua Status HP"] + sorted([str(x) for x in df['flag_nomor_hp_valid'].dropna().unique()])
        selected_hp = st.sidebar.selectbox("Status Nomor HP:", val_hp)
    else:
        selected_hp = "Semua Status HP"

    # 5. Status Pembayaran
    if 'status_bayar' in df.columns:
        val_bayar = ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", val_bayar)
    else:
        selected_bayar = "Semua Status Bayar"

    # 6. Status Tindak Lanjut
    if 'status_tindak_lanjut' in df.columns:
        val_tl = ["Semua Status TL"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Tindak Lanjut:", val_tl)
    else:
        selected_tl = "Semua Status TL"

    # 7. Jenis Pemilik
    if 'pemilik_jenis' in df.columns:
        val_pemilik = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", val_pemilik)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # 8. Pencarian Teks
    cari_kata = st.sidebar.text_input("Cari Plat / Nama Pemilik:")

    # ---------------------------------------------------
    # 4. TERAPKAN FILTER KE DATASET
    # ---------------------------------------------------
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
    if selected_hp != "Semua Status HP" and 'flag_nomor_hp_valid' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['flag_nomor_hp_valid'] == selected_hp]
    if selected_bayar != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'] == selected_bayar]
    if selected_tl != "Semua Status TL" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'] == selected_tl]
    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'] == selected_pemilik]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        col_nama = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df_filtered.columns else 'nama_instansi' if 'nama_instansi' in df_filtered.columns else None
        cond_nama = df_filtered[col_nama].astype(str).str.contains(cari_kata, case=False, na=False) if col_nama else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # ---------------------------------------------------
    # 5. RINGKASAN METRIK KPI
    # ---------------------------------------------------
    total_kendaraan = len(df_filtered)

    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        s_tl = df_filtered['status_tindak_lanjut'].astype(str).str.strip().str.upper()

        cond_blm_lunas = s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)
        cond_lunas = s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False) & ~cond_blm_lunas
        cond_sdh_tl = s_tl.str.contains('SUDAH DITINDAKLANJUTI|SUDAH TL|SDH TL', na=False)
        cond_blm_tl = s_tl.str.contains('BELUM DITINDAKLANJUTI|BELUM TL|BLM TL', na=False) & ~cond_sdh_tl

        jml_lunas = len(df_filtered[cond_lunas])
        jml_belum_lunas = len(df_filtered[cond_blm_lunas])
        jml_lunas_sdh_tl = len(df_filtered[cond_lunas & cond_sdh_tl])
        jml_lunas_blm_tl = len(df_filtered[cond_lunas & cond_blm_tl])
        jml_blm_lunas_sdh_tl = len(df_filtered[cond_blm_lunas & cond_sdh_tl])
        jml_blm_lunas_blm_tl = len(df_filtered[cond_blm_lunas & cond_blm_tl])
        
        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl * 100) if total_sdh_tl > 0 else 0.0
    else:
        jml_lunas = jml_belum_lunas = jml_lunas_sdh_tl = jml_lunas_blm_tl = jml_blm_lunas_sdh_tl = jml_blm_lunas_blm_tl = 0
        conversion_rate = 0.0

    hp_valid = len(df_filtered[df_filtered['flag_nomor_hp_valid'].astype(str).str.upper() == 'VALID']) if 'flag_nomor_hp_valid' in df_filtered.columns else 0
    persen_hp_valid = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0.0
    persen_lunas = (jml_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0
    persen_belum_lunas = (jml_belum_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    st.subheader(f"📊 Ringkasan Indikator Utama ({selected_cabang})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    c2.metric("Nomor HP Valid", f"{hp_valid:,} Unit")
    c3.metric("Rasio HP Valid", f"{persen_hp_valid:.1f}%")
    c4.metric("Efektivitas TL", f"{conversion_rate:.1f}%")

    st.markdown("---")

    st.subheader("📌 Analisis Pembayaran & Status TL")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Lunas", f"{jml_lunas:,} Unit", f"{persen_lunas:.1f}%")
    m2.metric("Belum Lunas", f"{jml_belum_lunas:,} Unit", f"{persen_belum_lunas:.1f}%", delta_color="inverse")
    m3.metric("Lunas Sudah TL", f"{jml_lunas_sdh_tl:,} Unit") 
    m4.metric("Lunas Belum TL", f"{jml_lunas_blm_tl:,} Unit")
    m5.metric("Belum Lunas Sudah TL", f"{jml_blm_lunas_sdh_tl:,} Unit")

    if jml_blm_lunas_blm_tl > 0:
        st.warning(f"⚠️ **Beban Kerja:** Terdapat **{jml_blm_lunas_blm_tl:,} Unit** belum lunas & belum TL.")

    st.markdown("---")

    # ---------------------------------------------------
    # 6. VISUALISASI GRAFIK
    # ---------------------------------------------------
    st.subheader("📈 Visualisasi Grafik Analisis")
    
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.markdown("##### Status Pembayaran vs Tindak Lanjut")
        if not df_filtered.empty and 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
            df_grouped = df_filtered.groupby(['status_bayar', 'status_tindak_lanjut']).size().reset_index(name='Jumlah')
            fig_grouped = px.bar(
                df_grouped, x='status_bayar', y='Jumlah', color='status_tindak_lanjut',
                barmode='group', text='Jumlah', color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_grouped.update_traces(textposition='outside')
            st.plotly_chart(fig_grouped, use_container_width=True)
        else:
            st.info("Data tidak mencukupi untuk bagan ini.")

    with row1_col2:
        st.markdown("##### Top 10 Samsat Terbanyak")
        if not df_filtered.empty and 'nama_samsat' in df_filtered.columns:
            samsat_counts = df_filtered['nama_samsat'].value_counts().head(10).reset_index()
            samsat_counts.columns = ['Samsat', 'Jumlah']
            fig_samsat = px.bar(
                samsat_counts, x='Jumlah', y='Samsat', orientation='h', color='Jumlah', 
                color_continuous_scale='Blues', text='Jumlah'
            )
            fig_samsat.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_samsat, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("##### Distribusi Masa Tunggakan")
        if not df_filtered.empty and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
            tunggakan_counts = df_filtered['kelompok_selisih_hari_tunggakan'].value_counts().reset_index()
            tunggakan_counts.columns = ['Masa Tunggakan', 'Jumlah']
            fig_pie = px.pie(
                tunggakan_counts, values='Jumlah', names='Masa Tunggakan', hole=0.35, 
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with row2_col2:
        st.markdown("##### Sebaran Jenis Kepemilikan")
        if not df_filtered.empty and 'pemilik_jenis' in df_filtered.columns:
            pemilik_counts = df_filtered['pemilik_jenis'].value_counts().reset_index()
            pemilik_counts.columns = ['Jenis Pemilik', 'Jumlah']
            fig_donut = px.pie(
                pemilik_counts, values='Jumlah', names='Jenis Pemilik', hole=0.4, 
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------
    # 7. TABEL DETAIL & DOWNLOAD
    # ---------------------------------------------------
    st.subheader("📋 Tabel Detail Kendaraan")
    st.info("💡 Tips: Klik judul kolom untuk mengurutkan (sort) data.")
    
    kolom_tampilan = [c for c in [
        'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
        'kode_golongan', 'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'flag_nomor_hp_valid', 'status_tindak_lanjut', 'status_bayar', 'prioritas'
    ] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    st.markdown("### 📥 Download Hasil Filter Data")
    dl1, dl2 = st.columns(2)
    
    with dl1:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Data_Tunggakan')
            st.download_button(
                label="📊 Download File Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Hasil_Filter_Tunggakan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.warning("Pustaka 'openpyxl' diperlukan untuk ekspor Excel.")
            
    with dl2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File CSV (.csv)",
            data=csv_data,
            file_name="data_tunggakan_filtered.csv",
            mime="text/csv"
        )

# ---------------------------------------------------
# 8. COPYRIGHT FOOTER
# ---------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>© 2026 JRLXFikri - Cabang Lhokseumawe. All rights reserved.</p>",
    unsafe_allow_html=True
)
