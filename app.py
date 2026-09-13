import base64
import io
import time
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import openpyxl
import pandas as pd
import requests
import streamlit as st
from supabase import Client, create_client

# ==========================================
# 1. إعدادات الصفحة الأساسية
# ==========================================
st.set_page_config(page_title="المنصة المركزية لإدارة العمليات", layout="wide", page_icon="🚚")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    body { direction: RTL; text-align: right; background-color: #f8fafc; }
    .stApp { direction: RTL; font-family: 'Tajawal', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white; padding: 1.8rem; border-radius: 14px;
        margin-bottom: 1.5rem; text-align: center;
        box-shadow: 0 8px 20px rgba(30, 60, 114, 0.15);
    }
    .dash-card { padding: 20px; border-radius: 12px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الثوابت والإعدادات (قواعد البيانات والبريد)
# ==========================================
SUPABASE_URL = "https://vnettsvcpqvfgdqimukk.supabase.co"

# --- إعدادات الإيميل المكتملة ---
SENDER_EMAIL = "giadomer0@gmail.com"
RECEIVER_EMAIL = "gharibalhara@gmail.com"
APP_PASSWORD = "Giad';lkjhgfdsaGIAD" 

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/411/411712.png", width=100)
    st.markdown("### ⚙️ إعدادات النظام الأساسية")
    supabase_key_input = st.text_input(
        "مفتاح السحابة (Supabase):", type="password",
        value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZuZXR0c3ZjcHF2ZmdkcWltdWtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5ODU5MzUsImV4cCI6MjEwNDU2MTkzNX0.YzyZee6NZylZpxysi6TlWomf2l_YdVA9njZVOboU9KQ"
    )
    gemini_key_input = st.text_input(
        "مفتاح الذكاء الاصطناعي (Gemini):", type="password",
        value="AQ.Ab8RN6IXdqrpdjHEC77q7_D2KQ9U7drmmCVWiwBqH0jm1doHWw"
    )

supabase: Client = None
if supabase_key_input:
    try:
        supabase = create_client(SUPABASE_URL, supabase_key_input.strip())
    except:
        st.sidebar.error("⚠️ خطأ في الاتصال بقاعدة البيانات")

# ==========================================
# 3. دوال العمليات (الإيميل، الذكاء الاصطناعي)
# ==========================================
def send_delay_email(driver_name, start_time_str, hours_passed):
    try:
        subject = f"🚨 عاجل: تأخير إغلاق وردية المندوب ({driver_name})"
        body = f"""
        مرحباً الإدارة الكريمة،
        
        هذا إشعار آلي من نظام الإدارة اللوجستية:
        المندوب [{driver_name}] تجاوز مدة العمل المسموحة (12.5 ساعة).
        
        - وقت بدء الوردية (الخروج): {start_time_str}
        - الساعات المنقضية حتى الآن: {hours_passed} ساعة.
        
        الرجاء التواصل مع المندوب للتأكد من إغلاق العداد ورفع ملخص الطلبات.
        
        مع تحيات،
        نظام العمليات الآلي.
        """
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

def check_overtime_drivers():
    """التحقق من تجاوز 12.5 ساعة وإرسال الإيميل"""
    if not supabase: return []
    overtime_drivers = []
    try:
        active_logs = supabase.table('daily_logs').select("*").eq('shift_status', 'active').execute().data
        now_utc = pd.Timestamp.now(tz='UTC')
        
        for log in active_logs:
            created_at_utc = pd.to_datetime(log['created_at'])
            if created_at_utc.tzinfo is None:
                created_at_utc = created_at_utc.tz_localize('UTC')
                
            hours_passed = (now_utc - created_at_utc).total_seconds() / 3600.0
            
            if hours_passed >= 12.5:
                hours_rounded = round(hours_passed, 1)
                start_time_str = created_at_utc.tz_convert('Asia/Riyadh').strftime('%Y-%m-%d %I:%M %p')
                
                overtime_drivers.append({'name': log['driver_name'], 'time': start_time_str, 'hours': hours_rounded})
                
                if not log.get('email_sent'):
                    success = send_delay_email(log['driver_name'], start_time_str, hours_rounded)
                    if success:
                        supabase.table('daily_logs').update({'email_sent': True}).eq('id', log['id']).execute()
    except Exception:
        pass
    return overtime_drivers

def extract_number_from_image(image_file, prompt, api_key):
    if not image_file or not api_key: return None
    try:
        base64_image = base64.b64encode(image_file.getvalue()).decode('utf-8')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
        payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": image_file.type, "data": base64_image}}]}]}
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            numbers = re.findall(r'\d+', text.replace(',', ''))
            return int(numbers[0]) if numbers else None
    except: return None

def extract_orders_and_date(image_file, api_key):
    """استخراج الطلبات الموصلة والمرتجعة وجمعهما"""
    if not image_file or not api_key: return None, None
    try:
        base64_image = base64.b64encode(image_file.getvalue()).decode('utf-8')
        prompt = """
        Analyze this delivery summary image and extract:
        1. Find the number of 'Delivered' orders (الطلبات الموصلة).
        2. Find the number of 'Returned' or 'Return Pickups' orders (الطلبات المرتجعة).
        3. Add BOTH numbers together to get the Total Orders.
        4. Find the Date shown in the image.
        Reply EXACTLY in this format and nothing else:
        ORDERS: [Total Orders Number]
        DATE: [YYYY-MM-DD]
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
        payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": image_file.type, "data": base64_image}}]}]}
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            orders = re.search(r'ORDERS:\s*(\d+)', text, re.IGNORECASE)
            date = re.search(r'DATE:\s*([^\n]+)', text, re.IGNORECASE)
            o_count = int(orders.group(1)) if orders else None
            d_str = date.group(1).strip() if date and date.group(1).strip().upper() not in ['NONE', 'NULL', '0'] else None
            return o_count, d_str
    except: pass
    return None, None

# ==========================================
# 4. واجهة المستخدم (التنبيهات العلوية والتبويبات)
# ==========================================
st.markdown('<div class="main-header"><h1 style="color:white; margin:0;">🚚 المنصة المركزية لإدارة العمليات اللوجستية</h1></div>', unsafe_allow_html=True)

# فحص المناديب المتأخرين وعرض تنبيهات حية
delayed_list = check_overtime_drivers()
if delayed_list:
    for item in delayed_list:
        st.error(f"🚨 **تنبيه عاجل:** المندوب **{item['name']}** تجاوز **{item['hours']} ساعة** من العمل (البداية: {item['time']}). (تم إرسال إشعار للإدارة).")

tab_manual, tab_live, tab_fleet, tab_report = st.tabs([
    "✍️ الإدخال اليدوي (للمدير)", "📡 المراقبة اللحظية (للتطبيق)", "👥 إدارة الأسطول", "📊 تقارير الأداء"
])

# --- تبويب الإدخال اليدوي ---
with tab_manual:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.subheader("إدخال بيانات المندوب يدوياً (مؤقت حتى اعتماد التطبيق)")
    
    drivers_list = ["-- اختر المندوب --"]
    if supabase:
        try:
            drivers_data = supabase.table('drivers').select('*').execute().data
            unique_names = set()
            for d in drivers_data:
                # تصفية الأسماء المكررة واعتماد المتوفر (عربي أو إنجليزي)
                name = d.get('name_ar') or d.get('name_en') or d.get('name')
                if name and str(name).strip():
                    unique_names.add(str(name).strip())
            drivers_list += sorted(list(unique_names))
        except: pass
            
    selected_driver = st.selectbox("👤 اسم المندوب:", drivers_list)
    st.markdown("---")
    
    col_img1, col_img2, col_img3 = st.columns(3)
    with col_img1:
        orders_img = st.file_uploader("📦 صورة ملخص الطلبات", type=['jpg', 'jpeg', 'png'])
    with col_img2:
        start_odo_img = st.file_uploader("🟢 صورة عداد الخروج", type=['jpg', 'jpeg', 'png'])
    with col_img3:
        end_odo_img = st.file_uploader("🔴 صورة عداد العودة", type=['jpg', 'jpeg', 'png'])
        
    if st.button("🤖 استخراج الذكاء الاصطناعي وحفظ بالسحابة", type="primary", use_container_width=True):
        if selected_driver == "-- اختر المندوب --":
            st.warning("الرجاء اختيار المندوب أولاً.")
        elif not orders_img and not start_odo_img and not end_odo_img:
            st.warning("الرجاء رفع صورة واحدة على الأقل.")
        else:
            with st.spinner("جاري التحليل واستخراج الأرقام..."):
                orders_count, order_date = extract_orders_and_date(orders_img, gemini_key_input) if orders_img else (None, None)
                start_odo = extract_number_from_image(start_odo_img, "Extract ONLY the ODO number.", gemini_key_input) if start_odo_img else None
                end_odo = extract_number_from_image(end_odo_img, "Extract ONLY the ODO number.", gemini_key_input) if end_odo_img else None
                
                log_data = {
                    'driver_name': selected_driver,
                    'log_date': order_date if order_date else pd.Timestamp.now().strftime('%Y-%m-%d'),
                    'shift_status': 'completed' if end_odo else 'active',
                }
                if start_odo: log_data['start_odo'] = start_odo
                if end_odo: log_data['end_odo'] = end_odo
                if orders_count is not None: log_data['orders_count'] = orders_count
                if order_date: log_data['order_date'] = order_date
                
                supabase.table('daily_logs').insert(log_data).execute()
                
                st.success(f"✅ تم الحفظ! إجمالي الطلبات: {orders_count or '-'} | خروج: {start_odo or '-'} | عودة: {end_odo or '-'}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- تبويب المراقبة اللحظية ---
with tab_live:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.subheader("📡 السجلات اللحظية للعمليات")
    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 تحديث البيانات", use_container_width=True): st.rerun()
    with col_info:
        st.info(f"📧 سيتم إرسال إشعار التأخير إلى: {RECEIVER_EMAIL}")
        
    if supabase:
        try:
            logs = supabase.table('daily_logs').select("*").order('created_at', desc=True).limit(50).execute().data
            if logs:
                df_l = pd.DataFrame(logs)
                df_l['المسافة المقطوعة'] = df_l.apply(
                    lambda r: (r.get('end_odo', 0) - r.get('start_odo', 0)) if pd.notna(r.get('start_odo')) and pd.notna(r.get('end_odo')) else "-", axis=1
                )
                cols_to_show = ['driver_name', 'log_date', 'orders_count', 'shift_status', 'start_odo', 'end_odo', 'المسافة المقطوعة']
                for c in cols_to_show:
                    if c not in df_l.columns: df_l[c] = "-"
                        
                display_df = df_l[cols_to_show].copy()
                display_df.rename(columns={
                    'driver_name': 'المندوب', 'log_date': 'التاريخ', 'orders_count': 'إجمالي الطلبات', 
                    'shift_status': 'حالة الوردية', 'start_odo': 'عداد الانطلاق', 'end_odo': 'عداد العودة'
                }, inplace=True)
                
                def color_status(val):
                    color = '#dcfce3' if val == 'completed' else '#fee2e2'
                    return f'background-color: {color}; font-weight: bold;'
                
                st.dataframe(display_df.style.map(color_status, subset=['حالة الوردية']), use_container_width=True, hide_index=True)
            else:
                st.info("لا توجد سجلات حالياً.")
        except Exception as e:
            st.error("جاري الاتصال بقاعدة البيانات...")
    st.markdown('</div>', unsafe_allow_html=True)

# --- تبويب إدارة الأسطول ---
with tab_fleet:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.subheader("👥 بيانات المناديب")
    if supabase:
        try:
            drivers = supabase.table('drivers').select("*").execute().data
            if drivers:
                df_d = pd.DataFrame(drivers)[['name_ar', 'phone', 'plate_number', 'app_password']]
                df_d.rename(columns={'name_ar': 'الاسم', 'phone': 'رقم الجوال', 'plate_number': 'لوحة السيارة', 'app_password': 'رقم تطبيق الجوال'}, inplace=True)
                st.dataframe(df_d, use_container_width=True, hide_index=True)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)

# --- تبويب التقارير ---
with tab_report:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.subheader("📊 تصدير التقرير النهائي (Excel)")
    if st.button("🚀 تحميل التقرير التشغيلي الموحد", type="primary"):
        if supabase:
            logs = supabase.table('daily_logs').select("*").order('created_at', desc=True).execute().data
            if logs:
                df_export = pd.DataFrame(logs)
                out = io.BytesIO()
                df_export.to_excel(out, index=False)
                out.seek(0)
                st.download_button("📥 اضغط هنا لتحميل الملف", data=out, file_name="التقرير_التشغيلي_للمناديب.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown('</div>', unsafe_allow_html=True)
