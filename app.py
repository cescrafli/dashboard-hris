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
    div[data-testid="stMetricValue"] {font-size: 18px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 HR Analytics: Performance & Appraisal System")
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
    "KESSLER EXECUTIVE SEARCH", "APP INTERNATIONAL INDONESIA", "PT WIAGA INTECH NUSANTARA",
    "PARAMADAKSA TEKNOLOGI NUSANTARA NEXSOFT"
]

# --- 3. FUNGSI SMART LOAD ---
@st.cache_data
def load_data_smart(file):
    try:
        df_scan = pd.read_excel(file, header=None, nrows=10)
    except:
        file.seek(0)
        df_scan = pd.read_csv(file, header=None, nrows=10, encoding='utf-8', sep=None, engine='python')
    
    header_idx = 0
    found = False
    for i, row in df_scan.iterrows():
        txt = " ".join(row.astype(str).str.upper().tolist())
        if "NAMA" in txt and ("MASUK" in txt or "ABSEN" in txt):
            header_idx = i
            found = True
            break
            
    file.seek(0)
    if not found:
        header_idx = 0
        
    try:
        df = pd.read_excel(file, header=header_idx)
    except:
        file.seek(0)
        df = pd.read_csv(file, header=header_idx, encoding='utf-8', sep=None, engine='python')
    return df

# --- HELPER: SYNC SLIDER & INPUT ---
def make_synced_input(label, key_prefix, default_val=80):
    key_val = f"{key_prefix}_val"
    if key_val not in st.session_state:
        st.session_state[key_val] = default_val

    def update_from_slider():
        st.session_state[key_val] = st.session_state[f"{key_prefix}_slider"]

    def update_from_number():
        st.session_state[key_val] = st.session_state[f"{key_prefix}_number"]

    c1, c2 = st.columns([3, 1])
    with c1:
        st.slider(
            label=f"{label} (Geser)",
            min_value=0, max_value=100,
            value=st.session_state[key_val],
            key=f"{key_prefix}_slider",
            on_change=update_from_slider
        )
    with c2:
        st.number_input(
            label="Ketik Nilai",
            min_value=0, max_value=100,
            value=st.session_state[key_val],
            key=f"{key_prefix}_number",
            on_change=update_from_number
        )
    
    return st.session_state[key_val]

# --- 4. SIDEBAR CONTROLS ---
st.sidebar.header("1. Data Source")
# UPDATE: Tambahkan accept_multiple_files=True
uploaded_files = st.sidebar.file_uploader("Upload Report (Bisa Pilih Banyak File)", type=["xlsx", "csv"], accept_multiple_files=True)

if uploaded_files:
    # A. LOAD & MAPPING (MULTI-FILE LOGIC)
    all_dfs = []
    
    # Loop setiap file yang diupload
    for file in uploaded_files:
        try:
            df_temp = load_data_smart(file)
            # Opsional: Bersihkan nama kolom agar konsisten saat digabung
            df_temp.columns = [str(c).strip() for c in df_temp.columns]
            all_dfs.append(df_temp)
        except Exception as e:
            st.sidebar.error(f"Gagal load file: {file.name}. Error: {e}")

    if all_dfs:
        # Gabungkan semua file menjadi satu DataFrame besar
        df_raw = pd.concat(all_dfs, ignore_index=True)
        
        # --- PROSES SEPERTI BIASA SETELAH DIGABUNG ---
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        cols = df_raw.columns.tolist()

        st.sidebar.header("2. Mapping Kolom")
        def find(k): 
            for i,c in enumerate(cols): 
                if any(x in c.upper() for x in k): return i
            return 0

        # Selectbox mengambil kolom dari data gabungan
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
            with st.spinner("Menggabungkan Data & Kalkulasi..."):
                
                # 1. Cleaning Basic
                df_act = df_raw[[c_nama, c_masuk, c_keluar, c_lokasi, c_catatan]].copy()
                df_act.columns = ['Nama', 'Masuk_Raw', 'Keluar_Raw', 'Lokasi', 'Catatan']

                # 2. Parsing Date
                df_act['Masuk_Obj'] = pd.to_datetime(df_act['Masuk_Raw'], errors='coerce')
                df_act = df_act.dropna(subset=['Masuk_Obj']) 
                
                if df_act.empty:
                    st.error("Format Tanggal/Waktu tidak terdeteksi. Pastikan format Excel seragam.")
                    st.stop()

                df_act['Tanggal'] = df_act['Masuk_Obj'].dt.date
                df_act['Absen Masuk'] = df_act['Masuk_Obj']
                df_act['Absen Keluar'] = pd.to_datetime(df_act['Keluar_Raw'], errors='coerce')
                df_act['Lokasi'] = df_act['Lokasi'].fillna("").astype(str).str.upper()
                df_act['Catatan'] = df_act['Catatan'].fillna("").astype(str).str.upper()

                # 3. Cross Join (Master Data)
                # Mencari range tanggal min/max dari KESELURUHAN file
                unique_names = df_act['Nama'].unique()
                min_date = df_act['Tanggal'].min()
                max_date = df_act['Tanggal'].max()
                all_dates = pd.date_range(start=min_date, end=max_date)
                
                grid = list(itertools.product(unique_names, all_dates.date))
                df_master = pd.DataFrame(grid, columns=['Nama', 'Tanggal'])
                
                # Hapus duplikat jika ada file yang overlapping (tanggal sama diupload 2x)
                df_act = df_act.drop_duplicates(subset=['Nama', 'Tanggal'], keep='last')
                
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
                st.success(f"Berhasil menggabungkan {len(uploaded_files)} file!")

    else:
        st.sidebar.warning("File kosong atau format tidak didukung.")

