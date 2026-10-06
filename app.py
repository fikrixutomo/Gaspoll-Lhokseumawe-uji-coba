import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import io

# ---------------------------------------------------
# 1. KONFIGURASI HALAMAN & TAMPILAN
# ---------------------------------------------------
st.set_page_config(
    page_title="Dashboard Tunggakan",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJEKSI CUSTOM CSS UNTUK TAMPILAN MODERN ---
st.markdown("""
<style>
    /* Desain Kartu untuk Metrik Utama */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #f0f2f6;
        padding: 5% 10% 5% 10%;
        border-radius: 15px;
        box-shadow: 2px 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 2px 8px 20px rgba(0,0,0,0.15);
    }
    
    /* Warna latar belakang aplikasi yang lebih lembut */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Merapikan jarak Tab */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 25px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 2. PEMUATAN DATA AMAN (OPTIMASI MEMORI)
# ---------------------------------------------------
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "filtered" not in f]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            # Gunakan engine C (standar) dengan mencoba pemisah ';' terlebih dahulu
            df_temp = pd.read_csv(file, sep=";", on_bad_lines='skip', low_memory=True)
            if df_temp.shape[1] <= 1:
                df_temp = pd.read_csv(file, sep=",", on_bad_lines='skip', low_memory=True)
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
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
        
    return pd.DataFrame()

df = load_and_combine_data()

# ---------------------------------------------------
# 3. HEADER DASHBOARD
# ---------------------------------------------------
col_logo, col_title = st.columns([1, 11])
with col_logo:
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-top: -10px;'>🚗</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='color: #1E3A8A; font-weight: 800; margin-bottom: 0px;'>Dashboard Analisis GASPOLL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 1.1em;'>Monitoring interaktif data tunggakan dan tindak lanjut kendaraan secara real-time.</p>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------
# 4. FILTER SIDEBAR
# ---------------------------------------------------
if df.empty:
    st.error("⚠️ File CSV data tidak ditemukan atau gagal dibaca.")
else:
    st.sidebar.markdown("### 🔍 Panel Filter Data")
    
    if 'flag_nomor_hp_valid' in df.columns:
        col_hp_name = 'flag_nomor_hp_valid'
    elif 'status_nomor_hp_valid' in df.columns:
        col_hp_name = 'status_nomor_hp_valid'
    else:
        col_hp_name = None

    selected_cabang = st.sidebar.selectbox("Cabang / Wilayah:", ["Semua Cabang / Wilayah"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])) if 'nama_cabang' in df.columns else "Semua Cabang / Wilayah"
    
    val_samsat = ["Semua Samsat"] + sorted([str(x) for x in df[df['nama_cabang'] == selected_cabang]['nama_samsat'].dropna().unique()]) if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df.columns and 'nama_samsat' in df.columns else ["Semua Samsat"] + sorted([str(x) for x in df['nama_samsat'].dropna().unique()]) if 'nama_samsat' in df.columns else ["Semua Samsat"]
    selected_samsat = st.sidebar.selectbox("Samsat:", val_samsat)
    
    selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])) if 'pemilik_jenis' in df.columns else "Semua Jenis Pemilik"
    
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else None
    
    selected_bayar = st.sidebar.selectbox("Status Pembayaran:", ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])) if 'status_bayar' in df.columns else "Semua Status Bayar"
    selected_tl = st.sidebar.selectbox("Status Tindak Lanjut:", ["Semua Status TL"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])) if 'status_tindak_lanjut' in df.columns else "Semua Status TL"
    
    cari_kata = st.sidebar.text_input("Cari Plat / Nama:")

    # Terapkan Filter
    df_filtered = df.copy()
    if selected_cabang != "Semua Cabang / Wilayah": df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat": df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_pemilik != "Semua Jenis Pemilik": df_filtered = df_filtered[df_filtered['pemilik_jenis'].astype(str) == selected_pemilik]
    if selected_bayar != "Semua Status Bayar": df_filtered = df_filtered[df_filtered['status_bayar'].astype(str) == selected_bayar]
    if selected_tl != "Semua Status TL": df_filtered = df_filtered[df_filtered['status_tindak_lanjut'].astype(str) == selected_tl]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False) if col_perusahaan else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # Kalkulasi Metrik KPI
    total_kendaraan = len(df_filtered)
    if col_hp_name and col_hp_name in df_filtered.columns:
        hp_valid = len(df_filtered[df_filtered[col_hp_name].astype(str).str.upper() == 'VALID'])
    else:
        hp_valid = 0
    persen_hp_valid = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.upper()
        s_tl = df_filtered['status_tindak_lanjut'].astype(str).str.upper()
        
        cond_lunas = s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False)
        cond_blm_lunas = s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)
        cond_sdh_tl = s_tl.str.contains('SUDAH DITINDAKLANJUTI|SUDAH TL|SDH TL', na=False)
        
        jml_lunas = len(df_filtered[cond_lunas])
        jml_belum_lunas = len(df_filtered[cond_blm_lunas])
        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        jml_lunas_sdh_tl = len(df_filtered[cond_lunas & cond_sdh_tl])
        
        conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl * 100) if total_sdh_tl > 0 else 0.0
    else:
        jml_lunas = jml_belum_lunas = conversion_rate = 0

    # ---------------------------------------------------
    # 5. TAMPILAN BERBASIS TAB (TABS)
    # ---------------------------------------------------
    tab_grafik, tab_tabel = st.tabs(["📈 Ringkasan & Grafik", "📋 Tabel Data & Unduh"])

    with tab_grafik:
        st.markdown(f"#### 📌 Ringkasan Indikator Utama ({selected_cabang})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
        c2.metric("Kendaraan Belum Lunas", f"{jml_belum_lunas:,} Unit", delta_color="inverse")
        c3.metric("Nomor HP Valid", f"{persen_hp_valid:.1f}%")
        c4.metric("Efektivitas TL (Conversion)", f"{conversion_rate:.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Grafik
        g1, g2 = st.columns(2)
        with g1:
            if not df_filtered.empty and 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
                df_grouped = df_filtered.groupby(['status_bayar', 'status_tindak_lanjut']).size().reset_index(name='Jumlah')
                fig_bar = px.bar(
                    df_grouped, x='status_bayar', y='Jumlah', color='status_tindak_lanjut',
                    barmode='group', text='Jumlah', title="📊 Status Pembayaran vs Tindak Lanjut",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    template="plotly_white"
                )
                fig_bar.update_traces(textposition='outside')
                fig_bar.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_bar, use_container_width=True)
                
        with g2:
            if not df_filtered.empty and 'pemilik_jenis' in df_filtered.columns:
                fig_pie = px.pie(
                    df_filtered, names='pemilik_jenis', title="🍩 Distribusi Jenis Pemilik", hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    template="plotly_white"
                )
                fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab_tabel:
        st.markdown("#### 📋 Tabel Detail Kendaraan")
        st.info("💡 **Tips:** Anda dapat menggunakan kotak pencarian (search) kecil di pojok kanan atas tabel jika Anda mengarahkan kursor ke area tabel.")
        
        kolom_tampilan = [c for c in [
            'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
            'kode_golongan', 'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
            'status_tindak_lanjut', 'status_bayar', 'prioritas'
        ] if c in df_filtered.columns]
        
        st.dataframe(df_filtered[kolom_tampilan], use_container_width=True, height=450)
        
        st.markdown("### 📥 Opsi Ekspor Data")
        dl1, dl2 = st.columns(2)
        with dl1:
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_filtered.to_excel(writer, index=False, sheet_name='Data_Tunggakan')
                st.download_button("📊 Download Format Excel (.xlsx)", data=buffer.getvalue(), file_name="Hasil_GASPOLL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception:
                st.warning("Pustaka 'openpyxl' diperlukan untuk ekspor Excel.")
        with dl2:
            st.download_button("📄 Download Format CSV (.csv)", data=df_filtered.to_csv(index=False).encode('utf-8'), file_name="Hasil_GASPOLL.csv", mime="text/csv")

# ---------------------------------------------------
# 6. FOOTER
# ---------------------------------------------------
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF; font-size: 0.85em;'>© 2026 JRLX Fikri - Cabang Lhokseumawe. All rights reserved.</p>", unsafe_allow_html=True)
