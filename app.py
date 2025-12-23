import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
import itertools
from datetime import date, datetime
import calendar

# --- 1. CONFIG & STYLE ---
warnings.filterwarnings('ignore')
st.set_page_config(page_title="HR Dashboard Ultimate", layout="wide")

st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;}
    .stDataFrame {font-size: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 HR Analytics: Performance & Appraisal System")
st.markdown("Fitur: **Slicer Lengkap**, **Logika Libur Otomatis**, **Top Ranking**, dan **Appraisal Calculator**.")
st.markdown("---")

# --- 2. DATA LIBUR NASIONAL & KANTOR (2025) ---
libur_nasional = {
    date(2025, 1, 1): "Tahun Baru Masehi",
    date(2025, 1, 27): "Isra Mikraj Nabi Muhammad SAW",
    date(2025, 1, 28): "Cuti Bersama Imlek", 
    date(2025, 1, 29): "Tahun Baru Imlek 2576 Kongzili",
    date(2025, 3, 29): "Hari Suci Nyepi",
    date(2025, 3, 31): "Idul Fitri 1446H",
    date(2025, 4, 1): "Idul Fitri 1446H",
    date(2025, 4, 2): "Cuti Bersama Idul Fitri",
    date(2025, 4, 3): "Cuti Bersama Idul Fitri",
    date(2025, 4, 4): "Cuti Bersama Idul Fitri",
    date(2025, 4, 18): "Wafat Yesus Kristus (Jumat Agung)",
    date(2025, 4, 20): "Kebangkitan Yesus Kristus (Paskah)",
    date(2025, 5, 1): "Hari Buruh Internasional",
    date(2025, 5, 12): "Hari Raya Waisak",
    date(2025, 5, 29): "Kenaikan Yesus Kristus",
    date(2025, 6, 1): "Hari Lahir Pancasila",
    date(2025, 6, 6): "Hari Raya Idul Adha 1446H",
    date(2025, 6, 27): "Tahun Baru Islam 1447H",
    date(2025, 8, 17): "Hari Kemerdekaan RI",
    date(2025, 9, 5): "Maulid Nabi Muhammad SAW",
    date(2025, 12, 25): "Hari Raya Natal",
    date(2025, 12, 26): "Cuti Bersama Natal"
}

kantor_list = [
    "SCIENTIA", "GADING SERPONG", "CURUG SANGERENG", "KELAPA DUA", 
    "PAGEDANGAN", "MEDANG", "BINONG", "CISAUK", "LEGOK", "BSD", "SERPONG",
    "PT ITOKO SANNIN ABADI", "GLOBAL KONSULTAN", "PT. PRATAMA SOLUTION", "REGUS", 
    "PT. PARAMADAKSA TEKNOLOGI NUSANTARA", "AIMAN - ANUGERAH INOVASI MANUNGGAL", 
    "PT GANITRI NITSAYA HARITA", "PT VALUTAC INOVASI KREASI",
    "PRIME GLOBAL (KAP KANEL & REKAN)", "SANJAYA SOLUSINDO (PT SANJAYA SOLUSI DIGITAL INDONESIA)",
    "PT. SARAHMA GLOBAL INFORMATIKA", "TRIPROCKETS TRAVEL INDONESIA", "THE MAP CONSULTANT",
    "KESSLER EXECUTIVE SEARCH", "APP INTERNATIONAL INDONESIA"
]

# --- 3. FUNGSI SMART LOAD ---
@st.cache_data
def load_data_smart(file):
    # Coba baca 10 baris pertama untuk mencari header
    try:
        df_scan = pd.read_excel(file, header=None, nrows=10)
    except:
        file.seek(0)
        df_scan = pd.read_csv(file, header=None, nrows=10, encoding='utf-8', sep=None, engine='python')
    
    header_idx = 0
    found = False
    for i, row in df_scan.iterrows():
        txt = " ".join(row.astype(str).str.upper().tolist())
        # Logika deteksi header: harus ada kata NAMA dan (MASUK atau ABSEN)
        if "NAMA" in txt and ("MASUK" in txt or "ABSEN" in txt):
            header_idx = i
            found = True
            break
            
    file.seek(0)
    # Jika tidak ketemu header spesifik, default ke 0
    if not found:
        header_idx = 0
        
    try:
        df = pd.read_excel(file, header=header_idx)
    except:
        file.seek(0)
        df = pd.read_csv(file, header=header_idx, encoding='utf-8', sep=None, engine='python')
    return df

# --- 4. SIDEBAR CONTROLS ---
st.sidebar.header("1. Data Source")
uploaded_file = st.sidebar.file_uploader("Upload Report (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    # A. LOAD & MAPPING
    try:
        df_raw = load_data_smart(uploaded_file)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        cols = df_raw.columns.tolist()

        st.sidebar.header("2. Mapping Kolom")
        def find(k): 
            for i,c in enumerate(cols): 
                if any(x in c.upper() for x in k): return i
            return 0

        c_nama = st.sidebar.selectbox("Nama", cols, index=find(['NAMA','NAME']))
        c_masuk = st.sidebar.selectbox("Absen Masuk", cols, index=find(['MASUK','IN']))
        c_keluar = st.sidebar.selectbox("Absen Keluar", cols, index=find(['KELUAR','OUT']))
        c_lokasi = st.sidebar.selectbox("Lokasi", cols, index=find(['LOKASI','LOC']))
        c_catatan = st.sidebar.selectbox("Catatan", cols, index=find(['CATATAN','KET']))

        # B. SETTINGS
        st.sidebar.header("3. Pengaturan")
        target_jam = 8.5
        
        if st.sidebar.button("Proses Dashboard 🚀"):
            st.session_state['processed'] = True 
            
            # --- 5. DATA PROCESSING ---
            with st.spinner("Mengkalkulasi Data, Cross Join & Slicer..."):
                
                # 1. Cleaning Basic
                # Pastikan kolom ada sebelum dipanggil
                df_act = df_raw[[c_nama, c_masuk, c_keluar, c_lokasi, c_catatan]].copy()
                df_act.columns = ['Nama', 'Masuk_Raw', 'Keluar_Raw', 'Lokasi', 'Catatan']

                # 2. Parsing Date
                df_act['Masuk_Obj'] = pd.to_datetime(df_act['Masuk_Raw'], errors='coerce')
                df_act = df_act.dropna(subset=['Masuk_Obj']) 
                
                if df_act.empty:
                    st.error("Format Tanggal/Waktu tidak terdeteksi. Pastikan kolom Absen Masuk berisi format tanggal waktu yang benar.")
                    st.stop()

                df_act['Tanggal'] = df_act['Masuk_Obj'].dt.date
                df_act['Absen Masuk'] = df_act['Masuk_Obj']
                df_act['Absen Keluar'] = pd.to_datetime(df_act['Keluar_Raw'], errors='coerce')
                df_act['Lokasi'] = df_act['Lokasi'].fillna("").astype(str).str.upper()
                df_act['Catatan'] = df_act['Catatan'].fillna("").astype(str).str.upper()

                # 3. Cross Join (Master Data)
                unique_names = df_act['Nama'].unique()
                min_date = df_act['Tanggal'].min()
                max_date = df_act['Tanggal'].max()
                all_dates = pd.date_range(start=min_date, end=max_date)
                
                grid = list(itertools.product(unique_names, all_dates.date))
                df_master = pd.DataFrame(grid, columns=['Nama', 'Tanggal'])
                df_final = pd.merge(df_master, df_act, on=['Nama', 'Tanggal'], how='left')

                # --- 4. LOGIKA STATUS ---
                def get_status(row):
                    tgl = row['Tanggal']
                    cat = str(row['Catatan']).strip().upper() if pd.notnull(row['Catatan']) else ""
                    lok = str(row['Lokasi']).strip().upper() if pd.notnull(row['Lokasi']) else ""
                    ada_absen = pd.notnull(row['Absen Masuk'])
                    
                    is_weekend = tgl.weekday() >= 5 # 5=Sabtu, 6=Minggu

                    # A. CEK HARI LIBUR NASIONAL
                    if tgl in libur_nasional:
                        if ada_absen:
                            is_wfo = any(k in lok for k in kantor_list)
                            return "Lembur Libur (WFO)" if is_wfo else "Lembur Libur (WFH)"
                        return "Libur Nasional"

                    # B. CEK SABTU / MINGGU
                    if is_weekend:
                        if ada_absen:
                            is_wfo = any(k in lok for k in kantor_list)
                            return "Lembur Weekend (WFO)" if is_wfo else "Lembur Weekend (WFH)"
                        return "Libur Akhir Pekan"

                    # C. HARI BIASA
                    keywords_kerja = ['WFH', 'WFO', 'MASUK', 'WORK', '-', 'NAN', 'HADIR', '']
                    # Logika: Jika catatan BUKAN salah satu keyword di atas, anggap Cuti/Izin/Sakit
                    is_catatan_kerja = any(k == cat or k in cat for k in keywords_kerja)
                    
                    if cat != "" and not is_catatan_kerja:
                        return "Cuti" 

                    if ada_absen:
                        is_wfo = any(k in lok for k in kantor_list)
                        return "WFO" if is_wfo else "WFH"
                    
                    return "Alpha"

                df_final['Status'] = df_final.apply(get_status, axis=1)
                
                # Hitung Durasi & Performa
                df_final['Durasi'] = (df_final['Absen Keluar'] - df_final['Absen Masuk']).dt.total_seconds() / 3600
                df_final['Durasi'] = df_final['Durasi'].fillna(0).round(2)
                
                def cek_performa(val):
                    if val == 0: return "-"
                    return "Under" if val < target_jam else "On Track"
                df_final['Performa'] = df_final['Durasi'].apply(cek_performa)

                # --- EKSTRAKSI WAKTU UNTUK SLICER ---
                df_final['Tanggal_DT'] = pd.to_datetime(df_final['Tanggal'])
                df_final['Tahun'] = df_final['Tanggal_DT'].dt.year
                df_final['Bulan'] = df_final['Tanggal_DT'].dt.month_name()
                df_final['Bulan_Angka'] = df_final['Tanggal_DT'].dt.month
                df_final['Minggu_Ke'] = df_final['Tanggal_DT'].dt.isocalendar().week

                st.session_state['df_full'] = df_final
                st.success("Data Berhasil di Proses!")

    except Exception as e:
        st.error(f"Terjadi Kesalahan saat memproses data: {e}")
        st.write("Tips: Pastikan file Excel tidak dikunci password dan memiliki header kolom.")

# --- 6. VISUALISASI & SLICER ---
if 'df_full' in st.session_state:
    df = st.session_state['df_full']
    
    # --- SLICER (SIDEBAR) ---
    st.sidebar.markdown("---")
    st.sidebar.header("4. Filter Data (Slicer)")
    
    # 1. Tahun
    sel_tahun = st.sidebar.multiselect("Pilih Tahun", sorted(df['Tahun'].unique()), default=sorted(df['Tahun'].unique()))
    
    # 2. Bulan
    df_bulan_unik = df[['Bulan', 'Bulan_Angka']].drop_duplicates().sort_values('Bulan_Angka')
    sel_bulan = st.sidebar.multiselect("Pilih Bulan", df_bulan_unik['Bulan'].tolist(), default=df_bulan_unik['Bulan'].tolist())
    
    # 3. Minggu (Slider Range)
    # Handle jika data kosong atau hanya 1 minggu
    if not df.empty:
        min_week = int(df['Minggu_Ke'].min())
        max_week = int(df['Minggu_Ke'].max())
        if min_week == max_week:
            sel_minggu = (min_week, max_week)
        else:
            sel_minggu = st.sidebar.slider("Pilih Range Minggu Ke-", min_value=min_week, max_value=max_week, value=(min_week, max_week))
    else:
        sel_minggu = (0,0)
        
    # 4. Karyawan
    sel_karyawan = st.sidebar.multiselect("Pilih Karyawan", sorted(df['Nama'].unique()), default=sorted(df['Nama'].unique()))

    # --- FILTERING ---
    if not sel_tahun: sel_tahun = df['Tahun'].unique()
    if not sel_bulan: sel_bulan = df['Bulan'].unique()
    if not sel_karyawan: sel_karyawan = df['Nama'].unique()
    
    mask = (df['Tahun'].isin(sel_tahun) & 
            df['Bulan'].isin(sel_bulan) & 
            (df['Minggu_Ke'] >= sel_minggu[0]) & (df['Minggu_Ke'] <= sel_minggu[1]) & 
            df['Nama'].isin(sel_karyawan))
    
    df_filtered = df[mask].copy()

    # --- TAB MENU ---
    tab1, tab2 = st.tabs(["📈 Dashboard Monitoring", "📝 Kalkulator Appraisal"])
    
    # === TAB 1: DASHBOARD UTAMA ===
    with tab1:
        if df_filtered.empty:
            st.warning("Data kosong dengan filter ini.")
        else:
            # --- A. KPI CARDS UTAMA ---
            total_karyawan = df_filtered['Nama'].nunique()
            # Rata-rata jam kerja global (hanya menghitung yg masuk)
            avg_jam_global = df_filtered[df_filtered['Durasi']>0]['Durasi'].mean()
            # Handle NaN jika tidak ada data durasi
            if pd.isna(avg_jam_global): avg_jam_global = 0
            
            total_under = len(df_filtered[df_filtered['Performa'] == 'Under'])
            
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            k1.metric("Total Karyawan", total_karyawan)
            k2.metric("Avg Jam Kerja", f"{avg_jam_global:.2f} Jam")
            k3.metric("WFO Total", len(df_filtered[df_filtered['Status'].str.contains('WFO', na=False)]))
            k4.metric("WFH Total", len(df_filtered[df_filtered['Status'].str.contains('WFH', na=False)]))
            k5.metric("Alpha", len(df_filtered[df_filtered['Status'] == 'Alpha']), delta_color="inverse")
            k6.metric("Underperformance", f"{total_under}", delta="< 8.5 Jam", delta_color="inverse")

            st.markdown("---")

            # --- B. CHARTS ROW 1 ---
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("1. Komposisi Kehadiran")
                color_map = {
                    "Alpha": "#FF5252", "WFH": "#2196F3", "WFO": "#4CAF50", 
                    "Cuti": "#FFC107", "Libur Nasional": "#9E9E9E",
                    "Libur Akhir Pekan": "#BDBDBD", "Lembur Weekend (WFO)": "#1B5E20",
                    "Lembur Weekend (WFH)": "#0D47A1", "Lembur Libur (WFO)": "#1B5E20",
                    "Lembur Libur (WFH)": "#0D47A1"
                }
                df_pie = df_filtered['Status'].value_counts().reset_index()
                df_pie.columns = ['Status', 'Jumlah']
                fig_pie = px.pie(df_pie, values='Jumlah', names='Status', color='Status', color_discrete_map=color_map, hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                st.subheader("2. Monitoring Kepatuhan Bulanan")
                df_monthly = df_filtered[df_filtered['Durasi']>0].groupby('Bulan_Angka')['Durasi'].mean().reset_index()
                # Jika df_monthly kosong, skip
                if not df_monthly.empty:
                    df_monthly['Bulan'] = df_monthly['Bulan_Angka'].apply(lambda x: calendar.month_name[x])
                    fig_monthly = px.line(df_monthly, x='Bulan', y='Durasi', markers=True, title="Trend Rata-rata Jam Kerja per Bulan")
                    fig_monthly.add_hline(y=8.5, line_width=2, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_monthly, use_container_width=True)
                else:
                    st.info("Belum ada data durasi untuk grafik bulanan.")

            # --- C. CHARTS ROW 2 ---
            c3, c4 = st.columns(2)
            with c3:
                st.subheader("3. Monitoring Jam Kerja Harian")
                df_hadir = df_filtered[df_filtered['Durasi'] > 0].sort_values('Tanggal')
                if not df_hadir.empty:
                    fig_line = px.line(df_hadir, x='Tanggal', y='Durasi', color='Nama', markers=True)
                    fig_line.add_hline(y=8.5, line_width=2, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("Belum ada data kehadiran harian.")
            
            with c4:
                st.subheader("4. Top Ranking")
                tab_rank1, tab_rank2 = st.tabs(["Rajin (Hadir)", "Bolos (Absen)"])
                
                with tab_rank1:
                    df_present = df_filtered[df_filtered['Status'].str.contains('WF|Lembur', na=False)].groupby('Nama').size().reset_index(name='Jumlah Hadir')
                    df_present = df_present.sort_values('Jumlah Hadir', ascending=False).head(3)
                    if not df_present.empty:
                        fig_top3_hadir = px.bar(df_present, x='Jumlah Hadir', y='Nama', orientation='h', color_discrete_sequence=['#4CAF50'])
                        st.plotly_chart(fig_top3_hadir, use_container_width=True)
                    else:
                        st.write("-")
                    
                with tab_rank2:
                    df_absent = df_filtered[df_filtered['Status'].isin(['Alpha', 'Cuti'])].groupby('Nama').size().reset_index(name='Jumlah Absen')
                    df_absent = df_absent.sort_values('Jumlah Absen', ascending=False).head(3)
                    if not df_absent.empty:
                        fig_top3_absen = px.bar(df_absent, x='Jumlah Absen', y='Nama', orientation='h', color_discrete_sequence=['#FF5252'])
                        st.plotly_chart(fig_top3_absen, use_container_width=True)
                    else:
                        st.success("Tidak ada ketidakhadiran (Alpha/Cuti).")

            # --- D. TABEL DETAIL (EXPANDER) ---
            st.markdown("---")
            with st.expander("📂 Buka/Tutup Detail Data Karyawan", expanded=False):
                def highlight_under(row):
                    if row['Durasi'] > 0 and row['Durasi'] < 8.5: return ['background-color: #ffcdd2'] * len(row)
                    if row['Status'] == 'Alpha': return ['background-color: #ffebee'] * len(row)
                    return [''] * len(row)
                
                try:
                    st.dataframe(df_filtered[['Tanggal', 'Nama', 'Status', 'Durasi', 'Performa', 'Masuk_Raw', 'Keluar_Raw']].style.apply(highlight_under, axis=1), use_container_width=True)
                except:
                    st.dataframe(df_filtered[['Tanggal', 'Nama', 'Status', 'Durasi', 'Performa']], use_container_width=True)

    # === TAB 2: APPRAISAL CALCULATOR ===
    with tab2:
        st.header("🧮 Simulasi Penilaian (Per Karyawan)")
        st.info("Pilih karyawan untuk menghitung skor appraisal berdasarkan rumus bobot.")
        
        # Dropdown Karyawan
        list_karyawan_app = sorted(df['Nama'].unique())
        # Proteksi jika list kosong
        if not list_karyawan_app:
            st.warning("Data karyawan tidak ditemukan.")
            target_emp = None
        else:
            target_emp = st.selectbox("Pilih Karyawan:", list_karyawan_app)
        
        if target_emp:
            # Ambil data Full sesuai filter Slicer (Periode penilaian = Periode slicer)
            df_emp = df_filtered[df_filtered['Nama'] == target_emp]
            
            if df_emp.empty:
                st.warning("Tidak ada data untuk karyawan ini di periode yang dipilih.")
            else:
                total_days = len(df_emp)
                # Hari libur tidak mengurangi kuota kerja wajib
                libur_count = len(df_emp[df_emp['Status'].isin(['Libur Nasional', 'Libur Akhir Pekan'])])
                
                wajib_kerja = total_days - libur_count
                if wajib_kerja <= 0: wajib_kerja = 1
                
                # Hitung Alpha
                alpha_count = len(df_emp[df_emp['Status'] == 'Alpha'])
                
                # 1. Skor Absensi (10%)
                score_absensi = ((wajib_kerja - alpha_count) / wajib_kerja) * 100
                if score_absensi < 0: score_absensi = 0
                
                # 2. Skor WFO (20%) - Target dinamis 80% dari hari kerja
                wfo_count = len(df_emp[df_emp['Status'].str.contains('WFO', na=False)])
                target_wfo_dinamis = int(wajib_kerja * 0.8) 
                if target_wfo_dinamis < 1: target_wfo_dinamis = 1
                
                score_wfo = (wfo_count / target_wfo_dinamis) * 100
                if score_wfo > 100: score_wfo = 100

                # TAMPILAN OTOMATIS
                c1, c2 = st.columns(2)
                c1.metric("Skor Absensi (Bobot 10%)", f"{score_absensi:.1f}", f"Alpha: {alpha_count}")
                c2.metric("Skor WFO (Bobot 20%)", f"{score_wfo:.1f}", f"WFO: {wfo_count} dari target {target_wfo_dinamis}")
                
                st.markdown("#### Input Penilaian Manual (Atasan)")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    v_kom = st.slider("1. Komunikasi (10%)", 0, 100, 80)
                    v_kpi = st.slider("2. KPI Achievement (20%)", 0, 120, 100)
                    v_skill = st.slider("4. Problem Solving (10%)", 0, 100, 75)
                with col_m2:
                    v_kual = st.slider("6. Kualitas Kerja (15%)", 0, 100, 80)
                    v_proj = st.slider("7. Project (15%)", 0, 100, 70)
                    
                # Rumus Final
                final_score = (score_absensi*0.1) + (score_wfo*0.2) + (v_kom*0.1) + (min(v_kpi,100)*0.2) + (v_skill*0.1) + (v_kual*0.15) + (v_proj*0.15)
                
                # Grade
                if final_score >= 90: grade = "A (Outstanding)"
                elif final_score >= 80: grade = "B (Exceeds)"
                elif final_score >= 70: grade = "C (Meets)"
                elif final_score >= 50: grade = "D (Improvement)"
                else: grade = "E (Unsatisfactory)"

                st.markdown("---")
                st.subheader(f"🏆 HASIL APPRAISAL: {final_score:.2f}")
                st.caption(f"Grade: {grade}")
                
                # Radar Chart
                df_radar = pd.DataFrame({
                    'Kategori': ['Absensi', 'WFO', 'Komunikasi', 'KPI', 'Skill', 'Kualitas', 'Project'],
                    'Nilai': [score_absensi, score_wfo, v_kom, min(v_kpi,100), v_skill, v_kual, v_proj]
                })
                fig_radar = px.line_polar(df_radar, r='Nilai', theta='Kategori', line_close=True)
                fig_radar.update_traces(fill='toself')
                st.plotly_chart(fig_radar, use_container_width=True)

else:
    st.info("👈 Silakan upload file Excel absensi Anda.")