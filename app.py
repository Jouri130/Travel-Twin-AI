import streamlit as st
from openai import OpenAI
import json
import os
import re

# --- 1. إعدادات API عِلم ---

API_KEY = "sk-fsC3VMwu1A3PmoIKZuCvBg"
BASE_URL = "https://elmodels.ngrok.app/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# --- 2. وظائف الذكاء الاصطناعي ---

def clean_json_response(content):
    """طريقة احترافية لاستخراج الـ JSON من استجابة المودل"""
    try:
        # البحث عن أي نص بين { } لمعالجة أي نصوص إضافية من المودل
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None


def get_nuha_plan(prefs):
    """وظيفة نهى كـ Agent لتوليد خطة سياحية ذكية باستخدام Prompt مطور"""

    external_data = {
        "current_weather": "24°C - جو معتدل ولطيف",
        "crowd_status": "ازدحام منخفض في الوجهات المقترحة"
    }
    
    system_prompt = f"""
    أنتِ 'نهى 2.0'، التوأم الرقمي الذكي والوكيل السياحي الأكثر دراية بالمملكة العربية السعودية. 
    مهمتك هي تصميم رحلة مخصصة بالكامل (Personalized) تعكس شخصية المستخدم وتفضيلاته.
    
    القواعد الذهبية لنهى 2.0:
    1. اللهجة: تحدثي بلهجة سعودية بيضاء، ودودة، وراقية (مثل: 'يا هلا والله'،'يا هلا ومرحبا').
    2. الذكاء السياقي: إذا كان الجو بارداً، اقترحي أماكن مغلقة دافئة أو أنشطة شتوية. إذا كان التوقيت مسائياً، ركزي على الإضاءات والمطاعم الحيوية.
    3. التفاصيل: لا تذكري أسماء الأماكن فقط، بل اذكري 'لماذا' اخترتِ هذا المكان بناءً على اهتمامات المستخدم.
    4. الدقة المادية: التزمي بالميزانية (اقتصادية = أماكن عامة ومطاعم شعبية، فاخرة = فنادق 5 نجوم وتجارب حصرية).
    5. المخرج: يجب أن يكون المخرج JSON حصراً ولا شيء غيره.
    6. يجب ان تكون اماكن حقيقية وموجودة في المملكة وتحديداً المكان الذي اختاره المستخدم.
    7. الذكاء السياقي: اقترحي أماكن تناسب جو {external_data['current_weather']}.
    8. الهيكلة: يجب أن يتضمن كل نشاط رابط 'google_maps_link' حقيقي.
    """

    user_query = f"""
    صممي لي رحلة بناءً على هذه البيانات:
    - المستخدم: {prefs['user_name']}
    - المدينة: {prefs['region']}
    - الاهتمامات: {', '.join(prefs['interests'])}
    - الرفقة: {prefs['companion']}
    - التوقيت المفضل: {prefs['timing']}
    - حالة الطقس التي يفضلها الآن: {prefs['weather']}
    - مستوى الميزانية: {prefs['budget']}

    المطلوب مخرج JSON بهذا الهيكل:
    {{
      "summary": "ترحيب حار بلهجة نهى وتحليل لسبب اختيار هذه الأماكن بناءً على الطقس والازدحام",
      "schedule": [
        {{"time": "الوقت", "activity": "اسم الفعالية", "location": "الموقع الدقيق", "why": "سبب الاختيار الذكي"}},
        ... (3 أنشطة على الأقل)
      ],
      "estimated_cost": "توقع التكلفة الإجمالية بالريال السعودي"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="nuha-2.0",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
     
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        st.error(f"حدث خطأ في الاتصال: {e}")
        return None

def text_to_speech(text):
    """تحويل النص إلى صوت باستخدام elm-tts"""
    try:
        response = client.audio.speech.create(
            model="elm-tts",
            voice="default",
            input=text
        )
        return response.content
    except:
        return None

# --- 3. تصميم الواجهة ---
st.set_page_config(page_title="Travel With Me", page_icon="🧭", layout="centered")

# دالة لعرض ملف التوأم الرقمي في القائمة الجانبية
def show_digital_twin_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>🤖 توأمي الرقمي</h2>", unsafe_allow_html=True)
        st.markdown("---")
        if 'user_name' in st.session_state:
            st.success(f"المستخدم: {st.session_state.user_name}")
            if 'interests' in st.session_state:
                st.markdown("**السمات المستنتجة:**")
                interests = st.session_state.interests
                if "تاريخ وثقافة" in interests: st.info("🏛️ باحث عن الأصالة")
                if "ترفيه" in interests: st.info("🎢 محب للمغامرة")
                if "مطاعم ومقاهي" in interests: st.info("☕ متذوق وخبير مقاهي")
                
                budget = st.session_state.get('budget', '')
                if "فاخرة" in budget: st.warning("💎 نمط حياة VIP")
            
            st.caption("يتم تحديث التوأم لحظياً بناءً على تفاعلك.")
        else:
            st.info("قم بتسجيل اسمك لبدء بناء توأمك الرقمي.")


# --- 3. تصميم الواجهة (CSS المطور) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* 1. إصلاح ألوان النصوص وإجبارها على الظهور بلون غامق */
    html, body, [class*="st-"], .stMarkdown, p, h1, h2, h3, h4, span, label, div, li {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        color: #2D3436 !important; /* لون رمادي غامق جداً للوضوح التام */
    }
    
    /* 2. لون خلفية التطبيق */
    .stApp { 
        background-color: #F4F1E1 !important; 
    }
    
    /* 3. تنسيق الكروت (Cards) */
    .card {
        background-color: #ffffff !important;
        border: 1px solid #D1C7A7 !important;
        border-radius: 15px !important;
        padding: 25px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        color: #2D3436 !important;
    }

    /* 4. تنسيق العناوين الكبيرة */
    .big-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #3D6B6B !important;
        line-height: 1.1;
        margin-bottom: 15px;
    }

    /* 5. تنسيق الأزرار (Buttons) */
    .stButton>button {
        background-color: #3D6B6B !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
        width: 100%;
        font-size: 1.1rem;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #2A4D4D !important;
        transform: translateY(-2px);
    }

    /* 6. تنسيق القائمة الجانبية (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-left: 1px solid #D1C7A7 !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #2D3436 !important;
    }

    /* 7. إخفاء العناصر الافتراضية لستريمليت لمظهر احترافي */
    header, footer { visibility: hidden; }
    
    /* 8. تنسيق الروابط */
    a {
        color: #D4A373 !important;
        text-decoration: none !important;
        font-weight: bold;
    }
    a:hover {
        text-decoration: underline !important;
    }

</style>
""", unsafe_allow_html=True)

