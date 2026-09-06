
import streamlit as st
import pandas as pd
import io
import time

st.set_page_config(page_title="نظام تتبع المناديب", layout="wide", page_icon="🚚")

# Custom CSS for Right-to-Left and styling
st.markdown("""
<style>
    body { direction: RTL; text-align: right; }
    .stApp { direction: RTL; font-family: 'Tajawal', sans-serif; }
    .driver-card { padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 20px; background-color: #f9f9f9; }
    h1, h2, h3, h4, p, span, label { text-align: right !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    /* Hide some Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("📊 نظام تتبع إنتاجية المناديب واستخراج التقارير")
st.markdown("ارفع صور كل مندوب على حدة، ثم قم برفع ملف البنزين لاستخراج التقرير النهائي.")

# Initialize session state for storing data temporarily
if 'drivers_data' not in st.session_state:
    st.session_state.drivers_data = []

if 'driver_counter' not in st.session_state:
    st.session_state.driver_counter = 1

# List of known drivers for dropdown
DRIVER_NAMES = [
    "مد جوني - MD JONY",
    "الصديق الامين - ELSIDDIG ELAMIN ABBAS GADORA",
    "محمد علي - MUHAMMAD ALI JAMIL",
    "حمزة رياض - HAMZA RIAZ RIAZ AHMAD",
    "اقبال أكرم - MUHAMMAD IQBAL",
    "أحمد سليمان - AHMED ABDALHAMED IBRAHIM SULIMAN",
    "ناهد مولا - NAHID MOLLAH",
    "مندوب آخر (كتابة يدوية)"
]

# --- SECTION 1: ADD DRIVER DATA ---
st.header("1️⃣ إدخال صور المندوب")
with st.container():
    st.markdown('<div class="driver-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col2:
        selected_driver = st.selectbox("اختر اسم المندوب", DRIVER_NAMES, key=f"driver_select_{st.session_state.driver_counter}")
        if selected_driver == "مندوب آخر (كتابة يدوية)":
            driver_name_input = st.text_input("أدخل اسم المندوب:")
        else:
            driver_name_input = selected_driver
            
    st.markdown("---")
    
    col_img1, col_img2, col_img3 = st.columns(3)
    
    with col_img1:
        st.write("صورة الطلبات (التطبيق)")
        orders_img = st.file_uploader("رفع الطلبات", type=['jpg', 'jpeg', 'png'], key=f"orders_{st.session_state.driver_counter}", label_visibility="collapsed")
        
    with col_img2:
        st.write("عداد الخروج")
        start_odo_img = st.file_uploader("رفع الخروج", type=['jpg', 'jpeg', 'png'], key=f"start_{st.session_state.driver_counter}", label_visibility="collapsed")
        
    with col_img3:
        st.write("عداد العودة")
        end_odo_img = st.file_uploader("رفع العودة", type=['jpg', 'jpeg', 'png'], key=f"end_{st.session_state.driver_counter}", label_visibility="collapsed")

    if st.button("➕ حفظ بيانات المندوب وإضافة مندوب جديد", type="primary"):
        if driver_name_input:
            # Here we simulate AI reading. In a real app, you'd pass these images to Gemini API
            # For demonstration, we just record that images were uploaded.
            st.session_state.drivers_data.append({
                "اسم المندوب": driver_name_input.split(" - ")[0], # Arabic name
                "الاسم الإنجليزي": driver_name_input.split(" - ")[1] if " - " in driver_name_input else driver_name_input,
                "تم رفع الطلبات": "نعم" if orders_img else "لا",
                "تم رفع الخروج": "نعم" if start_odo_img else "لا",
                "تم رفع العودة": "نعم" if end_odo_img else "لا",
                # Simulated values extracted by AI:
                "الطلبات": 20, # Simulated
                "عداد الخروج": 100000, # Simulated
                "عداد العودة": 100250 # Simulated
            })
            st.session_state.driver_counter += 1
            st.success(f"تم حفظ صور {driver_name_input.split(' - ')[0]} بنجاح! انتقل للمندوب التالي.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("يرجى إدخال/اختيار اسم المندوب")
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- SECTION 2: SHOW SAVED DRIVERS ---
if st.session_state.drivers_data:
    st.header(f"2️⃣ المناديب المسجلين حتى الآن ({len(st.session_state.drivers_data)})")
    
    # Display as a dataframe
    df_temp = pd.DataFrame(st.session_state.drivers_data)
    # Reorder columns for display
    display_cols = ["اسم المندوب", "تم رفع الطلبات", "تم رفع الخروج", "تم رفع العودة"]
    st.dataframe(df_temp[display_cols], use_container_width=True)

    if st.button("🗑️ مسح القائمة والبدء من جديد"):
        st.session_state.drivers_data = []
        st.session_state.driver_counter = 1
        st.rerun()

# --- SECTION 3: FUEL FILE & FINAL REPORT ---
st.markdown("---")
st.header("3️⃣ ملف البنزين وإنشاء التقرير النهائي")

fuel_file = st.file_uploader("ارفع ملف البنزين بصيغة Excel (XLSX)", type=['xlsx'])

if fuel_file and len(st.session_state.drivers_data) > 0:
    if st.button("🚀 إنشاء التقرير النهائي", type="primary"):
        with st.spinner("جاري تحليل الصور ومعالجة ملف البنزين..."):
            time.sleep(2) # Simulate processing time
            
            # --- Excel Generation Logic ---
            # Create a mock excel file for downloading based on session data
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 1. Summary Sheet
                df_summary = pd.DataFrame(st.session_state.drivers_data)
                
                # Format summary dataframe
                df_summary['المسافة (كم)'] = df_summary['عداد العودة'] - df_summary['عداد الخروج']
                # Mock fuel data integration
                df_summary['عدد مرات التعبئة'] = 2
                df_summary['الوقود (لتر)'] = 36.5
                df_summary['التكلفة (ريال)'] = 80.0
                
                final_cols = ["اسم المندوب", "الاسم الإنجليزي", "الطلبات", "عداد الخروج", "عداد العودة", "المسافة (كم)", "عدد مرات التعبئة", "الوقود (لتر)", "التكلفة (ريال)"]
                df_summary[final_cols].to_excel(writer, sheet_name='ملخص اليوم', index=False)
                
                # 2. Fuel details sheet (reading from uploaded file)
                try:
                    df_fuel_input = pd.read_excel(fuel_file)
                    df_fuel_input.to_excel(writer, sheet_name='تفاصيل البنزين', index=False)
                except Exception as e:
                    st.error("حدث خطأ في قراءة ملف البنزين. يرجى التأكد من الصيغة.")
            
            output.seek(0)
            
            st.success("✅ تم الانتهاء من إعداد التقرير بنجاح!")
            
            st.download_button(
                label="📥 تحميل ملف التقرير النهائي (Excel)",
                data=output,
                file_name="تقرير_الإنتاجية_اليومي.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
elif len(st.session_state.drivers_data) == 0 and fuel_file:
    st.warning("يرجى إدخال بيانات مندوب واحد على الأقل قبل استخراج التقرير.")
