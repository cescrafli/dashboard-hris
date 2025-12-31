import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
import itertools
import io
from datetime import date, datetime, time, timedelta
import calendar

# --- 1. CONFIG & STYLE---
warnings.filterwarnings('ignore')
st.set_page_config(page_title="HRIS Enterprise Command Center", layout="wide", page_icon="🏢")

st.markdown("""
<style>
    /* Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Settings */
    .stApp { 
        background-color: #f8fafc; 
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Card Design */
    div[data-testid="metric-container"] {
        background: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    
    /* Headers */
    h1, h2, h3 { color: #0f172a; font-weight: 700; letter-spacing: -0.5px; }
    p, label { color: #64748b; }
    
    /* Custom Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px;
        color: #64748b;
        font-weight: 600;
        border: 1px solid #e2e8f0;
        padding: 0 24px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
        border-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* DataFrame */
    .stDataFrame { border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🏢 HRIS Dashboard")
    st.markdown("<p style='font-size: 16px; margin-top: -10px; color: #64748b;'>Enterprise People Analytics & Performance Management System</p>", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div style="text-align: right; padding: 12px; background: white; border-radius: 12px; border: 1px solid #e2e8f0;">
        <span style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Date</span><br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">{datetime.now().strftime('%d %B %Y')}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 2. CONFIG DATA---
libur_nasional = {
    date(2025, 1, 1): "Tahun Baru Masehi", date(2025, 1, 27): "Isra Mikraj",
    date(2025, 1, 28): "Cuti Imlek", date(2025, 1, 29): "Imlek",
    date(2025, 3, 29): "Nyepi", date(2025, 3, 31): "Idul Fitri",
    date(2025, 4, 1): "Idul Fitri", date(2025, 4, 2): "Cuti Lebaran",
    date(2025, 4, 3): "Cuti Lebaran", date(2025, 4, 4): "Cuti Lebaran",
    date(2025, 4, 18): "Jumat Agung", date(2025, 4, 20): "Paskah",
    date(2025, 5, 1): "Hari Buruh", date(2025, 5, 12): "Waisak",
    date(2025, 5, 29): "Kenaikan Isa Almasih", date(2025, 6, 1): "Pancasila",
    date(2025, 6, 6): "Idul Adha", date(2025, 6, 27): "1 Muharram",
    date(2025, 8, 17): "Kemerdekaan RI", date(2025, 9, 5): "Maulid Nabi",
    date(2025, 12, 25): "Natal", date(2025, 12, 26): "Cuti Natal"
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

# --- 3. CORE FUNCTIONS ---
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
            header_idx = i; found = True; break
            
    file.seek(0)
    if not found: header_idx = 0
        
    try:
        df = pd.read_excel(file, header=header_idx)
    except:
        file.seek(0)
        df = pd.read_csv(file, header=header_idx, encoding='utf-8', sep=None, engine='python')
    return df

def make_synced_input(label, key_prefix, default_val=80):
    key_val = f"{key_prefix}_val"
    if key_val not in st.session_state: st.session_state[key_val] = default_val
    def update_sl(): st.session_state[key_val] = st.session_state[f"{key_prefix}_slider"]
    def update_nm(): st.session_state[key_val] = st.session_state[f"{key_prefix}_number"]

    st.markdown(f"<div style='margin-bottom:5px; font-weight:600; font-size:14px; color:#475569'>{label}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: st.slider("S", 0, 100, st.session_state[key_val], key=f"{key_prefix}_slider", on_change=update_sl, label_visibility="collapsed")
    with c2: st.number_input("N", 0, 100, st.session_state[key_val], key=f"{key_prefix}_number", on_change=update_nm, label_visibility="collapsed")
    return st.session_state[key_val]

# --- 4. SIDEBAR & PROCESSING ---
with st.sidebar:
    st.header("📂 Data Import")
    uploaded_files = st.file_uploader("Upload Attendance Files", type=["xlsx", "csv"], accept_multiple_files=True)
    st.caption("Supports .xlsx and .csv")
    st.markdown("---")

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        try:
            df_temp = load_data_smart(file)
            df_temp.columns = [str(c).strip() for c in df_temp.columns]
            all_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Error reading file {file.name}: {e}")

    if all_dfs:
        df_raw = pd.concat(all_dfs, ignore_index=True)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        cols = df_raw.columns.tolist()

        st.sidebar.subheader("🛠️ Column Mapping")
        def find(k): 
            for i,c in enumerate(cols): 
                if any(x in c.upper() for x in k): return i
            return 0

        c_nama = st.sidebar.selectbox("Nama", cols, index=find(['NAMA','NAME']))
        c_masuk = st.sidebar.selectbox("Check In", cols, index=find(['MASUK','IN']))
        c_keluar = st.sidebar.selectbox("Check Out", cols, index=find(['KELUAR','OUT']))
        c_lokasi = st.sidebar.selectbox("Location", cols, index=find(['LOKASI','LOC']))
        c_catatan = st.sidebar.selectbox("Notes", cols, index=find(['CATATAN','KET']))

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Business Rules")
        target_jam = st.sidebar.number_input("Standard Daily Hours", value=8.5, step=0.5)
        jam_masuk_kantor = st.sidebar.time_input("Late Threshold Time", value=time(9, 0))
        estimasi_biaya_lembur = st.sidebar.number_input("Est. Overtime Cost/Hour (IDR)", value=50000, step=5000)
        
        if st.sidebar.button("🚀 Analyze Data", type="primary", use_container_width=True):
            st.session_state['processed'] = True 
            
            with st.spinner("🔄 Crunching Data & Generating Insights..."):
                # --- PROCESSING PIPELINE ---
                df_act = df_raw[[c_nama, c_masuk, c_keluar, c_lokasi, c_catatan]].copy()
                df_act.columns = ['Nama', 'Masuk_Raw', 'Keluar_Raw', 'Lokasi', 'Catatan']
                df_act['Masuk_Obj'] = pd.to_datetime(df_act['Masuk_Raw'], errors='coerce')
                df_act = df_act.dropna(subset=['Masuk_Obj']) 
                
                if df_act.empty: st.stop()

                df_act['Tanggal'] = df_act['Masuk_Obj'].dt.date
                df_act['Jam_Masuk'] = df_act['Masuk_Obj'].dt.time
                df_act['Absen Masuk'] = df_act['Masuk_Obj']
                df_act['Absen Keluar'] = pd.to_datetime(df_act['Keluar_Raw'], errors='coerce')

                # Auto Checkout
                def set_auto_checkout(row):
                    if pd.notnull(row['Absen Masuk']) and pd.isnull(row['Absen Keluar']):
                        return row['Absen Masuk'].replace(hour=20, minute=0, second=0)
                    return row['Absen Keluar']
                df_act['Absen Keluar'] = df_act.apply(set_auto_checkout, axis=1)
                
                # Cleaning Strings
                df_act['Lokasi'] = df_act['Lokasi'].fillna("Unknown").astype(str).str.upper()
                df_act['Catatan'] = df_act['Catatan'].fillna("-").astype(str).str.upper()

                # Late Logic
                def cek_keterlambatan(row):
                    if pd.isnull(row['Jam_Masuk']): return "On Time", 0
                    if row['Jam_Masuk'] > jam_masuk_kantor:
                        dt_masuk = datetime.combine(date.min, row['Jam_Masuk'])
                        dt_target = datetime.combine(date.min, jam_masuk_kantor)
                        diff_min = (dt_masuk - dt_target).total_seconds() / 60
                        if diff_min <= 15: return "Mild Late (<15m)", 1
                        elif diff_min <= 60: return "Moderate Late (15-60m)", 1
                        else: return "Severe Late (>60m)", 1
                    return "On Time", 0
                
                res_late = df_act.apply(cek_keterlambatan, axis=1, result_type='expand')
                df_act['Late_Category'] = res_late[0]
                df_act['Is_Late'] = res_late[1]

                # Merge Master
                unique_names = df_act['Nama'].unique()
                min_date = df_act['Tanggal'].min()
                max_date = df_act['Tanggal'].max()
                grid = list(itertools.product(unique_names, pd.date_range(min_date, max_date).date))
                df_master = pd.DataFrame(grid, columns=['Nama', 'Tanggal'])
                df_act = df_act.drop_duplicates(subset=['Nama', 'Tanggal'], keep='last')
                df_final = pd.merge(df_master, df_act, on=['Nama', 'Tanggal'], how='left')

                # Status Logic
                def get_status(row):
                    tgl = row['Tanggal']
                    cat = str(row['Catatan']).strip().upper() if pd.notnull(row['Catatan']) else ""
                    lok = str(row['Lokasi']).strip().upper() if pd.notnull(row['Lokasi']) else ""
                    ada_absen = pd.notnull(row['Absen Masuk'])
                    is_weekend = tgl.weekday() >= 5 

                    if tgl in libur_nasional:
                        if ada_absen: return "Lembur Libur (WFO)" if any(k in lok for k in kantor_list) else "Lembur Libur (WFH)"
                        return "Libur Nasional"
                    if is_weekend:
                        if ada_absen: return "Lembur Weekend (WFO)" if any(k in lok for k in kantor_list) else "Lembur Weekend (WFH)"
                        return "Libur Akhir Pekan"
                    
                    keywords = ['WFH', 'WFO', 'MASUK', 'WORK', '-', 'NAN', 'HADIR', '']
                    if cat != "" and not any(k in cat for k in keywords): return "Cuti"
                    if ada_absen: return "WFO" if any(k in lok for k in kantor_list) else "WFH"
                    return "Alpha"

                df_final['Status'] = df_final.apply(get_status, axis=1)
                
                # Metrics Calculation
                df_final['Durasi'] = (df_final['Absen Keluar'] - df_final['Absen Masuk']).dt.total_seconds() / 3600
                df_final['Durasi'] = df_final['Durasi'].fillna(0).round(2)
                df_final['Overtime'] = df_final['Durasi'].apply(lambda x: max(0, x - target_jam))
                df_final['Overtime_Cost'] = df_final['Overtime'] * estimasi_biaya_lembur
                
                df_final['Performa'] = df_final['Durasi'].apply(lambda x: "Under" if x > 0 and x < target_jam else ("On Track" if x >= target_jam else "-"))

                # Slicers & Meta
                df_final['Tanggal_DT'] = pd.to_datetime(df_final['Tanggal'])
                df_final['Tahun'] = df_final['Tanggal_DT'].dt.year
                df_final['Bulan'] = df_final['Tanggal_DT'].dt.month_name()
                df_final['Bulan_Angka'] = df_final['Tanggal_DT'].dt.month
                df_final['Hari'] = df_final['Tanggal_DT'].dt.day_name()
                df_final['Minggu_Ke'] = df_final['Tanggal_DT'].dt.isocalendar().week
                
                df_final['Is_Late'] = df_final['Is_Late'].fillna(0)
                df_final['Late_Category'] = df_final['Late_Category'].fillna("-")

                st.session_state['df_full'] = df_final
                st.success("✅ Analytics Engine Completed Successfully!")

    else:
        st.sidebar.info("👋 Welcome! Please upload attendance file to start.")

# --- 6. VISUALIZATION ENGINE ---
if 'df_full' in st.session_state:
    df = st.session_state['df_full']
    
    # FILTER BAR
    with st.sidebar.expander("🌪️ Filter & Slice", expanded=True):
        sel_tahun = st.multiselect("Tahun", sorted(df['Tahun'].unique()), default=sorted(df['Tahun'].unique()))
        df_bln = df[['Bulan', 'Bulan_Angka']].drop_duplicates().sort_values('Bulan_Angka')
        sel_bulan = st.multiselect("Bulan", df_bln['Bulan'].tolist(), default=df_bln['Bulan'].tolist())
        
        if not df.empty:
            w_min, w_max = int(df['Minggu_Ke'].min()), int(df['Minggu_Ke'].max())
            sel_minggu = st.slider("Minggu", w_min, w_max, (w_min, w_max)) if w_min != w_max else (w_min, w_max)
        else: sel_minggu = (0,0)
            
        sel_karyawan = st.multiselect("Karyawan", sorted(df['Nama'].unique()), default=sorted(df['Nama'].unique()))

    # APPLY FILTER
    if not sel_tahun: sel_tahun = df['Tahun'].unique()
    if not sel_bulan: sel_bulan = df['Bulan'].unique()
    if not sel_karyawan: sel_karyawan = df['Nama'].unique()
    
    mask = (df['Tahun'].isin(sel_tahun) & df['Bulan'].isin(sel_bulan) & 
            (df['Minggu_Ke'] >= sel_minggu[0]) & (df['Minggu_Ke'] <= sel_minggu[1]) & 
            df['Nama'].isin(sel_karyawan))
    df_f = df[mask].copy()
    
    # EXPORT RAW
    st.sidebar.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_f.to_excel(writer, index=False, sheet_name='Report')
    st.sidebar.download_button("📥 Download Raw Data", buffer.getvalue(), f"HR_Report_{date.today()}.xlsx", "application/vnd.ms-excel", use_container_width=True)

    # TABS
    tab1, tab2 = st.tabs(["📊 Dashboard Monitoring", "📝 Performance Review"])
    
    # === TAB 1: EXECUTIVE DASHBOARD ===
    with tab1:
        if df_f.empty: st.warning("No data found for the selected criteria.")
        else:
            # --- AI INSIGHTS ---
            top_emp = df_f.groupby('Nama')['Durasi'].sum().idxmax()
            most_late_day = df_f[df_f['Is_Late']==1]['Hari'].mode()[0] if df_f['Is_Late'].sum() > 0 else "None"
            avg_prod = df_f[df_f['Durasi']>0]['Durasi'].mean()
            
            st.info(f"💡 **AI Insights:** Top Performer: **{top_emp}** | Most Late Day: **{most_late_day}** | Avg Productivity: **{avg_prod:.2f} hrs/day**")

            # --- KEY METRICS ---
            total_days_log = len(df_f)
            total_hadir = len(df_f[df_f['Status'].str.contains('WFO|WFH|Lembur', na=False)])
            total_alpha = len(df_f[df_f['Status'] == 'Alpha'])
            total_wfo = len(df_f[df_f['Status'].str.contains('WFO', na=False)])
            total_wfh = len(df_f[df_f['Status'].str.contains('WFH', na=False)])
            total_under = len(df_f[df_f['Performa'] == 'Under'])
            total_late_count = df_f['Is_Late'].sum()
            est_cost = df_f['Overtime_Cost'].sum()
            
            wajib_kerja = max(1, total_days_log - len(df_f[df_f['Status'].isin(['Libur Nasional', 'Libur Akhir Pekan'])]))
            att_rate = (total_hadir / wajib_kerja) * 100
            
            # Row 1 Metrics
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            m1.metric("Headcount", df_f['Nama'].nunique())
            m2.metric("Avg Hours", f"{avg_prod:.1f} H")
            m3.metric("WFO", total_wfo)
            m4.metric("WFH", total_wfh)
            m5.metric("Alpha", total_alpha, delta_color="inverse")
            m6.metric("Underperf.", total_under, delta_color="inverse")
            m7.metric("Late", int(total_late_count), delta_color="inverse")

            st.markdown("---")

            # --- ROW 1: DISTRIBUTION & TREND ---
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("Attendance Composition")
                df_pie = df_f['Status'].value_counts().reset_index()
                df_pie.columns = ['Status', 'Jumlah']
                fig_pie = px.pie(df_pie, values='Jumlah', names='Status', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader("Monthly Productivity Trend")
                df_monthly = df_f[df_f['Durasi']>0].groupby('Bulan_Angka')['Durasi'].mean().reset_index()
                if not df_monthly.empty:
                    df_monthly['Bulan'] = df_monthly['Bulan_Angka'].apply(lambda x: calendar.month_name[x])
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(x=df_monthly['Bulan'], y=df_monthly['Durasi'], mode='lines+markers', name='Avg Hours', line=dict(color='#3b82f6', width=3)))
                    fig_trend.add_trace(go.Scatter(x=df_monthly['Bulan'], y=[target_jam]*len(df_monthly), mode='lines', name='Target', line=dict(color='red', dash='dash')))
                    fig_trend.update_layout(xaxis_title=None, yaxis_title="Hours", margin=dict(t=20, b=20, l=0, r=0), hovermode="x unified")
                    st.plotly_chart(fig_trend, use_container_width=True)

            # --- ROW 2: DETAILED ANALYSIS ---
            c3, c4 = st.columns([2, 1])
            with c3:
                st.subheader("Daily Productivity Monitor")
                df_daily = df_f[df_f['Durasi']>0].groupby('Tanggal')['Durasi'].mean().reset_index()
                fig_area = px.area(df_daily, x='Tanggal', y='Durasi', line_shape='spline')
                fig_area.add_hline(y=target_jam, line_dash="dash", line_color="red")
                fig_area.update_traces(line_color='#10b981', fillcolor='rgba(16, 185, 129, 0.1)')
                fig_area.update_layout(xaxis_title=None, yaxis_title="Hours", margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_area, use_container_width=True)
            
            with c4:
                st.subheader("🚨 Late Severity Breakdown")
                # Filter only late records
                df_late = df_f[df_f['Is_Late'] == 1]['Late_Category'].value_counts().reset_index()
                
                if not df_late.empty:
                    df_late.columns = ['Category', 'Count']
                    # Create Donut Chart
                    fig_pie_late = px.pie(df_late, values='Count', names='Category', color='Category', 
                                     color_discrete_map={
                                            "Mild Late (<15m)": "#fbbf24", 
                                            "Moderate Late (15-60m)": "#f97316", 
                                            "Severe Late (>60m)": "#ef4444"
                                     },
                                     hole=0.6)
                    fig_pie_late.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2), 
                                              margin=dict(t=0, l=0, r=0, b=0))
                    st.plotly_chart(fig_pie_late, use_container_width=True)
                else:
                    st.success("✅ Excellent! No late arrivals detected.")

            # --- ROW 3: TOP Ranking---
            st.markdown("### 🏆 Top 3 Leaderboards")
            r1, r2, r3 = st.columns(3)
            
            with r1:
                st.markdown("**Most Present**")
                df_pres = df_f[df_f['Status'].str.contains('WF|Lembur', na=False)].groupby('Nama').size().reset_index(name='Days')
                df_top3_pres = df_pres.sort_values('Days', ascending=False).head(3)
                fig_r1 = px.bar(df_top3_pres, x='Days', y='Nama', orientation='h', text_auto=True, color_discrete_sequence=['#3b82f6'])
                fig_r1.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig_r1, use_container_width=True)

            with r2:
                st.markdown("**Highest Absenteeism**")
                df_abs = df_f[df_f['Status'].isin(['Alpha', 'Cuti'])].groupby('Nama').size().reset_index(name='Days')
                df_top3_abs = df_abs.sort_values('Days', ascending=False).head(3)
                if not df_top3_abs.empty:
                    fig_r2 = px.bar(df_top3_abs, x='Days', y='Nama', orientation='h', text_auto=True, color_discrete_sequence=['#ef4444'])
                    fig_r2.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), height=200)
                    st.plotly_chart(fig_r2, use_container_width=True)
                else:
                    st.success("Perfect attendance! No Data.")

            with r3:
                st.markdown("**Highest Work Hours**")
                df_hrs = df_f.groupby('Nama')['Durasi'].sum().reset_index()
                df_top3_hrs = df_hrs.sort_values('Durasi', ascending=False).head(3)
                fig_r3 = px.bar(df_top3_hrs, x='Durasi', y='Nama', orientation='h', text_auto='.0f', color_discrete_sequence=['#10b981'])
                fig_r3.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig_r3, use_container_width=True)

            # --- DATA TABLE---
            with st.expander("📄 Detailed Data Employee", expanded=False):
                # 1. Prepare Data
                df_display = df_f.copy()
                
                # 2. Calculate Totals
                total_durasi = df_display['Durasi'].sum()
                total_cost = df_display['Overtime_Cost'].sum()
                
                # 3. Create Total Row
                # Init row with empty strings
                total_row = {col: '' for col in df_display.columns}
                total_row['Nama'] = 'TOTAL SUMMARY'
                total_row['Durasi'] = total_durasi
                total_row['Overtime_Cost'] = total_cost
                
                # 4. Append
                df_total = pd.DataFrame([total_row])
                df_final_table = pd.concat([df_display, df_total], ignore_index=True)
                
                # 5. Styling
                def highlight_total(row):
                    if row['Nama'] == 'TOTAL SUMMARY':
                        return ['background-color: #d1e7dd; font-weight: bold; color: #0f5132'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_final_table.style
                    .apply(highlight_total, axis=1)
                    .format({'Durasi': '{:.2f}', 'Overtime_Cost': 'IDR {:,.0f}'}), 
                    use_container_width=True
                )

    # === TAB 2: PERFORMANCE REVIEW===
    with tab2:
        st.write("")
        col_sel, col_dummy = st.columns([1, 2])
        with col_sel:
            target_emp = st.selectbox("👤 Select Employee for Review:", sorted(df['Nama'].unique()))
        
        if target_emp:
            df_emp = df_f[df_f['Nama'] == target_emp].copy()
            
            if not df_emp.empty:
                # --- CALCULATION ENGINE---
                
                # 1. KPI (Presence) (20%)
                # Hitung kehadiran aktif
                total_hari_hadir = len(df_emp[df_emp['Durasi'] > 0])
                score_kpi_raw = (total_hari_hadir / 20) * 100
                score_kpi = min(100, score_kpi_raw)
                
                # 2. Project (Productivity) (15%)
                # Logic: Loop hari per hari. Weekend/Libur jika 0 jam tidak dihitung (Exempt).
                list_skor_project = []
                for idx, row in df_emp.iterrows():
                    durasi = row['Durasi']
                    status = row['Status']
                    is_holiday_weekend = any(x in status for x in ["Libur", "Akhir Pekan"])
                    
                    
                    if is_holiday_weekend and durasi == 0:
                        continue 
                    
                    # Hitung skor harian
                    if durasi >= target_jam:
                        skor_harian = 100
                    else:
                        skor_harian = (durasi / target_jam) * 100
                    
                    list_skor_project.append(skor_harian)
                
                if len(list_skor_project) > 0:
                    score_project = sum(list_skor_project) / len(list_skor_project)
                else:
                    score_project = 0
                
                # 3. Absensi / Compliance (10%)
                # (Wajib Kerja - Alpha) / Wajib Kerja
                total_d = len(df_emp)
                libur_count = len(df_emp[df_emp['Status'].isin(['Libur Nasional', 'Libur Akhir Pekan'])])
                wajib = max(1, total_d - libur_count)
                alpha_count = len(df_emp[df_emp['Status'] == 'Alpha'])
                score_att = max(0, ((wajib - alpha_count)/wajib)*100)
                
                # 4. WFO Presence (20%)
                # Target: Jumlah Minggu * 4
                minggu_count = df_emp['Minggu_Ke'].nunique()
                target_wfo_total = max(1, minggu_count * 4)
                actual_wfo = len(df_emp[df_emp['Status'].str.contains('WFO', na=False)])
                score_wfo = min(100, (actual_wfo/target_wfo_total)*100)
                
                # UI Layout
                c_left, c_right = st.columns([1, 1], gap="large")
                
                with c_left:
                    st.markdown("#### 🤖 System Metrics (65%)")
                    cols_sys = st.columns(2)
                    cols_sys[0].success(f"**KPI Presence (20%)**\n# {score_kpi:.1f}")
                    cols_sys[1].info(f"**Project (15%)**\n# {score_project:.1f}")
                    cols_sys[0].warning(f"**Compliance (10%)**\n# {score_att:.1f}")
                    cols_sys[1].info(f"**WFO (20%)**\n# {score_wfo:.1f}")
                    
                    st.markdown("---")
                    st.markdown("#### 👨‍⚖️ Manager Review (35%)")
                    v_kom = make_synced_input("1. Communication (10%)", "v_kom", 80)
                    v_prob = make_synced_input("2. Problem Solving (10%)", "v_prob", 75)
                    v_qual = make_synced_input("3. Quality of Work (15%)", "v_qual", 80)

                with c_right:
                    # Final Formula
                    final_score = (
                        (v_kom * 0.10) +        # Manual 1
                        (score_kpi * 0.20) +    # System 2
                        (score_att * 0.10) +    # System 3
                        (v_prob * 0.10) +       # Manual 4
                        (score_wfo * 0.20) +    # System 5
                        (v_qual * 0.15) +       # Manual 6
                        (score_project * 0.15)  # System 7
                    )
                    
                    if final_score >= 90: grade, color, bg = "A (Outstanding)", "#10b981", "#d1fae5"
                    elif final_score >= 80: grade, color, bg = "B (Exceeds)", "#3b82f6", "#dbeafe"
                    elif final_score >= 70: grade, color, bg = "C (Meets)", "#f59e0b", "#fef3c7"
                    elif final_score >= 50: grade, color, bg = "D (Improvement)", "#f97316", "#ffedd5"
                    else: grade, color, bg = "E (Unsatisfactory)", "#ef4444", "#fee2e2"

                    st.markdown(f"""
                    <div style="background-color: {bg}; border: 2px solid {color}; padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 20px;">
                        <h4 style="color: {color}; margin:0; letter-spacing: 2px;">FINAL SCORE</h4>
                        <h1 style="color: {color}; font-size: 4.5em; margin: 0; font-weight: 800;">{final_score:.1f}</h1>
                        <h3 style="color: {color}; margin:0;">{grade}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Radar Chart Updated Categories
                    df_r = pd.DataFrame({
                        'Metric': ['Komunikasi (10%)', 'KPI (20%)', 'Absensi (10%)', 'Prob. Solving (10%)', 'WFO (20%)', 'Kualitas (15%)', 'Project (15%)'],
                        'Value': [v_kom, score_kpi, score_att, v_prob, score_wfo, v_qual, score_project]
                    })
                    fig_r = px.line_polar(df_r, r='Value', theta='Metric', line_close=True)
                    fig_r.update_traces(fill='toself', line_color=color)
                    fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=20, b=20))
                    st.plotly_chart(fig_r, use_container_width=True)
                    
                    # DOWNLOAD REPORT
                    report_text = f"""
                    PERFORMANCE APPRAISAL REPORT
                    ----------------------------
                    Employee: {target_emp}
                    Date: {date.today()}
                    
                    SYSTEM METRICS (65%):
                    - KPI (Presence): {score_kpi:.2f}
                    - Project Score: {score_project:.2f}
                    - Compliance: {score_att:.2f}
                    - WFO Score: {score_wfo:.2f}
                    
                    MANAGER REVIEW (35%):
                    - Communication: {v_kom}
                    - Problem Solving: {v_prob}
                    - Quality Of Work: {v_qual}
                    
                    FINAL RESULT:
                    - Total Score: {final_score:.2f}
                    - Grade: {grade}
                    """
                    st.download_button("💾 Download Report (TXT)", report_text, f"Appraisal_{target_emp}.txt", use_container_width=True)

else:

    st.info("👋 Please upload your attendance file in the sidebar to start.")
