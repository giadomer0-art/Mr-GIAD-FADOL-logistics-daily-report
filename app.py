import streamlit as st
import pandas as pd
import io
import time
import re
import google.generativeai as genai
from PIL import Image
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="نظام تتبع المناديب", layout="wide", page_icon="🚚")

# Custom CSS
st.markdown("""
<style>
    body { direction: RTL; text-align: right; }
    .stApp { direction: RTL; font-family: 'Tajawal', sans-serif; }
    .driver-card { padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 20px; background-color: #f9f9f9; }
    h1, h2, h3, h4, p, span, label { text-align: right !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ----------------- AI Vision Function -----------------
def extract_number_from_image(image_file, prompt, api_key):
    if not image_file or not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')# أسرع وأدق للأرقام
        img = Image.open(image_file)
        response = model.generate_content([prompt, img])
        text = response.text.strip().replace(',', '')
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return None
    except Exception as e:
        st.error(f"خطأ في قراءة الصورة: {e}")
        return None

# ----------------- UI Sidebar (API Key) -----------------
with st.sidebar:
    st.header("⚙️ إعدادات النظام")
    api_key_input = st.text_input("أدخل مفتاح Gemini API السري:", type="password", help="مطلوب لتفعيل الذكاء الاصطناعي لقراءة الصور")
    st.markdown("---")
    st.markdown("**كيف تحصل على المفتاح مجاناً؟**\n1. اذهب لموقع [Google AI Studio](https://aistudio.google.com/app/apikey)\n2. اضغط Create API Key\n3. انسخه والصقه هنا.")

st.title("📊 نظام الذكاء الاصطناعي لاستخراج تقارير المناديب")

# Initialize Session State
if 'drivers_data' not in st.session_state:
    st.session_state.drivers_data = []
if 'driver_counter' not in st.session_state:
    st.session_state.driver_counter = 1

DRIVER_NAMES = [
    "حمزة رياض - HAMZA RIAZ RIAZ AHMAD",
    "الصديق الامين - ELSIDDIG ELAMIN ABBAS GADORA",
    "محمد علي - MUHAMMAD ALI JAMIL",
    "اقبال أكرم - MUHAMMAD IQBAL",
    "أحمد سليمان - AHMED ABDALHAMED IBRAHIM SULIMAN",
    "مد جوني - MD JONY",
    "ناهد مولا - NAHID MOLLAH",
    "مندوب آخر (كتابة يدوية)"
]

# ----------------- SECTION 1: ADD DRIVER -----------------
st.header("1️⃣ إدخال صور المندوب")
with st.container():
    st.markdown('<div class="driver-card">', unsafe_allow_html=True)
    
    selected_driver = st.selectbox("اختر اسم المندوب", DRIVER_NAMES, key=f"d_select_{st.session_state.driver_counter}")
    driver_name_input = st.text_input("أدخل اسم المندوب:") if selected_driver == "مندوب آخر (كتابة يدوية)" else selected_driver
            
    st.markdown("---")
    col_img1, col_img2, col_img3 = st.columns(3)
    
    with col_img1:
        st.write("🚚 صورة الطلبات")
        orders_img = st.file_uploader("رفع الطلبات", type=['jpg', 'jpeg', 'png', 'webp'], key=f"ord_{st.session_state.driver_counter}", label_visibility="collapsed")
        
    with col_img2:
        st.write("🟢 عداد الخروج")
        start_odo_img = st.file_uploader("رفع الخروج", type=['jpg', 'jpeg', 'png', 'webp'], key=f"st_{st.session_state.driver_counter}", label_visibility="collapsed")
        
    with col_img3:
        st.write("🔴 عداد العودة")
        end_odo_img = st.file_uploader("رفع العودة", type=['jpg', 'jpeg', 'png', 'webp'], key=f"en_{st.session_state.driver_counter}", label_visibility="collapsed")

    if st.button("🤖 قراءة الصور وحفظ بيانات المندوب", type="primary"):
        if not api_key_input:
            st.error("⚠️ يرجى إدخال مفتاح API في القائمة الجانبية لتفعيل الذكاء الاصطناعي.")
        elif driver_name_input:
            with st.spinner('جاري تحليل الصور بالذكاء الاصطناعي...'):
                orders_count = extract_number_from_image(orders_img, "Extract ONLY the number of 'Delivered Orders' or 'الطلبات الموصلة'. Return only digits.", api_key_input) if orders_img else None
                start_odo = extract_number_from_image(start_odo_img, "Extract the ODO (odometer) distance reading. Return ONLY the number without km.", api_key_input) if start_odo_img else None
                end_odo = extract_number_from_image(end_odo_img, "Extract the ODO (odometer) distance reading. Return ONLY the number without km.", api_key_input) if end_odo_img else None

                arb_name = driver_name_input.split(" - ")[0]
                eng_name = driver_name_input.split(" - ")[1] if " - " in driver_name_input else driver_name_input

                st.session_state.drivers_data.append({
                    "اسم المندوب": arb_name,
                    "الاسم الإنجليزي": eng_name,
                    "الطلبات": orders_count,
                    "عداد الخروج": start_odo,
                    "عداد العودة": end_odo
                })
                st.session_state.driver_counter += 1
                st.success(f"✅ تم بنجاح استخراج: {orders_count or '-'} طلب | خروج: {start_odo or '-'} | عودة: {end_odo or '-'}")
                time.sleep(2)
                st.rerun()
        else:
            st.error("يرجى إدخال/اختيار اسم المندوب")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- SECTION 2: SAVED DRIVERS -----------------
if st.session_state.drivers_data:
    st.header(f"2️⃣ المناديب المسجلين حتى الآن ({len(st.session_state.drivers_data)})")
    df_temp = pd.DataFrame(st.session_state.drivers_data)
    st.dataframe(df_temp[["اسم المندوب", "الطلبات", "عداد الخروج", "عداد العودة"]], use_container_width=True)
    if st.button("🗑️ مسح وإعادة تعيين"):
        st.session_state.drivers_data = []
        st.rerun()

# ----------------- SECTION 3: FUEL & EXCEL GENERATION -----------------
st.markdown("---")
st.header("3️⃣ ملف البنزين وإنشاء التقرير الاحترافي")
fuel_file = st.file_uploader("ارفع ملف البنزين بصيغة Excel (XLSX)", type=['xlsx'])

if fuel_file and len(st.session_state.drivers_data) > 0:
    if st.button("🚀 إنشاء وتنسيق التقرير النهائي", type="primary"):
        with st.spinner("جاري دمج البيانات وتنسيق ملف الإكسل..."):
            try:
                # 1. Process Fuel Data
                df_fuel = pd.read_excel(fuel_file)
                fuel_summary = df_fuel.groupby('اسم السائق').agg(
                    fuel_count=('رقم المعاملة', 'count'), fuel_cost=('القيمة', 'sum'), fuel_liters=('عدد اللترات', 'sum')
                ).reset_index()
                
                fuel_dict = {row['اسم السائق']: {'count': row['fuel_count'], 'cost': row['fuel_cost'], 'liters': row['fuel_liters']} for _, row in fuel_summary.iterrows()}

                # 2. Build Exact OpenPyXL File
                wb = openpyxl.Workbook()
                ws_summary = wb.active
                ws_summary.title = "ملخص اليوم"
                ws_summary.views.sheetView[0].rightToLeft = True
                
                ws_fuel = wb.create_sheet(title="تفاصيل البنزين")
                ws_fuel.views.sheetView[0].rightToLeft = True

                # Styles
                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                data_font = Font(name="Calibri", size=11)
                bold_font = Font(name="Calibri", size=11, bold=True)
                tot_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'), top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))
                dbl_bot_border = Border(top=Side(style='thin', color='000000'), bottom=Side(style='double', color='000000'))

                # Summary Headers
                sum_headers = ["م", "اسم الموظف", "اسم الموظف بالانجليزي", "الطلبات", "عداد الخروج", "عداد العودة", "المسافة (كم)", "مرات التعبئة", "الوقود (لتر)", "التكلفة (ريال)"]
                ws_summary.append(sum_headers)

                # Summary Data
                for r_idx, drv in enumerate(st.session_state.drivers_data, start=2):
                    eng = drv['الاسم الإنجليزي']
                    f_d = fuel_dict.get(eng, {'count': 0, 'liters': 0.0, 'cost': 0.0})
                    dist_f = f'=IF(AND(ISNUMBER(E{r_idx}), ISNUMBER(F{r_idx})), F{r_idx}-E{r_idx}, "-")'
                    
                    row_data = [
                        r_idx-1, drv['اسم المندوب'], eng, drv['الطلبات'] or "-", drv['عداد الخروج'] or "-", drv['عداد العودة'] or "-",
                        dist_f, f_d['count'], f_d['liters'], f_d['cost']
                    ]
                    for c_idx, val in enumerate(row_data, 1):
                        ws_summary.cell(row=r_idx, column=c_idx, value=val)

                # Summary Totals
                tot_r = len(st.session_state.drivers_data) + 2
                ws_summary.cell(row=tot_r, column=1, value="")
                ws_summary.cell(row=tot_r, column=2, value="الإجمالي")
                ws_summary.cell(row=tot_r, column=4, value=f"=SUM(D2:D{tot_r-1})")
                ws_summary.cell(row=tot_r, column=5, value="-")
                ws_summary.cell(row=tot_r, column=6, value="-")
                ws_summary.cell(row=tot_r, column=7, value=f'=SUMIF(G2:G{tot_r-1}, "<>-")')
                ws_summary.cell(row=tot_r, column=8, value=f"=SUM(H2:H{tot_r-1})")
                ws_summary.cell(row=tot_r, column=9, value=f"=SUM(I2:I{tot_r-1})")
                ws_summary.cell(row=tot_r, column=10, value=f"=SUM(J2:J{tot_r-1})")

                # Apply Styles to Summary
                for c in range(1, 11):
                    ws_summary.cell(row=1, column=c).fill = header_fill
                    ws_summary.cell(row=1, column=c).font = header_font
                    ws_summary.cell(row=1, column=c).alignment = Alignment(horizontal="center", vertical="center")
                    
                    ws_summary.cell(row=tot_r, column=c).fill = tot_fill
                    ws_summary.cell(row=tot_r, column=c).font = bold_font
                    ws_summary.cell(row=tot_r, column=c).border = dbl_bot_border
                    ws_summary.cell(row=tot_r, column=c).alignment = Alignment(horizontal="center", vertical="center")

                for r in range(2, tot_r):
                    for c in range(1, 11):
                        cell = ws_summary.cell(row=r, column=c)
                        cell.font = data_font
                        cell.border = thin_border
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                        if c in [4, 5, 6] and isinstance(cell.value, (int, float)): cell.number_format = '#,##0'
                        elif c == 9 and isinstance(cell.value, (int, float)): cell.number_format = '#,##0.000'
                        elif c == 10 and isinstance(cell.value, (int, float)): cell.number_format = '#,##0.00'

                for col in ws_summary.columns:
                    ws_summary.column_dimensions[get_column_letter(col[0].column)].width = 16

                # Fuel Sheet Data & Style (copy from df_fuel)
                fuel_headers = list(df_fuel.columns)
                ws_fuel.append(fuel_headers)
                for r in dataframe_to_rows(df_fuel, index=False, header=False): ws_fuel.append(r)
                
                # Save to BytesIO
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                
                st.success("✅ تم إعداد التقرير بجميع التنسيقات الحقيقية!")
                st.download_button("📥 تحميل التقرير (Excel)", data=output, file_name="التقرير_اليومي_الاحترافي.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