# إدارة الصفحات والتوأم الرقمي
if 'page' not in st.session_state: st.session_state.page = 'welcome'
show_digital_twin_sidebar()

current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "logo.PNG")

# --- شاشة 1: الترحيب ---
if st.session_state.page == 'welcome':
    col_l, col_r = st.columns([1, 4])
    with col_l:
        if os.path.exists(logo_path):
            st.image(logo_path, width=130)
        elif os.path.exists("logo.png"):
            st.image("logo.png", width=130)
        else:
            st.markdown("<h1 style='font-size: 60px; margin:0;'>🧭</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 40px;'>", unsafe_allow_html=True)
    st.markdown("<h1 class='big-title'>رحلتك،<br>مصممة لك وحدك</h1>", unsafe_allow_html=True)
    st.markdown("""
    <p class='sub-title'>
    توأمك الرقمي الذكي يفهمك ويخطط لرحلتك بذكاء، <br>
    ويتكيف لحظيًا مع الازدحام والطقس.
    </p>
    """, unsafe_allow_html=True)
    
    if st.button("ابدأ رحلتك"):
        st.session_state.page = 'name_entry'
        st.rerun()

# --- شاشة 2: تسجيل الاسم ---
elif st.session_state.page == 'name_entry':
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("الأسم الكريم")
    name = st.text_input("", placeholder="اكتب اسمك هنا...", label_visibility="collapsed")
    
    if name:
        st.markdown(f"<p style='color: #3D6B6B; font-weight: bold; font-size:1.2rem;'>عاشت الأسامي يا {name}، يا أهلاً وسهلاً نورت التطبيق ✨</p>", unsafe_allow_html=True)
        if st.button("استمرار"):
            st.session_state.user_name = name
            st.session_state.page = 'prefs'
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- شاشة 3: التفضيلات ---
elif st.session_state.page == 'prefs':
    st.markdown(f"### حيّاك الله يا {st.session_state.user_name} 🧭")
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        region = st.selectbox("📍 اختر وجهتك:", ["الرياض", "جدة", "العلا", "أبها"])
        interests = st.multiselect("⭐ ما هي اهتماماتك؟", ["تاريخ وثقافة", "تسوق", "مطاعم ومقاهي", "طبيعة", "ترفيه"], default=["مطاعم ومقاهي"])
        companion = st.radio("👥 من يرافقك؟", ["بمفردي", "العائلة", "الأصدقاء"], horizontal=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        timing = st.radio("⏰ توقيت الطلعة المفضّل:", ["صباحي", "مسائي", "يوم كامل"], horizontal=True)
        weather = st.radio("☁️ جوّك المفضّل:", ["مشمس وصافي", "غائم ومنعش", "بارد هادئ"], horizontal=True)
        budget = st.radio("💰 الميزانية:", ["اقتصادية", "متوسطة", "فاخرة (VIP)"], horizontal=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("✨ احصل على اقتراح نهى 2.0"):
        if not interests:
            st.warning("لطفاً، اختر اهتماماً واحداً على الأقل.")
        else:
            with st.spinner("نهى تحلل الظروف والطقس لراحتك..."):
                current_prefs = {
                    "user_name": st.session_state.user_name,
                    "region": region,
                    "interests": interests,
                    "companion": companion,
                    "timing": timing,
                    "weather": weather,
                    "budget": budget
                }
                res = get_nuha_plan(current_prefs)
                if res:
                    st.session_state.plan = res
                    st.session_state.page = 'result'
                    st.rerun()

# --- شاشة 4: النتائج ---
elif st.session_state.page == 'result':
    plan = st.session_state.get('plan', {})
    st.markdown(f"### جدولك الذكي المقترح 🗓️")
    
    st.markdown(f"<div class='card' style='border-right: 6px solid #3D6B6B;'>", unsafe_allow_html=True)
    st.write(plan.get('summary', ''))
    if st.button("🎙️ استمع لتوصية توأمك الرقمي"):
        audio = text_to_speech(plan.get('summary', ''))
        if audio: st.audio(audio, format="audio/wav")
    st.markdown("</div>", unsafe_allow_html=True)

    for item in plan.get('schedule', []):
        st.markdown(f"""
        <div class='card'>
            <span style='color:#3D6B6B; font-weight:bold;'>{item.get('time', '')}</span> - {item.get('activity', '')}<br>
            <small style='color:gray;'>📍 {item.get('location', '')}</small><br>
            <p style='font-size:0.9rem; margin-top:8px;'>{item.get('why', '')}</p>
            <a href="{item.get('google_maps_link', '#')}" target="_blank" style="color: #D4A373; text-decoration: none; font-weight: bold;">📍 عرض في الخريطة ←</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='card' style='text-align:center; background:#E8F0F0; border:none;'><b>التكلفة التقديرية: {plan.get('estimated_cost', '')}</b></div>", unsafe_allow_html=True)

    st.markdown("<div class='booking-btn-style'>", unsafe_allow_html=True)
    if st.button("✅ تأكيد واحجز الآن"):
        st.balloons()
        st.success("تم تأكيد حجزك بنجاح! رحلة سعيدة.")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔄 تعديل التفضيلات"):
        st.session_state.page = 'prefs'
        st.rerun()