# --- 6. VISUALISASI & SLICER ---
if 'df_full' in st.session_state:
    df = st.session_state['df_full']
    
    # --- SLICER (SIDEBAR) ---
    st.sidebar.markdown("---")
    st.sidebar.header("4. Filter Data")
    
    # 1. Tahun
    sel_tahun = st.sidebar.multiselect("Tahun", sorted(df['Tahun'].unique()), default=sorted(df['Tahun'].unique()))
    
    # 2. Bulan
    df_bulan_unik = df[['Bulan', 'Bulan_Angka']].drop_duplicates().sort_values('Bulan_Angka')
    sel_bulan = st.sidebar.multiselect("Bulan", df_bulan_unik['Bulan'].tolist(), default=df_bulan_unik['Bulan'].tolist())
    
    # 3. Minggu (Slider Range)
    if not df.empty:
        min_week = int(df['Minggu_Ke'].min())
        max_week = int(df['Minggu_Ke'].max())
        if min_week == max_week:
            sel_minggu = (min_week, max_week)
        else:
            sel_minggu = st.sidebar.slider("Range Minggu Ke-", min_value=min_week, max_value=max_week, value=(min_week, max_week))
    else:
        sel_minggu = (0,0)
        
    # 4. Karyawan
    sel_karyawan = st.sidebar.multiselect("List Karyawan", sorted(df['Nama'].unique()), default=sorted(df['Nama'].unique()))

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
            total_karyawan = df_filtered['Nama'].nunique()
            avg_jam_global = df_filtered[df_filtered['Durasi']>0]['Durasi'].mean()
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

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Pie Chart Kehadiran")
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
                st.subheader("Monitoring Kepatuhan Bulanan")
                df_monthly = df_filtered[df_filtered['Durasi']>0].groupby('Bulan_Angka')['Durasi'].mean().reset_index()
                if not df_monthly.empty:
                    df_monthly['Bulan'] = df_monthly['Bulan_Angka'].apply(lambda x: calendar.month_name[x])
                    fig_monthly = px.line(df_monthly, x='Bulan', y='Durasi', markers=True, title="Trend Rata-rata Jam Kerja per Bulan")
                    fig_monthly.add_hline(y=8.5, line_width=2, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_monthly, use_container_width=True)
                else:
                    st.info("Belum ada data durasi untuk grafik bulanan.")

            c3, c4 = st.columns(2)
            with c3:
                st.subheader("Monitoring Jam Kerja Harian")
                df_hadir = df_filtered[df_filtered['Durasi'] > 0].sort_values('Tanggal')
                if not df_hadir.empty:
                    fig_line = px.line(df_hadir, x='Tanggal', y='Durasi', color='Nama', markers=True)
                    fig_line.add_hline(y=8.5, line_width=2, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("Belum ada data kehadiran harian.")
            
            with c4:
                st.subheader("Top Ranking")
                tab_rank1, tab_rank2 = st.tabs(["Kehadiran", "Ketidakhadiran"])
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

            st.markdown("---")
            with st.expander("📂 Detail Data Karyawan", expanded=False):
                cols_view = ['Tanggal', 'Nama', 'Status', 'Durasi', 'Performa', 'Masuk_Raw', 'Keluar_Raw']
                df_detail = df_filtered[cols_view].copy()
                df_detail['Tanggal'] = df_detail['Tanggal'].astype(str)

                total_durasi = df_detail['Durasi'].sum()
                total_hadir = len(df_detail[df_detail['Status'].str.contains('WFO|WFH|Lembur', na=False)])
                
                row_total = pd.DataFrame({
                    'Tanggal': ['TOTAL KESELURUHAN'],
                    'Nama': ['-'], 
                    'Status': [f"Hadir: {total_hadir} Hari"], 
                    'Durasi': [total_durasi], 
                    'Performa': ['-'],
                    'Masuk_Raw': ['-'],
                    'Keluar_Raw': ['-']
                })

                df_final_view = pd.concat([df_detail, row_total], ignore_index=True)

                def highlight_style(row):
                    if row['Tanggal'] == 'TOTAL KESELURUHAN':
                        return ['font-weight: bold; background-color: #cfd8dc; color: black'] * len(row)
                    styles = [''] * len(row)
                    if row['Durasi'] > 0 and row['Durasi'] < 8.5:
                        styles = ['background-color: #ffcdd2'] * len(row)
                    elif row['Status'] == 'Alpha':
                        styles = ['background-color: #ffebee'] * len(row)
                    return styles
                
                try:
                    st.dataframe(df_final_view.style.apply(highlight_style, axis=1).format({'Durasi': '{:.2f}'}), use_container_width=True)
                except:
                    st.dataframe(df_final_view)

    # === TAB 2: UPDATE APPRAISAL CALCULATOR (LOGIC PERBAIKAN DI SINI) ===
    with tab2:
        st.header("🧮 Penilaian Kinerja Appraisal")
        st.info("Pilih karyawan untuk menghitung skor appraisal secara otomatis dan manual.")
        
        list_karyawan_app = sorted(df['Nama'].unique())
        
        col_sel_emp, col_dummy = st.columns([1, 2])
        with col_sel_emp:
            target_emp = st.selectbox("Pilih Karyawan:", list_karyawan_app) if list_karyawan_app else None
        
        if target_emp:
            # Filter Data Khusus Karyawan Terpilih
            df_emp = df_filtered[df_filtered['Nama'] == target_emp].copy()
            
            if df_emp.empty:
                st.warning("Tidak ada data untuk karyawan ini di periode yang dipilih.")
            else:
                st.markdown("### A. Penilaian by System (Bobot 65%)")
                
                # --- 1. KPI ACHIEVEMENT (20%) ---
                total_hari_hadir = len(df_emp[df_emp['Durasi'] > 0])
                score_kpi_raw = (total_hari_hadir / 20) * 100
                score_kpi = 100 if score_kpi_raw > 100 else score_kpi_raw
                
                # --- 2. PROJECT DEVELOPMENT (15%) [LOGIC BARU] ---
                # Logic: Hitung nilai harian. Jika absen di hari kerja = 0.
                list_skor_project = []
                
                for idx, row in df_emp.iterrows():
                    durasi = row['Durasi']
                    status = row['Status']
                    
                    # Cek apakah hari ini "Countable" (Wajib dinilai)
                    # Hari yang TIDAK dinilai: Libur/Weekend TAPI tidak masuk (Durasi 0)
                    is_holiday_weekend = any(x in status for x in ["Libur", "Akhir Pekan"])
                    
                    if is_holiday_weekend and durasi == 0:
                        continue # Skip, jangan masukkan ke rata-rata (Exempt)
                    
                    # Hitung skor harian
                    if durasi >= 8.5:
                        skor_harian = 100
                    else:
                        skor_harian = (durasi / 8.5) * 100
                    
                    # Note: Jika Alpha (Status bukan Libur tapi Durasi 0), skor_harian otomatis 0
                    list_skor_project.append(skor_harian)
                
                if len(list_skor_project) > 0:
                    score_project = sum(list_skor_project) / len(list_skor_project)
                else:
                    score_project = 0
                    
                # Pembulatan agar rapi
                score_project = round(score_project, 2)

                # --- 3. KELENGKAPAN ABSENSI (10%) ---
                total_days = len(df_emp)
                libur_count = len(df_emp[df_emp['Status'].isin(['Libur Nasional', 'Libur Akhir Pekan'])])
                wajib_kerja = total_days - libur_count
                if wajib_kerja < 1: wajib_kerja = 1
                
                alpha_count = len(df_emp[df_emp['Status'] == 'Alpha'])
                score_absensi = ((wajib_kerja - alpha_count) / wajib_kerja) * 100
                if score_absensi < 0: score_absensi = 0

                # --- 4. WFO Presence (20%) ---
                jumlah_minggu = df_emp['Minggu_Ke'].nunique()
                if jumlah_minggu < 1: jumlah_minggu = 1
                
                target_wfo_total = jumlah_minggu * 4
                actual_wfo = len(df_emp[df_emp['Status'].str.contains('WFO', na=False)])
                
                score_wfo_raw = (actual_wfo / target_wfo_total) * 100
                score_wfo = 100 if score_wfo_raw > 100 else score_wfo_raw

                # TAMPILAN SYSTEM SCORE
                c_sys1, c_sys2, c_sys3, c_sys4 = st.columns(4)
                c_sys1.metric("2. KPI (20%)", f"{score_kpi:.1f}", f"{total_hari_hadir}/20 Hari")
                # Update tampilan metrik Project
                c_sys2.metric("7. Project (15%)", f"{score_project:.1f}", "Rata-rata Skor")
                c_sys3.metric("3. Absensi (10%)", f"{score_absensi:.1f}", f"Alpha: {alpha_count}")
                c_sys4.metric("5. WFO (20%)", f"{score_wfo:.1f}", f"{actual_wfo}/{target_wfo_total} Hari")

                st.markdown("---")
                st.markdown("### B. Penilaian Manual (Bobot 35%)")
                st.caption("Geser slider atau ketik angka (0-100). Keduanya sinkron.")

                # INPUT MANUAL DENGAN FUNGSI SYNC
                # 1. Komunikasi (10%)
                st.markdown("**1. Komunikasi (10%)**")
                val_komunikasi = make_synced_input("Skor Komunikasi", "komunikasi", 80)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 4. Problem Solving (10%)
                st.markdown("**4. Keahlian / Problem Solving (10%)**")
                val_problem_solving = make_synced_input("Skor Problem Solving", "problem", 75)

                st.markdown("<br>", unsafe_allow_html=True)

                # 6. Kualitas Kerja (15%)
                st.markdown("**6. Kualitas Kerja (15%)** - Inisiatif, laporan, diskusi, responsive")
                val_kualitas = make_synced_input("Skor Kualitas", "kualitas", 80)

                # --- FINAL CALCULATION ---
                final_score = (
                    (val_komunikasi * 0.10) +       # Manual 1
                    (score_kpi * 0.20) +            # System 2
                    (score_absensi * 0.10) +        # System 3
                    (val_problem_solving * 0.10) +  # Manual 4
                    (score_wfo * 0.20) +            # System 5
                    (val_kualitas * 0.15) +         # Manual 6
                    (score_project * 0.15)          # System 7
                )

                # Grade Logic
                if final_score >= 90: grade = "A (Outstanding)"
                elif final_score >= 80: grade = "B (Exceeds)"
                elif final_score >= 70: grade = "C (Meets)"
                elif final_score >= 50: grade = "D (Improvement)"
                else: grade = "E (Unsatisfactory)"

                st.markdown("---")
                st.subheader(f"🏆 TOTAL SCORE: {final_score:.2f}")
                st.info(f"Grade: **{grade}**")

                # RADAR CHART
                df_radar = pd.DataFrame({
                    'Kategori': ['Komunikasi (10%)', 'KPI (20%)', 'Absensi (10%)', 'Prob. Solving (10%)', 'WFO (20%)', 'Kualitas (15%)', 'Project (15%)'],
                    'Nilai': [val_komunikasi, score_kpi, score_absensi, val_problem_solving, score_wfo, val_kualitas, score_project]
                })
                
                fig_radar = px.line_polar(df_radar, r='Nilai', theta='Kategori', line_close=True)
                fig_radar.update_traces(fill='toself', line_color='#4CAF50')
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
                st.plotly_chart(fig_radar, use_container_width=True)

else:
    st.info("👈 Silakan upload file Excel absensi Anda.")