"""
StressCare AI - Streamlit App
---------------------------------------
A no-database app covering:
- Consent, anonymous mode and data controls
- Multilingual UI (15 languages)
- Free text, emoji/emotion check-in, questionnaires, voice-to-text
- Safety/fear/wellbeing assessment
- NLP preprocessing + stress/risk assessment
- Optional OpenAI chatbot + offline fallback
- TTS for chatbot responses
- Personalized activities, YouTube searches and game categories
- Task scheduling/reminder mode
- Paint-like drawing canvas
- Camera photo + photo upload + video upload
- Video-call prototype / optional staff meeting URL
- Emergency support and trusted-contact link
- Human-in-the-loop queue
- Dashboard, trends, analytics and downloadable reports

IMPORTANT:
This is a wellness-support application, not a medical diagnostic device. Emergency numbers/resources should be verified for the deployment country.
"""

import os
import re
import json
import hashlib
import unicodedata
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Page config MUST be before any Streamlit UI command.
st.set_page_config(
    page_title="StressCare AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Optional dependencies: the app still starts if some are unavailable.
try:
    import plotly.express as px
except Exception:
    px = None

try:
    from langdetect import detect
except Exception:
    detect = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    from streamlit_drawable_canvas import st_canvas
except Exception:
    st_canvas = None

try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
except Exception:
    webrtc_streamer = None
    WebRtcMode = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# ---------------------------------------------------------------------------
# 1. LANGUAGE / UI
# ---------------------------------------------------------------------------

LANGUAGES = {
    "English": {"code": "en", "stt": "en-IN", "tts": "en"},
    "Tamil": {"code": "ta", "stt": "ta-IN", "tts": "ta"},
    "Hindi": {"code": "hi", "stt": "hi-IN", "tts": "hi"},
    "Telugu": {"code": "te", "stt": "te-IN", "tts": "te"},
    "Malayalam": {"code": "ml", "stt": "ml-IN", "tts": "ml"},
    "Kannada": {"code": "kn", "stt": "kn-IN", "tts": "kn"},
    "Bengali": {"code": "bn", "stt": "bn-IN", "tts": "bn"},
    "Marathi": {"code": "mr", "stt": "mr-IN", "tts": "mr"},
    "Gujarati": {"code": "gu", "stt": "gu-IN", "tts": "gu"},
    "Punjabi": {"code": "pa", "stt": "pa-IN", "tts": "pa"},
    "Urdu": {"code": "ur", "stt": "ur-IN", "tts": "ur"},
    "Spanish": {"code": "es", "stt": "es-ES", "tts": "es"},
    "French": {"code": "fr", "stt": "fr-FR", "tts": "fr"},
    "German": {"code": "de", "stt": "de-DE", "tts": "de"},
    "Japanese": {"code": "ja", "stt": "ja-JP", "tts": "ja"},
}

UI = {
    "English": {
        "title": "StressCare AI",
        "subtitle": "Multilingual stress screening, support and wellbeing dashboard",
        "consent": "I consent to use this session for wellbeing screening and support.",
        "anonymous": "Anonymous mode",
        "language": "Language",
        "pause": "Pause session",
        "resume": "Continue session",
        "emergency": "Immediate emergency support",
        "analyze": "Analyze my wellbeing",
        "free_text": "How are you feeling? Describe what is happening.",
        "risk": "Risk level",
        "stress": "Stress score",
        "confidence": "Confidence",
        "chat": "AI Support Chat",
        "activities": "Personalized Activities",
        "schedule": "Tasks & Reminders",
        "media": "Photo / Video",
        "draw": "Paint-like Drawing",
        "human": "Human Support",
        "dashboard": "Dashboard",
        "reports": "Reports & Privacy",
    },
    "Tamil": {
        "title": "StressCare AI",
        "subtitle": "பல மொழி மனஅழுத்த மதிப்பீடு, ஆதரவு மற்றும் நலன் டாஷ்போர்டு",
        "consent": "நலன் மதிப்பீடு மற்றும் ஆதரவிற்காக இந்த session-ஐ பயன்படுத்த சம்மதிக்கிறேன்.",
        "anonymous": "அநாமதேய முறை",
        "language": "மொழி",
        "pause": "Session-ஐ நிறுத்து",
        "resume": "தொடரவும்",
        "emergency": "உடனடி அவசர உதவி",
        "analyze": "என் நலனை மதிப்பிடு",
        "free_text": "நீங்கள் எப்படி உணர்கிறீர்கள்? என்ன நடக்கிறது என்று எழுதுங்கள்.",
        "risk": "ஆபத்து நிலை",
        "stress": "மனஅழுத்த மதிப்பெண்",
        "confidence": "நம்பிக்கை",
        "chat": "AI ஆதரவு Chat",
        "activities": "தனிப்பயன் செயல்பாடுகள்",
        "schedule": "பணிகள் & நினைவூட்டல்கள்",
        "media": "புகைப்படம் / வீடியோ",
        "draw": "Paint போன்ற Drawing",
        "human": "மனித ஆதரவு",
        "dashboard": "டாஷ்போர்டு",
        "reports": "Reports & Privacy",
    },
    "Hindi": {
        "title": "StressCare AI",
        "subtitle": "बहुभाषी तनाव स्क्रीनिंग, सहायता और वेलनेस डैशबोर्ड",
        "consent": "मैं वेलनेस स्क्रीनिंग और सहायता के लिए इस session के उपयोग की सहमति देता/देती हूँ।",
        "anonymous": "गुमनाम मोड",
        "language": "भाषा",
        "pause": "Session रोकें",
        "resume": "जारी रखें",
        "emergency": "तुरंत आपातकालीन सहायता",
        "analyze": "मेरी स्थिति का विश्लेषण करें",
        "free_text": "आप कैसा महसूस कर रहे हैं? क्या हो रहा है लिखें।",
        "risk": "जोखिम स्तर",
        "stress": "तनाव स्कोर",
        "confidence": "विश्वास",
        "chat": "AI सहायता Chat",
        "activities": "व्यक्तिगत गतिविधियाँ",
        "schedule": "कार्य और रिमाइंडर",
        "media": "फोटो / वीडियो",
        "draw": "Paint जैसा Drawing",
        "human": "मानव सहायता",
        "dashboard": "डैशबोर्ड",
        "reports": "रिपोर्ट और Privacy",
    },
}

# Screening/question translations for all 15 supported languages.
SCREENING_TEXT = {
"English": {
 "emotion":"Emotion selection","emoji":"Chatbot emoji check-in","stress":"Stress level (0 = none, 10 = extreme)","questionnaire":"Emotional questionnaire",
 "q1":"I feel tense or under pressure","q2":"I find it difficult to relax","q3":"My thoughts feel difficult to control","q4":"Work/study or daily tasks feel difficult","q5":"I feel physically/emotionally exhausted",
 "safety_title":"Fear, safety & wellbeing","safety":"How safe do you feel right now?","safe":"I feel safe","unsure":"I am unsure","unsafe":"I don't feel safe","fear":"What are you most worried or afraid about? (optional)","wellbeing":"Overall wellbeing today (0 = very low, 10 = very good)","favorite_title":"Favorite activity for high-stress support","favorite":"Choose what you actually enjoy","voice":"Transcribed voice"
},
"Tamil": {
 "emotion":"உணர்வைத் தேர்வு செய்யவும்","emoji":"Chatbot emoji check-in","stress":"மனஅழுத்த நிலை (0 = இல்லை, 10 = மிகவும் அதிகம்)","questionnaire":"உணர்ச்சி கேள்வித்தாள்",
 "q1":"நான் பதற்றமாக அல்லது அழுத்தத்தில் இருப்பதாக உணர்கிறேன்","q2":"என்னால் ஓய்வெடுக்க கடினமாக உள்ளது","q3":"என் எண்ணங்களைக் கட்டுப்படுத்த கடினமாக உள்ளது","q4":"வேலை/படிப்பு அல்லது தினசரி பணிகள் கடினமாகத் தோன்றுகின்றன","q5":"உடல்/மன ரீதியாக மிகவும் சோர்வாக உணர்கிறேன்",
 "safety_title":"பயம், பாதுகாப்பு & நலன்","safety":"இப்போது நீங்கள் எவ்வளவு பாதுகாப்பாக உணர்கிறீர்கள்?","safe":"நான் பாதுகாப்பாக உணர்கிறேன்","unsure":"எனக்கு உறுதியாக தெரியவில்லை","unsafe":"நான் பாதுகாப்பாக உணரவில்லை","fear":"நீங்கள் எதைப் பற்றி அதிகம் கவலைப்படுகிறீர்கள் அல்லது பயப்படுகிறீர்கள்? (விருப்பம்)","wellbeing":"இன்றைய ஒட்டுமொத்த நலன் (0 = மிகவும் குறைவு, 10 = மிகவும் நன்று)","favorite_title":"அதிக மனஅழுத்தத்திற்கான பிடித்த செயல்பாடு","favorite":"உங்களுக்கு உண்மையில் பிடித்ததைத் தேர்வு செய்யவும்","voice":"குரலில் இருந்து மாற்றிய உரை"
},
"Hindi": {
 "emotion":"भावना चुनें","emoji":"Chatbot emoji check-in","stress":"तनाव स्तर (0 = नहीं, 10 = बहुत अधिक)","questionnaire":"भावनात्मक प्रश्नावली",
 "q1":"मुझे तनाव या दबाव महसूस होता है","q2":"मुझे आराम करना मुश्किल लगता है","q3":"मेरे विचारों को नियंत्रित करना मुश्किल लगता है","q4":"काम/पढ़ाई या दैनिक कार्य कठिन लगते हैं","q5":"मैं शारीरिक/भावनात्मक रूप से बहुत थका हुआ महसूस करता/करती हूँ",
 "safety_title":"डर, सुरक्षा और वेलनेस","safety":"अभी आप खुद को कितना सुरक्षित महसूस करते हैं?","safe":"मैं सुरक्षित महसूस करता/करती हूँ","unsure":"मुझे निश्चित नहीं है","unsafe":"मैं सुरक्षित महसूस नहीं करता/करती हूँ","fear":"आपको सबसे ज्यादा किस बात की चिंता या डर है? (वैकल्पिक)","wellbeing":"आज का समग्र वेलनेस (0 = बहुत कम, 10 = बहुत अच्छा)","favorite_title":"अधिक तनाव के लिए पसंदीदा गतिविधि","favorite":"जो आपको सच में पसंद है उसे चुनें","voice":"आवाज़ से बदला गया पाठ"
},
"Telugu": {
 "emotion":"భావాన్ని ఎంచుకోండి","emoji":"Chatbot emoji check-in","stress":"ఒత్తిడి స్థాయి (0 = లేదు, 10 = చాలా ఎక్కువ)","questionnaire":"భావోద్వేగ ప్రశ్నావళి","q1":"నేను ఒత్తిడిగా లేదా ప్రెషర్‌లో ఉన్నట్లు అనిపిస్తుంది","q2":"నాకు విశ్రాంతి తీసుకోవడం కష్టంగా ఉంది","q3":"నా ఆలోచనలను నియంత్రించడం కష్టంగా ఉంది","q4":"పని/చదువు లేదా రోజువారీ పనులు కష్టంగా అనిపిస్తున్నాయి","q5":"శారీరకంగా/భావోద్వేగంగా చాలా అలసిపోయినట్లు అనిపిస్తుంది","safety_title":"భయం, భద్రత & వెల్‌నెస్","safety":"ప్రస్తుతం మీరు ఎంత సురక్షితంగా అనిపిస్తోంది?","safe":"నేను సురక్షితంగా ఉన్నాను","unsure":"నాకు ఖచ్చితంగా తెలియదు","unsafe":"నేను సురక్షితంగా లేను","fear":"మీకు ఎక్కువగా ఏ విషయం గురించి ఆందోళన లేదా భయం ఉంది? (ఐచ్ఛికం)","wellbeing":"ఈరోజు మొత్తం వెల్‌నెస్ (0 = చాలా తక్కువ, 10 = చాలా మంచిది)","favorite_title":"అధిక ఒత్తిడికి ఇష్టమైన కార్యకలాపం","favorite":"మీకు నిజంగా నచ్చినదాన్ని ఎంచుకోండి","voice":"వాయిస్ నుండి మార్చిన టెక్స్ట్"
},
"Malayalam": {
 "emotion":"വികാരം തിരഞ്ഞെടുക്കുക","emoji":"Chatbot emoji check-in","stress":"സമ്മർദ്ദ നില (0 = ഇല്ല, 10 = വളരെ കൂടുതൽ)","questionnaire":"വൈകാരിക ചോദ്യാവലി","q1":"എനിക്ക് സമ്മർദ്ദമോ സമ്മർദ്ദാവസ്ഥയോ അനുഭവപ്പെടുന്നു","q2":"എനിക്ക് വിശ്രമിക്കാൻ ബുദ്ധിമുട്ടാണ്","q3":"എന്റെ ചിന്തകൾ നിയന്ത്രിക്കാൻ ബുദ്ധിമുട്ടാണ്","q4":"ജോലി/പഠനം അല്ലെങ്കിൽ ദൈനംദിന കാര്യങ്ങൾ ബുദ്ധിമുട്ടായി തോന്നുന്നു","q5":"ശാരീരികമായും/വൈകാരികമായും വളരെ ക്ഷീണിതനായി തോന്നുന്നു","safety_title":"ഭയം, സുരക്ഷ & വെൽനെസ്","safety":"ഇപ്പോൾ നിങ്ങൾക്ക് എത്രത്തോളം സുരക്ഷിതമായി തോന്നുന്നു?","safe":"എനിക്ക് സുരക്ഷിതമായി തോന്നുന്നു","unsure":"എനിക്ക് ഉറപ്പില്ല","unsafe":"എനിക്ക് സുരക്ഷിതമായി തോന്നുന്നില്ല","fear":"നിങ്ങൾക്ക് ഏറ്റവും കൂടുതൽ എന്തിനെക്കുറിച്ചാണ് ആശങ്കയോ ഭയമോ? (ഓപ്ഷണൽ)","wellbeing":"ഇന്നത്തെ മൊത്തത്തിലുള്ള വെൽനെസ് (0 = വളരെ കുറവ്, 10 = വളരെ നല്ലത്)","favorite_title":"കൂടുതൽ സമ്മർദ്ദത്തിനുള്ള ഇഷ്ട പ്രവർത്തനം","favorite":"നിങ്ങൾക്ക് ശരിക്കും ഇഷ്ടമുള്ളത് തിരഞ്ഞെടുക്കുക","voice":"ശബ്ദത്തിൽ നിന്ന് മാറ്റിയ ടെക്സ്റ്റ്"
},
"Kannada": {
 "emotion":"ಭಾವನೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ","emoji":"Chatbot emoji check-in","stress":"ಒತ್ತಡದ ಮಟ್ಟ (0 = ಇಲ್ಲ, 10 = ತುಂಬಾ ಹೆಚ್ಚು)","questionnaire":"ಭಾವನಾತ್ಮಕ ಪ್ರಶ್ನಾವಳಿ","q1":"ನನಗೆ ಒತ್ತಡ ಅಥವಾ ಟೆನ್ಷನ್ ಅನುಭವವಾಗುತ್ತದೆ","q2":"ನನಗೆ ವಿಶ್ರಾಂತಿ ಪಡೆಯಲು ಕಷ್ಟವಾಗುತ್ತದೆ","q3":"ನನ್ನ ಆಲೋಚನೆಗಳನ್ನು ನಿಯಂತ್ರಿಸಲು ಕಷ್ಟವಾಗುತ್ತದೆ","q4":"ಕೆಲಸ/ಓದು ಅಥವಾ ದೈನಂದಿನ ಕಾರ್ಯಗಳು ಕಷ್ಟವಾಗುತ್ತವೆ","q5":"ನಾನು ದೈಹಿಕವಾಗಿ/ಭಾವನಾತ್ಮಕವಾಗಿ ತುಂಬಾ ದಣಿದಿದ್ದೇನೆ","safety_title":"ಭಯ, ಸುರಕ್ಷತೆ & ವೆಲ್‌ನೆಸ್","safety":"ಈಗ ನೀವು ಎಷ್ಟು ಸುರಕ್ಷಿತವಾಗಿ ಭಾವಿಸುತ್ತೀರಿ?","safe":"ನಾನು ಸುರಕ್ಷಿತವಾಗಿದ್ದೇನೆ","unsure":"ನನಗೆ ಖಚಿತವಿಲ್ಲ","unsafe":"ನಾನು ಸುರಕ್ಷಿತವಾಗಿಲ್ಲ","fear":"ನೀವು ಯಾವುದರ ಬಗ್ಗೆ ಹೆಚ್ಚು ಚಿಂತಿತರಾಗಿದ್ದೀರಿ ಅಥವಾ ಭಯಪಡುತ್ತೀರಿ? (ಐಚ್ಛಿಕ)","wellbeing":"ಇಂದಿನ ಒಟ್ಟು ವೆಲ್‌ನೆಸ್ (0 = ತುಂಬಾ ಕಡಿಮೆ, 10 = ತುಂಬಾ ಉತ್ತಮ)","favorite_title":"ಹೆಚ್ಚಿನ ಒತ್ತಡಕ್ಕೆ ಇಷ್ಟದ ಚಟುವಟಿಕೆ","favorite":"ನಿಮಗೆ ನಿಜವಾಗಿಯೂ ಇಷ್ಟವಾದುದನ್ನು ಆಯ್ಕೆಮಾಡಿ","voice":"ಧ್ವನಿಯಿಂದ ಬದಲಾದ ಪಠ್ಯ"
},
"Bengali": {
 "emotion":"অনুভূতি নির্বাচন করুন","emoji":"Chatbot emoji check-in","stress":"স্ট্রেসের মাত্রা (0 = নেই, 10 = অত্যন্ত বেশি)","questionnaire":"আবেগগত প্রশ্নাবলী","q1":"আমি উত্তেজিত বা চাপের মধ্যে আছি বলে মনে হয়","q2":"আমার আরাম করতে অসুবিধা হয়","q3":"আমার চিন্তা নিয়ন্ত্রণ করা কঠিন হয়","q4":"কাজ/পড়াশোনা বা দৈনন্দিন কাজ কঠিন মনে হয়","q5":"আমি শারীরিক/মানসিকভাবে খুব ক্লান্ত বোধ করি","safety_title":"ভয়, নিরাপত্তা ও সুস্থতা","safety":"এই মুহূর্তে আপনি কতটা নিরাপদ বোধ করছেন?","safe":"আমি নিরাপদ বোধ করছি","unsure":"আমি নিশ্চিত নই","unsafe":"আমি নিরাপদ বোধ করছি না","fear":"আপনি কোন বিষয় নিয়ে সবচেয়ে বেশি চিন্তিত বা ভীত? (ঐচ্ছিক)","wellbeing":"আজকের সামগ্রিক সুস্থতা (0 = খুব কম, 10 = খুব ভালো)","favorite_title":"বেশি স্ট্রেসের জন্য পছন্দের কার্যকলাপ","favorite":"আপনার সত্যিই পছন্দেরটি বেছে নিন","voice":"ভয়েস থেকে রূপান্তরিত লেখা"
},
"Marathi": {
 "emotion":"भावना निवडा","emoji":"Chatbot emoji check-in","stress":"तणावाची पातळी (0 = नाही, 10 = खूप जास्त)","questionnaire":"भावनिक प्रश्नावली","q1":"मला तणाव किंवा दबाव जाणवतो","q2":"मला आराम करणे कठीण जाते","q3":"माझे विचार नियंत्रित करणे कठीण जाते","q4":"काम/अभ्यास किंवा दैनंदिन कामे कठीण वाटतात","q5":"मला शारीरिक/भावनिकदृष्ट्या खूप थकवा जाणवतो","safety_title":"भीती, सुरक्षितता आणि वेलनेस","safety":"आत्ता तुम्हाला किती सुरक्षित वाटते?","safe":"मला सुरक्षित वाटते","unsure":"मला खात्री नाही","unsafe":"मला सुरक्षित वाटत नाही","fear":"तुम्हाला सर्वात जास्त कशाची चिंता किंवा भीती वाटते? (पर्यायी)","wellbeing":"आजचे एकूण वेलनेस (0 = खूप कमी, 10 = खूप चांगले)","favorite_title":"जास्त तणावासाठी आवडती क्रिया","favorite":"तुम्हाला खरोखर आवडणारी गोष्ट निवडा","voice":"आवाजातून बदललेला मजकूर"
},
"Gujarati": {
 "emotion":"ભાવના પસંદ કરો","emoji":"Chatbot emoji check-in","stress":"તણાવનું સ્તર (0 = નથી, 10 = ખૂબ વધારે)","questionnaire":"ભાવનાત્મક પ્રશ્નાવલી","q1":"મને તણાવ અથવા દબાણ અનુભવાય છે","q2":"મને આરામ કરવામાં મુશ્કેલી પડે છે","q3":"મારા વિચારોને નિયંત્રિત કરવું મુશ્કેલ છે","q4":"કામ/અભ્યાસ અથવા દૈનિક કાર્યો મુશ્કેલ લાગે છે","q5":"મને શારીરિક/ભાવનાત્મક રીતે ખૂબ થાક લાગે છે","safety_title":"ભય, સુરક્ષા અને વેલનેસ","safety":"હમણાં તમને કેટલું સુરક્ષિત લાગે છે?","safe":"હું સુરક્ષિત અનુભવું છું","unsure":"મને ખાતરી નથી","unsafe":"હું સુરક્ષિત અનુભવતો/અનુભવતી નથી","fear":"તમને સૌથી વધુ કઈ બાબતની ચિંતા અથવા ભય છે? (વૈકલ્પિક)","wellbeing":"આજનું કુલ વેલનેસ (0 = ખૂબ ઓછું, 10 = ખૂબ સારું)","favorite_title":"વધુ તણાવ માટે મનપસંદ પ્રવૃત્તિ","favorite":"તમને ખરેખર ગમે તે પસંદ કરો","voice":"અવાજમાંથી બદલાયેલ લખાણ"
},
"Punjabi": {
 "emotion":"ਭਾਵਨਾ ਚੁਣੋ","emoji":"Chatbot emoji check-in","stress":"ਤਣਾਅ ਦਾ ਪੱਧਰ (0 = ਨਹੀਂ, 10 = ਬਹੁਤ ਜ਼ਿਆਦਾ)","questionnaire":"ਭਾਵਨਾਤਮਕ ਪ੍ਰਸ਼ਨਾਵਲੀ","q1":"ਮੈਂ ਤਣਾਅ ਜਾਂ ਦਬਾਅ ਮਹਿਸੂਸ ਕਰਦਾ/ਕਰਦੀ ਹਾਂ","q2":"ਮੈਨੂੰ ਆਰਾਮ ਕਰਨਾ ਔਖਾ ਲੱਗਦਾ ਹੈ","q3":"ਮੇਰੇ ਵਿਚਾਰਾਂ ਨੂੰ ਕਾਬੂ ਕਰਨਾ ਔਖਾ ਹੈ","q4":"ਕੰਮ/ਪੜ੍ਹਾਈ ਜਾਂ ਰੋਜ਼ਾਨਾ ਕੰਮ ਔਖੇ ਲੱਗਦੇ ਹਨ","q5":"ਮੈਂ ਸਰੀਰਕ/ਭਾਵਨਾਤਮਕ ਤੌਰ 'ਤੇ ਬਹੁਤ ਥੱਕਿਆ ਮਹਿਸੂਸ ਕਰਦਾ/ਕਰਦੀ ਹਾਂ","safety_title":"ਡਰ, ਸੁਰੱਖਿਆ ਅਤੇ ਵੈਲਨੈੱਸ","safety":"ਇਸ ਵੇਲੇ ਤੁਸੀਂ ਕਿੰਨਾ ਸੁਰੱਖਿਅਤ ਮਹਿਸੂਸ ਕਰਦੇ ਹੋ?","safe":"ਮੈਂ ਸੁਰੱਖਿਅਤ ਮਹਿਸੂਸ ਕਰਦਾ/ਕਰਦੀ ਹਾਂ","unsure":"ਮੈਨੂੰ ਪੱਕਾ ਨਹੀਂ ਪਤਾ","unsafe":"ਮੈਂ ਸੁਰੱਖਿਅਤ ਮਹਿਸੂਸ ਨਹੀਂ ਕਰਦਾ/ਕਰਦੀ","fear":"ਤੁਹਾਨੂੰ ਸਭ ਤੋਂ ਵੱਧ ਕਿਸ ਗੱਲ ਦੀ ਚਿੰਤਾ ਜਾਂ ਡਰ ਹੈ? (ਵਿਕਲਪਿਕ)","wellbeing":"ਅੱਜ ਦੀ ਕੁੱਲ ਵੈਲਨੈੱਸ (0 = ਬਹੁਤ ਘੱਟ, 10 = ਬਹੁਤ ਵਧੀਆ)","favorite_title":"ਜ਼ਿਆਦਾ ਤਣਾਅ ਲਈ ਮਨਪਸੰਦ ਗਤੀਵਿਧੀ","favorite":"ਜੋ ਤੁਹਾਨੂੰ ਸੱਚਮੁੱਚ ਪਸੰਦ ਹੈ ਉਹ ਚੁਣੋ","voice":"ਆਵਾਜ਼ ਤੋਂ ਬਦਲਿਆ ਟੈਕਸਟ"
},
"Urdu": {
 "emotion":"جذبات منتخب کریں","emoji":"Chatbot emoji check-in","stress":"تناؤ کی سطح (0 = نہیں، 10 = بہت زیادہ)","questionnaire":"جذباتی سوالنامہ","q1":"مجھے تناؤ یا دباؤ محسوس ہوتا ہے","q2":"مجھے آرام کرنا مشکل لگتا ہے","q3":"اپنے خیالات کو قابو کرنا مشکل لگتا ہے","q4":"کام/پڑھائی یا روزمرہ کے کام مشکل لگتے ہیں","q5":"میں جسمانی/جذباتی طور پر بہت تھکا ہوا محسوس کرتا/کرتی ہوں","safety_title":"خوف، حفاظت اور فلاح","safety":"اس وقت آپ خود کو کتنا محفوظ محسوس کرتے ہیں؟","safe":"میں خود کو محفوظ محسوس کرتا/کرتی ہوں","unsure":"مجھے یقین نہیں ہے","unsafe":"میں خود کو محفوظ محسوس نہیں کرتا/کرتی","fear":"آپ کو سب سے زیادہ کس بات کی فکر یا خوف ہے؟ (اختیاری)","wellbeing":"آج کی مجموعی فلاح (0 = بہت کم، 10 = بہت اچھی)","favorite_title":"زیادہ تناؤ کے لیے پسندیدہ سرگرمی","favorite":"جو آپ کو واقعی پسند ہے اسے منتخب کریں","voice":"آواز سے تبدیل شدہ متن"
},
"Spanish": {
 "emotion":"Selecciona una emoción","emoji":"Check-in de emoji del chatbot","stress":"Nivel de estrés (0 = ninguno, 10 = extremo)","questionnaire":"Cuestionario emocional","q1":"Me siento tenso/a o bajo presión","q2":"Me cuesta relajarme","q3":"Me cuesta controlar mis pensamientos","q4":"El trabajo/estudio o las tareas diarias me resultan difíciles","q5":"Me siento física/emocionalmente agotado/a","safety_title":"Miedo, seguridad y bienestar","safety":"¿Qué tan seguro/a te sientes ahora?","safe":"Me siento seguro/a","unsure":"No estoy seguro/a","unsafe":"No me siento seguro/a","fear":"¿Qué es lo que más te preocupa o te da miedo? (opcional)","wellbeing":"Bienestar general hoy (0 = muy bajo, 10 = muy bueno)","favorite_title":"Actividad favorita para momentos de mucho estrés","favorite":"Elige algo que realmente disfrutes","voice":"Texto transcrito de voz"
},
"French": {
 "emotion":"Sélection de l’émotion","emoji":"Check-in emoji du chatbot","stress":"Niveau de stress (0 = aucun, 10 = extrême)","questionnaire":"Questionnaire émotionnel","q1":"Je me sens tendu(e) ou sous pression","q2":"J’ai du mal à me détendre","q3":"J’ai du mal à contrôler mes pensées","q4":"Le travail/les études ou les tâches quotidiennes me semblent difficiles","q5":"Je me sens physiquement/émotionnellement épuisé(e)","safety_title":"Peur, sécurité et bien-être","safety":"À quel point vous sentez-vous en sécurité maintenant ?","safe":"Je me sens en sécurité","unsure":"Je ne suis pas sûr(e)","unsafe":"Je ne me sens pas en sécurité","fear":"Qu’est-ce qui vous inquiète ou vous fait le plus peur ? (facultatif)","wellbeing":"Bien-être général aujourd’hui (0 = très faible, 10 = très bon)","favorite_title":"Activité préférée en cas de stress élevé","favorite":"Choisissez ce que vous aimez vraiment","voice":"Texte transcrit de la voix"
},
"German": {
 "emotion":"Emotion auswählen","emoji":"Chatbot-Emoji-Check-in","stress":"Stresslevel (0 = keiner, 10 = extrem)","questionnaire":"Emotionaler Fragebogen","q1":"Ich fühle mich angespannt oder unter Druck","q2":"Ich kann mich nur schwer entspannen","q3":"Ich kann meine Gedanken nur schwer kontrollieren","q4":"Arbeit/Studium oder tägliche Aufgaben fühlen sich schwierig an","q5":"Ich fühle mich körperlich/emotional erschöpft","safety_title":"Angst, Sicherheit & Wohlbefinden","safety":"Wie sicher fühlen Sie sich gerade?","safe":"Ich fühle mich sicher","unsure":"Ich bin mir nicht sicher","unsafe":"Ich fühle mich nicht sicher","fear":"Worüber machen Sie sich am meisten Sorgen oder wovor haben Sie Angst? (optional)","wellbeing":"Allgemeines Wohlbefinden heute (0 = sehr niedrig, 10 = sehr gut)","favorite_title":"Lieblingsaktivität bei hohem Stress","favorite":"Wählen Sie etwas, das Sie wirklich mögen","voice":"Transkribierter Sprachtext"
},
"Japanese": {
 "emotion":"感情を選択してください","emoji":"チャットボット絵文字チェックイン","stress":"ストレスレベル（0＝なし、10＝非常に高い）","questionnaire":"感情に関する質問票","q1":"緊張している、またはプレッシャーを感じる","q2":"リラックスするのが難しい","q3":"考えをコントロールするのが難しい","q4":"仕事・勉強や日常の作業が難しく感じる","q5":"身体的・感情的にとても疲れている","safety_title":"恐怖・安全・ウェルビーイング","safety":"今、どのくらい安全だと感じますか？","safe":"安全だと感じます","unsure":"よく分かりません","unsafe":"安全だと感じません","fear":"一番心配していること、または怖いことは何ですか？（任意）","wellbeing":"今日の全体的なウェルビーイング（0＝とても低い、10＝とても良い）","favorite_title":"強いストレス時の好きな活動","favorite":"本当に好きなものを選んでください","voice":"音声から変換されたテキスト"
},
}

def stext(key):
    lang = st.session_state.get("language", "English")
    return SCREENING_TEXT.get(lang, SCREENING_TEXT["English"]).get(key, SCREENING_TEXT["English"].get(key, key))

# Complete core UI translations for all 15 supported languages.
CORE_UI = {
    "Telugu": {"title":"StressCare AI","subtitle":"బహుభాషా ఒత్తిడి స్క్రీనింగ్, సహాయం మరియు వెల్‌నెస్ డ్యాష్‌బోర్డ్","consent":"వెల్‌నెస్ స్క్రీనింగ్ మరియు సహాయం కోసం ఈ session ఉపయోగానికి నేను సమ్మతిస్తున్నాను.","anonymous":"అనామక మోడ్","language":"భాష","pause":"Session ఆపండి","resume":"కొనసాగించండి","emergency":"తక్షణ అత్యవసర సహాయం","analyze":"నా వెల్‌నెస్‌ను విశ్లేషించండి","free_text":"మీకు ఎలా అనిపిస్తోంది? ఏమి జరుగుతుందో వివరించండి.","risk":"ప్రమాద స్థాయి","stress":"ఒత్తిడి స్కోర్","confidence":"నమ్మకం","chat":"AI సహాయ Chat","activities":"వ్యక్తిగత కార్యకలాపాలు","schedule":"పనులు & రిమైండర్లు","media":"ఫోటో / వీడియో","draw":"Paint వంటి Drawing","human":"మానవ సహాయం","dashboard":"డ్యాష్‌బోర్డ్","reports":"రిపోర్టులు & Privacy"},
    "Malayalam": {"title":"StressCare AI","subtitle":"ബഹുഭാഷാ സമ്മർദ്ദ പരിശോധന, പിന്തുണ, വെൽനെസ് ഡാഷ്ബോർഡ്","consent":"വെൽനെസ് പരിശോധനയ്ക്കും പിന്തുണയ്ക്കുമായി ഈ session ഉപയോഗിക്കാൻ ഞാൻ സമ്മതിക്കുന്നു.","anonymous":"അജ്ഞാത മോഡ്","language":"ഭാഷ","pause":"Session നിർത്തുക","resume":"തുടരുക","emergency":"തൽക്ഷണ അടിയന്തര സഹായം","analyze":"എന്റെ വെൽനെസ് പരിശോധിക്കുക","free_text":"നിങ്ങൾക്ക് എങ്ങനെ തോന്നുന്നു? എന്താണ് സംഭവിക്കുന്നത് എന്ന് എഴുതുക.","risk":"റിസ്ക് നില","stress":"സമ്മർദ്ദ സ്കോർ","confidence":"വിശ്വാസനില","chat":"AI സഹായ Chat","activities":"വ്യക്തിഗത പ്രവർത്തനങ്ങൾ","schedule":"ടാസ്കുകളും റിമൈൻഡറുകളും","media":"ഫോട്ടോ / വീഡിയോ","draw":"Paint പോലുള്ള Drawing","human":"മനുഷ്യ സഹായം","dashboard":"ഡാഷ്ബോർഡ്","reports":"റിപ്പോർട്ടുകളും Privacy"},
    "Kannada": {"title":"StressCare AI","subtitle":"ಬಹುಭಾಷಾ ಒತ್ತಡ ಸ್ಕ್ರೀನಿಂಗ್, ಬೆಂಬಲ ಮತ್ತು ವೆಲ್‌ನೆಸ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್","consent":"ವೆಲ್‌ನೆಸ್ ಸ್ಕ್ರೀನಿಂಗ್ ಮತ್ತು ಬೆಂಬಲಕ್ಕಾಗಿ ಈ session ಬಳಕೆಗೆ ನಾನು ಒಪ್ಪುತ್ತೇನೆ.","anonymous":"ಅನಾಮಧೇಯ ಮೋಡ್","language":"ಭಾಷೆ","pause":"Session ನಿಲ್ಲಿಸಿ","resume":"ಮುಂದುವರಿಸಿ","emergency":"ತಕ್ಷಣದ ತುರ್ತು ಸಹಾಯ","analyze":"ನನ್ನ ವೆಲ್‌ನೆಸ್ ವಿಶ್ಲೇಷಿಸಿ","free_text":"ನಿಮಗೆ ಹೇಗನಿಸುತ್ತಿದೆ? ಏನಾಗುತ್ತಿದೆ ಎಂದು ವಿವರಿಸಿ.","risk":"ಅಪಾಯದ ಮಟ್ಟ","stress":"ಒತ್ತಡ ಸ್ಕೋರ್","confidence":"ವಿಶ್ವಾಸ","chat":"AI ಸಹಾಯ Chat","activities":"ವೈಯಕ್ತಿಕ ಚಟುವಟಿಕೆಗಳು","schedule":"ಕಾರ್ಯಗಳು & ಜ್ಞಾಪನೆಗಳು","media":"ಫೋಟೋ / ವೀಡಿಯೊ","draw":"Paint ರೀತಿಯ Drawing","human":"ಮಾನವ ಸಹಾಯ","dashboard":"ಡ್ಯಾಶ್‌ಬೋರ್ಡ್","reports":"ವರದಿಗಳು & Privacy"},
    "Bengali": {"title":"StressCare AI","subtitle":"বহুভাষিক স্ট্রেস স্ক্রিনিং, সহায়তা এবং ওয়েলনেস ড্যাশবোর্ড","consent":"ওয়েলনেস স্ক্রিনিং ও সহায়তার জন্য এই session ব্যবহারে আমি সম্মত।","anonymous":"অ্যানোনিমাস মোড","language":"ভাষা","pause":"Session থামান","resume":"চালিয়ে যান","emergency":"তাৎক্ষণিক জরুরি সহায়তা","analyze":"আমার ওয়েলনেস বিশ্লেষণ করুন","free_text":"আপনি কেমন অনুভব করছেন? কী হচ্ছে লিখুন।","risk":"ঝুঁকির স্তর","stress":"স্ট্রেস স্কোর","confidence":"আত্মবিশ্বাস","chat":"AI সহায়তা Chat","activities":"ব্যক্তিগত কার্যক্রম","schedule":"কাজ ও রিমাইন্ডার","media":"ফটো / ভিডিও","draw":"Paint-এর মতো Drawing","human":"মানব সহায়তা","dashboard":"ড্যাশবোর্ড","reports":"রিপোর্ট ও Privacy"},
    "Marathi": {"title":"StressCare AI","subtitle":"बहुभाषिक ताण तपासणी, सहाय्य आणि वेलनेस डॅशबोर्ड","consent":"वेलनेस तपासणी आणि सहाय्यासाठी हे session वापरण्यास माझी संमती आहे.","anonymous":"अनामिक मोड","language":"भाषा","pause":"Session थांबवा","resume":"पुढे सुरू ठेवा","emergency":"तात्काळ आपत्कालीन मदत","analyze":"माझ्या वेलनेसचे विश्लेषण करा","free_text":"तुम्हाला कसे वाटत आहे? काय घडत आहे ते लिहा.","risk":"जोखीम पातळी","stress":"ताण स्कोअर","confidence":"विश्वास","chat":"AI सहाय्य Chat","activities":"वैयक्तिक उपक्रम","schedule":"कामे आणि स्मरणपत्रे","media":"फोटो / व्हिडिओ","draw":"Paint सारखे Drawing","human":"मानवी मदत","dashboard":"डॅशबोर्ड","reports":"अहवाल आणि Privacy"},
    "Gujarati": {"title":"StressCare AI","subtitle":"બહુભાષી તણાવ સ્ક્રીનિંગ, સહાય અને વેલનેસ ડેશબોર્ડ","consent":"વેલનેસ સ્ક્રીનિંગ અને સહાય માટે આ session ના ઉપયોગ માટે હું સંમત છું.","anonymous":"અનામિક મોડ","language":"ભાષા","pause":"Session થોભાવો","resume":"ચાલુ રાખો","emergency":"તાત્કાલિક કટોકટી સહાય","analyze":"મારી વેલનેસનું વિશ્લેષણ કરો","free_text":"તમને કેવું લાગે છે? શું થઈ રહ્યું છે તે લખો.","risk":"જોખમ સ્તર","stress":"તણાવ સ્કોર","confidence":"વિશ્વાસ","chat":"AI સહાય Chat","activities":"વ્યક્તિગત પ્રવૃત્તિઓ","schedule":"કાર્યો અને રિમાઇન્ડર્સ","media":"ફોટો / વિડિયો","draw":"Paint જેવી Drawing","human":"માનવ સહાય","dashboard":"ડેશબોર્ડ","reports":"રિપોર્ટ્સ અને Privacy"},
    "Punjabi": {"title":"StressCare AI","subtitle":"ਬਹੁਭਾਸ਼ੀ ਤਣਾਅ ਸਕ੍ਰੀਨਿੰਗ, ਸਹਾਇਤਾ ਅਤੇ ਵੈਲਨੈੱਸ ਡੈਸ਼ਬੋਰਡ","consent":"ਵੈਲਨੈੱਸ ਸਕ੍ਰੀਨਿੰਗ ਅਤੇ ਸਹਾਇਤਾ ਲਈ ਇਸ session ਦੀ ਵਰਤੋਂ ਲਈ ਮੈਂ ਸਹਿਮਤ ਹਾਂ।","anonymous":"ਅਨਾਮ ਮੋਡ","language":"ਭਾਸ਼ਾ","pause":"Session ਰੋਕੋ","resume":"ਜਾਰੀ ਰੱਖੋ","emergency":"ਤੁਰੰਤ ਐਮਰਜੈਂਸੀ ਸਹਾਇਤਾ","analyze":"ਮੇਰੀ ਵੈਲਨੈੱਸ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰੋ","free_text":"ਤੁਸੀਂ ਕਿਵੇਂ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ? ਕੀ ਹੋ ਰਿਹਾ ਹੈ ਲਿਖੋ।","risk":"ਖਤਰੇ ਦਾ ਪੱਧਰ","stress":"ਤਣਾਅ ਸਕੋਰ","confidence":"ਭਰੋਸਾ","chat":"AI ਸਹਾਇਤਾ Chat","activities":"ਵਿਅਕਤੀਗਤ ਗਤੀਵਿਧੀਆਂ","schedule":"ਕੰਮ ਅਤੇ ਰਿਮਾਈਂਡਰ","media":"ਫੋਟੋ / ਵੀਡੀਓ","draw":"Paint ਵਰਗੀ Drawing","human":"ਮਨੁੱਖੀ ਸਹਾਇਤਾ","dashboard":"ਡੈਸ਼ਬੋਰਡ","reports":"ਰਿਪੋਰਟਾਂ ਅਤੇ Privacy"},
    "Urdu": {"title":"StressCare AI","subtitle":"کثیر لسانی ذہنی دباؤ اسکریننگ، مدد اور فلاحی ڈیش بورڈ","consent":"فلاحی اسکریننگ اور مدد کے لیے اس session کے استعمال پر میں رضامند ہوں۔","anonymous":"گمنام موڈ","language":"زبان","pause":"Session روکیں","resume":"جاری رکھیں","emergency":"فوری ہنگامی مدد","analyze":"میری فلاح کا تجزیہ کریں","free_text":"آپ کیسا محسوس کر رہے ہیں؟ کیا ہو رہا ہے بیان کریں۔","risk":"خطرے کی سطح","stress":"ذہنی دباؤ اسکور","confidence":"اعتماد","chat":"AI مدد Chat","activities":"ذاتی سرگرمیاں","schedule":"کام اور یاددہانیاں","media":"تصویر / ویڈیو","draw":"Paint جیسی Drawing","human":"انسانی مدد","dashboard":"ڈیش بورڈ","reports":"رپورٹس اور Privacy"},
    "Spanish": {"title":"StressCare AI","subtitle":"Panel multilingüe de detección de estrés, apoyo y bienestar","consent":"Acepto usar esta sesión para la evaluación y el apoyo del bienestar.","anonymous":"Modo anónimo","language":"Idioma","pause":"Pausar sesión","resume":"Continuar","emergency":"Ayuda de emergencia inmediata","analyze":"Analizar mi bienestar","free_text":"¿Cómo te sientes? Describe lo que está pasando.","risk":"Nivel de riesgo","stress":"Puntuación de estrés","confidence":"Confianza","chat":"Chat de apoyo de IA","activities":"Actividades personalizadas","schedule":"Tareas y recordatorios","media":"Foto / Video","draw":"Dibujo tipo Paint","human":"Apoyo humano","dashboard":"Panel","reports":"Informes y privacidad"},
    "French": {"title":"StressCare AI","subtitle":"Dépistage multilingue du stress, soutien et tableau de bien-être","consent":"J'accepte d'utiliser cette session pour l'évaluation et le soutien du bien-être.","anonymous":"Mode anonyme","language":"Langue","pause":"Mettre la session en pause","resume":"Continuer","emergency":"Aide d'urgence immédiate","analyze":"Analyser mon bien-être","free_text":"Comment vous sentez-vous ? Décrivez ce qui se passe.","risk":"Niveau de risque","stress":"Score de stress","confidence":"Confiance","chat":"Chat de soutien IA","activities":"Activités personnalisées","schedule":"Tâches et rappels","media":"Photo / Vidéo","draw":"Dessin type Paint","human":"Soutien humain","dashboard":"Tableau de bord","reports":"Rapports et confidentialité"},
    "German": {"title":"StressCare AI","subtitle":"Mehrsprachiges Stress-Screening, Unterstützung und Wohlbefinden-Dashboard","consent":"Ich stimme der Nutzung dieser Sitzung für Wohlbefindens-Screening und Unterstützung zu.","anonymous":"Anonymer Modus","language":"Sprache","pause":"Sitzung pausieren","resume":"Fortsetzen","emergency":"Sofortige Notfallhilfe","analyze":"Mein Wohlbefinden analysieren","free_text":"Wie fühlen Sie sich? Beschreiben Sie, was passiert.","risk":"Risikostufe","stress":"Stresswert","confidence":"Vertrauen","chat":"KI-Unterstützungs-Chat","activities":"Personalisierte Aktivitäten","schedule":"Aufgaben & Erinnerungen","media":"Foto / Video","draw":"Paint-ähnliches Zeichnen","human":"Menschliche Unterstützung","dashboard":"Dashboard","reports":"Berichte & Datenschutz"},
    "Japanese": {"title":"StressCare AI","subtitle":"多言語ストレスチェック・サポート・ウェルビーイングダッシュボード","consent":"ウェルビーイングの確認とサポートのため、このセッションを使用することに同意します。","anonymous":"匿名モード","language":"言語","pause":"セッションを一時停止","resume":"続ける","emergency":"緊急サポート","analyze":"自分の状態を分析","free_text":"今どんな気分ですか？起きていることを説明してください。","risk":"リスクレベル","stress":"ストレススコア","confidence":"信頼度","chat":"AIサポートチャット","activities":"パーソナライズされた活動","schedule":"タスクとリマインダー","media":"写真 / 動画","draw":"Paint風のお絵描き","human":"人によるサポート","dashboard":"ダッシュボード","reports":"レポートとプライバシー"},
}
UI.update(CORE_UI)

# Fill untranslated UI keys with English so every language remains usable.
for lang in LANGUAGES:
    if lang not in UI:
        UI[lang] = UI["English"].copy()
    else:
        for k, v in UI["English"].items():
            UI[lang].setdefault(k, v)


# ---------------------------------------------------------------------------
# 2. MULTILINGUAL NLP LEXICONS
# ---------------------------------------------------------------------------

STRESS_WORDS = {
    "en": ["stress", "stressed", "anxious", "anxiety", "panic", "worried", "worry",
           "overwhelmed", "pressure", "sad", "depressed", "angry", "fear", "scared",
           "can't sleep", "insomnia", "exhausted", "burnout", "hopeless", "crying"],
    "ta": ["மன அழுத்தம்", "கவலை", "பயம்", "அழுத்தம்", "சோகம்", "கோபம்", "தூக்கம் இல்லை",
           "சோர்வு", "தாங்க முடியவில்லை", "அழுகிறேன்", "பதட்டம்"],
    "hi": ["तनाव", "चिंता", "डर", "दबाव", "उदास", "गुस्सा", "नींद नहीं", "थकान",
           "घबराहट", "रोना", "परेशान"],
    "te": ["ఒత్తిడి", "ఆందోళన", "భయం", "బాధ", "కోపం", "నిద్ర లేదు", "అలసట"],
    "ml": ["സമ്മർദ്ദം", "ഉത്കണ്ഠ", "ഭയം", "ദുഃഖം", "കോപം", "ഉറക്കം ഇല്ല", "ക്ഷീണം"],
    "kn": ["ಒತ್ತಡ", "ಆತಂಕ", "ಭಯ", "ದುಃಖ", "ಕೋಪ", "ನಿದ್ರೆ ಇಲ್ಲ", "ಆಯಾಸ"],
    "bn": ["চাপ", "উদ্বেগ", "ভয়", "দুঃখ", "রাগ", "ঘুম নেই", "ক্লান্ত"],
    "mr": ["ताण", "चिंता", "भीती", "दुःख", "राग", "झोप नाही", "थकवा"],
    "gu": ["તણાવ", "ચિંતા", "ભય", "દુઃખ", "ગુસ્સો", "ઊંઘ નથી", "થાક"],
    "pa": ["ਤਣਾਅ", "ਚਿੰਤਾ", "ਡਰ", "ਉਦਾਸ", "ਗੁੱਸਾ", "ਨੀਂਦ ਨਹੀਂ", "ਥਕਾਵਟ"],
    "ur": ["تناؤ", "فکر", "خوف", "اداس", "غصہ", "نیند نہیں", "تھکن"],
    "es": ["estrés", "ansiedad", "miedo", "preocupado", "triste", "enojado",
           "presión", "no puedo dormir", "agotado", "pánico"],
    "fr": ["stress", "anxiété", "peur", "inquiet", "triste", "colère", "pression",
           "je ne dors pas", "épuisé", "panique"],
    "de": ["stress", "angst", "besorgt", "traurig", "wütend", "druck", "schlaf",
           "erschöpft", "panik"],
    "ja": ["ストレス", "不安", "心配", "怖い", "悲しい", "怒り", "眠れない", "疲れた", "パニック"],
}

POSITIVE_WORDS = {
    "en": ["happy", "calm", "good", "great", "relaxed", "hopeful", "excited", "okay",
           "fine", "peaceful", "better", "joy"],
    "ta": ["சந்தோஷம்", "நன்றாக", "அமைதி", "நம்பிக்கை", "சரி", "மகிழ்ச்சி"],
    "hi": ["खुश", "अच्छा", "शांत", "उम्मीद", "ठीक", "मज़ा"],
    "te": ["సంతోషం", "బాగుంది", "శాంతి", "ఆశ", "సరే"],
    "ml": ["സന്തോഷം", "നല്ലത്", "ശാന്തം", "പ്രതീക്ഷ", "ശരി"],
    "kn": ["ಸಂತೋಷ", "ಚೆನ್ನಾಗಿದೆ", "ಶಾಂತ", "ಭರವಸೆ", "ಸರಿ"],
    "bn": ["খুশি", "ভালো", "শান্ত", "আশা", "ঠিক"],
    "mr": ["आनंदी", "छान", "शांत", "आशा", "ठीक"],
    "gu": ["ખુશ", "સારું", "શાંત", "આશા", "બરાબર"],
    "pa": ["ਖੁਸ਼", "ਚੰਗਾ", "ਸ਼ਾਂਤ", "ਉਮੀਦ", "ਠੀਕ"],
    "ur": ["خوش", "اچھا", "پرسکون", "امید", "ٹھیک"],
    "es": ["feliz", "bien", "tranquilo", "esperanza", "genial", "relajado"],
    "fr": ["heureux", "bien", "calme", "espoir", "super", "détendu"],
    "de": ["glücklich", "gut", "ruhig", "hoffnung", "entspannt", "prima"],
    "ja": ["幸せ", "良い", "落ち着いて", "希望", "大丈夫", "嬉しい"],
}

EMERGENCY_PHRASES = [
    "kill myself", "suicide", "want to die", "end my life", "self harm",
    "hurt myself", "don't feel safe", "do not feel safe", "unsafe",
    "i am in danger", "someone is hurting me", "rape", "assault",
    "தற்கொலை", "சாக வேண்டும்", "என்னை காயப்படுத்த", "பாதுகாப்பாக இல்லை",
    "खुदकुशी", "मरना चाहता", "सुरक्षित नहीं", "मुझे खतरा है",
    "suicidio", "no me siento seguro", "me quiero morir",
    "suicide", "je ne me sens pas en sécurité",
    "ich fühle mich nicht sicher", "自殺", "安全ではない",
]


# ---------------------------------------------------------------------------
# 3. ACTIVITIES / RESOURCES
# ---------------------------------------------------------------------------

ACTIVITIES = {
    "Cooking": {
        "youtube": "cooking recipes relaxing easy recipes",
        "description": "Watch or follow a simple cooking activity.",
    },
    "Puzzle games": {
        "youtube": "relaxing puzzle games",
        "description": "Try a low-pressure puzzle game.",
    },
    "Car / Racing games": {
        "youtube": "relaxing car racing gameplay",
        "description": "Try a casual driving or racing game.",
    },
    "Drawing": {
        "youtube": "easy relaxing drawing tutorial",
        "description": "Use the built-in paint-like canvas.",
    },
    "Music": {
        "youtube": "relaxing music playlist",
        "description": "Listen to music you enjoy.",
    },
    "Dance": {
        "youtube": "beginner dance workout tutorial",
        "description": "Try a short dance routine.",
    },
    "Breathing / Meditation": {
        "youtube": "guided breathing meditation",
        "description": "Try a short grounding/breathing exercise.",
    },
    "Study / Productive planning": {
        "youtube": "study with me productivity planning",
        "description": "Break work into one small manageable task.",
    },
    "Comedy": {
        "youtube": "clean comedy relaxing videos",
        "description": "Watch something light and positive.",
    },
    "Nature": {
        "youtube": "relaxing nature sounds",
        "description": "Try a short nature/grounding break.",
    },
}

GAME_LINKS = {
    "Puzzle": "https://poki.com/en/puzzle",
    "Car / Racing": "https://poki.com/en/driving",
    "Arcade": "https://poki.com/en/arcade",
    "Strategy": "https://poki.com/en/strategy",
    "Sports": "https://poki.com/en/sports",
    "Multiplayer": "https://poki.com/en/multiplayer",
    "Action": "https://poki.com/en/action",
    "All games": "https://poki.com/",
}

EMERGENCY_CONTACTS = {
    "Emergency / ERSS": "112",
    "Ambulance": "102",
    "Police": "100",
    "Mental-health Tele-MANAS": "14416",
    "Women Helpline": "181",
    "Child Helpline": "1098",
}


# ---------------------------------------------------------------------------
# 4. SESSION STATE / PRIVACY
# ---------------------------------------------------------------------------

def new_session_id():
    raw = f"{datetime.now().isoformat()}-{os.urandom(8).hex()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def init_state():
    defaults = {
        "language": "English",
        "consent": False,
        "anonymous": True,
        "session_id": new_session_id(),
        "paused": False,
        "notification_mode": True,
        "session_start": datetime.now(),
        "risk_history": [],
        "emotion_history": [],
        "chat_history": [],
        "schedule": [],
        "staff_notifications": [],
        "feedback": [],
        "photos": [],
        "videos": [],
        "last_analysis": None,
        "favorite_activity": "Music",
        "fear": "",
        "safety": "I feel safe",
        "wellbeing": 5,
        "support_resistance": False,
        "emergency_contact": "",
        "meeting_url": "",
        "chat_audio_hash": "",
        "pending_chat_voice": "",
        "chat_voice_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def ui(key):
    return UI[st.session_state.language].get(key, UI["English"].get(key, key))


# ---------------------------------------------------------------------------
# 5. PREPROCESSING ENGINE
# ---------------------------------------------------------------------------

def mask_sensitive(text):
    """Mask common sensitive identifiers before analytics."""
    if not text:
        return ""
    patterns = [
        (r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL]"),
        (r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b", "[PHONE]"),
        (r"\b\d{12}\b", "[ID]"),
        (r"https?://\S+", "[URL]"),
    ]
    out = text
    for pattern, replacement in patterns:
        out = re.sub(pattern, replacement, out, flags=re.I)
    return out


def normalize_text(text):
    """Unicode normalization + whitespace/noise cleanup."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("\x00", " ")
    text = re.sub(r"(.)\1{4,}", r"\1\1\1", text)
    text = re.sub(r"[ \t\r\n]+", " ", text).strip()
    return text


def detect_language(text, fallback="en"):
    if not text or detect is None:
        return fallback
    try:
        code = detect(text)
        supported = {v["code"] for v in LANGUAGES.values()}
        return code if code in supported else fallback
    except Exception:
        return fallback


def extract_context(text):
    t = text.lower()
    context = []
    groups = {
        "Work / Study": ["work", "office", "job", "study", "exam", "college", "school",
                         "வேலை", "படிப்பு", "தேர்வு"],
        "Family / Relationship": ["family", "parent", "parents", "friend", "relationship",
                                  "husband", "wife", "குடும்பம்", "நண்பர்"],
        "Sleep": ["sleep", "insomnia", "night", "தூக்கம்", "உறக்கம்"],
        "Financial": ["money", "debt", "salary", "financial", "பணம்", "கடன்"],
        "Health": ["health", "pain", "ill", "sick", "hospital", "உடல்", "வலி"],
    }
    for label, words in groups.items():
        if any(w in t for w in words):
            context.append(label)
    return context or ["General wellbeing"]


def detect_emergency(text, safety_answer):
    t = text.lower()
    return safety_answer.lower().startswith("i don't") or any(
        phrase in t for phrase in EMERGENCY_PHRASES
    )


def word_hits(text, lexicon):
    t = text.lower()
    return sum(1 for word in lexicon if word in t)


def infer_emotion(text, selected_emotion, stress_slider):
    t = text.lower()
    stress_hits = word_hits(t, STRESS_WORDS)
    positive_hits = word_hits(t, POSITIVE_WORDS)

    if selected_emotion != "Not sure":
        emotion = selected_emotion
    elif stress_hits >= 2:
        emotion = "Anxious"
    elif "sad" in t or "சோகம்" in t or "उदास" in t:
        emotion = "Sad"
    elif "angry" in t or "கோபம்" in t or "गुस्सा" in t:
        emotion = "Angry"
    elif positive_hits >= 2:
        emotion = "Calm / Happy"
    else:
        emotion = "Neutral / Mixed"

    sentiment = "Negative" if stress_hits > positive_hits else (
        "Positive" if positive_hits > stress_hits else "Mixed"
    )
    return emotion, sentiment, stress_hits, positive_hits


def calculate_risk(text, selected_emotion, stress_slider, questionnaire,
                   safety_answer, wellbeing):
    emotion, sentiment, stress_hits, positive_hits = infer_emotion(
        text, selected_emotion, stress_slider
    )

    q_avg = sum(questionnaire) / max(1, len(questionnaire))
    distress = min(10.0, (stress_hits * 1.0) + (10 - wellbeing) * 0.55 + q_avg * 0.65)
    score = min(10.0, max(0.0, stress_slider * 0.45 + q_avg * 0.40 + distress * 0.45))

    urgent = detect_emergency(text, safety_answer)

    if urgent:
        risk = "URGENT"
        score = 10.0
    elif score >= 7.0:
        risk = "HIGH"
    elif score >= 4.0:
        risk = "MODERATE"
    else:
        risk = "LOW"

    context = extract_context(text)

    missing = []
    if not text.strip():
        missing.append("Free-text description")
    if selected_emotion == "Not sure":
        missing.append("Emotion selection")
    if not questionnaire:
        missing.append("Questionnaire")

    # Input consistency check: compare slider, questionnaire and text signal.
    text_signal = min(10, stress_hits * 2)
    consistency_gap = abs(stress_slider - ((q_avg + text_signal) / 2))
    consistency = "Consistent" if consistency_gap <= 3.0 else "Review recommended"

    # Confidence estimation: heuristic, not clinical probability.
    evidence = 0
    evidence += 2 if text.strip() else 0
    evidence += 2 if selected_emotion != "Not sure" else 0
    evidence += 2 if questionnaire else 0
    evidence += 1 if stress_hits or positive_hits else 0
    confidence = round(min(0.98, 0.45 + evidence * 0.07), 2)

    features = {
        "stress_slider": stress_slider,
        "questionnaire_average": round(q_avg, 2),
        "distress_signal": round(distress, 2),
        "stress_word_hits": stress_hits,
        "positive_word_hits": positive_hits,
        "wellbeing": wellbeing,
        "context_count": len(context),
        "safety_flag": urgent,
    }

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "emotion": emotion,
        "sentiment": sentiment,
        "distress_score": round(distress, 2),
        "stress_score": round(score, 2),
        "risk": risk,
        "context": context,
        "missing_inputs": missing,
        "consistency": consistency,
        "confidence": confidence,
        "features": features,
        "masked_text": mask_sensitive(normalize_text(text)),
        "detected_language": detect_language(text, LANGUAGES[st.session_state.language]["code"]),
    }


# ---------------------------------------------------------------------------
# 6. SUPPORT / CHATBOT
# ---------------------------------------------------------------------------

def support_response(user_text, analysis=None):
    """Optional OpenAI response; safe offline fallback if API is not configured."""
    user_text = normalize_text(user_text)
    risk = (analysis or {}).get("risk", "LOW")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            api_key = ""

    if OpenAI is not None and api_key:
        try:
            client = OpenAI(api_key=api_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            system = (
                "You are a supportive wellbeing chatbot inside a stress-analysis demo. "
                "Be empathetic, concise and practical. Do not diagnose or claim certainty. "
                "If the user indicates immediate danger, self-harm, abuse or feels unsafe, "
                "tell them to contact local emergency services/trusted support immediately. "
                "Suggest grounding, breaks and human support when appropriate."
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    *[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history[-8:]
                    ],
                    {"role": "user", "content": user_text},
                ],
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            st.warning(f"AI backend unavailable; using offline support. ({exc})")

    low = user_text.lower()
    if any(p in low for p in EMERGENCY_PHRASES):
        return (
            "I’m glad you told me. Your immediate safety matters. Please contact "
            "emergency support or a trusted person now. In India, you can use 112 for "
            "emergency assistance or Tele-MANAS at 14416 for mental-health support."
        )
    if risk in ("HIGH", "URGENT"):
        return (
            "You seem to be under a lot of pressure. Let’s reduce the next step: "
            "pause for a few minutes, take slow breaths, and choose one activity you enjoy. "
            "If this feels difficult to manage alone, please connect with a trusted person "
            "or the human-support option in this app."
        )
    if "sleep" in low or "தூக்கம்" in low:
        return "Try a short screen break, slow breathing and a simple wind-down routine."
    if "work" in low or "study" in low:
        return "Let’s make it smaller: choose one task, set a short timer, then take a break."
    return (
        "I hear you. You can tell me what is bothering you, and we can break it into "
        "one small next step. You can also choose an activity from the Activities tab."
    )


def browser_speak(text, lang):
    """Fallback voice response using the browser's built-in speech synthesis."""
    import json as _json

    safe_text = _json.dumps(str(text), ensure_ascii=False)
    safe_lang = _json.dumps(LANGUAGES[lang]["tts"])

    components.html(
        f"""
        <script>
        const text = {safe_text};
        const lang = {safe_lang};
        if ("speechSynthesis" in window) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }}
        </script>
        """,
        height=0,
    )


def speak_text(text, lang):
    """Generate an MP3 safely on Windows/Linux/macOS; fall back to browser speech."""
    if not text:
        return

    if gTTS is not None:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                temp_path = tmp.name

            gTTS(text=text[:2500], lang=LANGUAGES[lang]["tts"]).save(temp_path)

            with open(temp_path, "rb") as audio_file:
                audio_data = audio_file.read()

            if audio_data:
                st.audio(audio_data, format="audio/mp3")
                return
        except Exception as exc:
            st.info(f"gTTS is unavailable, so browser voice is being used. ({exc})")
        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    browser_speak(text, lang)


def speech_to_text(audio_bytes, language_code):
    if sr is None:
        return None, "SpeechRecognition is not installed. Run: python -m pip install SpeechRecognition"
    if not audio_bytes:
        return None, "The recording is empty."

    try:
        import io
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language=language_code)
        if not text.strip():
            return None, "No speech was detected."
        return text.strip(), None
    except sr.UnknownValueError:
        return None, "Speech was not clear enough to recognize. Try again in a quieter place."
    except sr.RequestError as exc:
        return None, f"Speech recognition service could not be reached. Check internet access. Details: {exc}"
    except Exception as exc:
        return None, f"Audio could not be processed. Details: {exc}"


# ---------------------------------------------------------------------------
# 7. SCHEDULING / REPORT HELPERS
# ---------------------------------------------------------------------------

def add_staff_notification(reason, risk=""):
    st.session_state.staff_notifications.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
        "risk": risk,
        "reviewed": False,
    })


def youtube_search(activity):
    from urllib.parse import quote_plus
    query = ACTIVITIES.get(activity, ACTIVITIES["Music"])["youtube"]
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"


def build_report():
    return {
        "app": "StressCare AI",
        "session_id": st.session_state.session_id if st.session_state.anonymous else "identified_session_disabled",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "anonymous_mode": st.session_state.anonymous,
        "screenings": st.session_state.risk_history,
        "emotion_history": st.session_state.emotion_history,
        "schedule": st.session_state.schedule,
        "media_summary": {
            "photos_or_drawings_saved": len(st.session_state.photos),
            "video_events_saved": len(st.session_state.videos),
        },
        "human_support_notifications": st.session_state.staff_notifications,
        "feedback": st.session_state.feedback,
        "privacy_note": "Free text is masked for common email/phone/ID/URL patterns before analytics.",
    }


def upcoming_due_tasks():
    now = datetime.now()
    due = []
    for task in st.session_state.schedule:
        if not task.get("done"):
            try:
                task_dt = datetime.fromisoformat(task["datetime"])
                delta = (task_dt - now).total_seconds()
                if -60 <= delta <= 300:
                    due.append(task)
            except Exception:
                pass
    return due


# ---------------------------------------------------------------------------
# 8. SIDEBAR
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")
    st.selectbox(
        ui("language"),
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.language),
        key="language",
    )

    st.session_state.anonymous = st.checkbox(
        ui("anonymous"), value=st.session_state.anonymous,
        help="No name/login is required. Session data remains in this Streamlit session."
    )

    st.session_state.notification_mode = st.toggle(
        "🔔 Notification / reminder mode",
        value=st.session_state.notification_mode,
    )

    if st.session_state.paused:
        if st.button(ui("resume"), use_container_width=True):
            st.session_state.paused = False
            st.rerun()
    else:
        if st.button(ui("pause"), use_container_width=True):
            st.session_state.paused = True
            st.rerun()

    st.divider()
    st.subheader("🚨 " + ui("emergency"))
    st.caption("If there is immediate danger, use local emergency services.")
    for label, number in EMERGENCY_CONTACTS.items():
        st.markdown(f"**{label}:** [{number}](tel:{number})")

    if st.session_state.emergency_contact:
        st.markdown(
            f"**Trusted contact:** "
            f"[Call trusted contact](tel:{st.session_state.emergency_contact})"
        )

    elapsed = datetime.now() - st.session_state.session_start
    minutes = int(elapsed.total_seconds() // 60)
    st.caption(f"Session time: {minutes} min")

    if st.session_state.notification_mode and minutes >= 20 and not st.session_state.paused:
        st.warning("⏰ You have been in this session for 20+ minutes. Consider a short break.")

    due = upcoming_due_tasks()
    if st.session_state.notification_mode and due:
        st.error("🔔 Task reminder: " + ", ".join(t["task"] for t in due))


# ---------------------------------------------------------------------------
# 9. CONSENT GATE
# ---------------------------------------------------------------------------

st.title("🧠 " + ui("title"))
st.caption(ui("subtitle"))

with st.expander("🔐 Consent, Privacy & Data Control", expanded=not st.session_state.consent):
    st.write(
        "This app keeps data in Streamlit session state unless you "
        "add your own database/backend. No account is required. Anonymous mode uses "
        "a random session identifier."
    )
    st.session_state.consent = st.checkbox(
        ui("consent"), value=st.session_state.consent
    )
    st.write(
        "Data control: you can clear the current session from the Reports & Privacy tab. "
        "Avoid entering passwords, financial details or unnecessary personal identifiers."
    )

if not st.session_state.consent:
    st.info("Please provide consent to use the screening and support features.")
    st.stop()

if st.session_state.paused:
    st.warning("⏸️ Session paused. Continue from the sidebar when you are ready.")
    st.stop()


# ---------------------------------------------------------------------------
# 10. MAIN TABS
# ---------------------------------------------------------------------------

tabs = st.tabs([
    "📝 Screening",
    "💬 AI Chat",
    "🎯 Activities",
    "⏰ Schedule",
    "📷 Photo / Video",
    "🎨 Drawing",
    "🚨 Emergency",
    "👩‍⚕️ Human Support",
    "📊 Dashboard",
    "📄 Reports & Privacy",
])


# ---------------------------------------------------------------------------
# TAB 1: SCREENING
# ---------------------------------------------------------------------------

with tabs[0]:
    st.header("📝 Stress & Wellbeing Screening")

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_emotion = st.selectbox(
            stext("emotion"),
            ["Not sure", "Calm / Happy", "Anxious", "Sad", "Angry", "Fearful", "Overwhelmed"],
            key="screen_emotion",
        )
    with col2:
        emoji = st.select_slider(
            stext("emoji"),
            options=["😀", "🙂", "😐", "😟", "😣", "😫", "😨"],
            value="😐",
            key="screen_emoji",
        )
    with col3:
        stress_slider = st.slider(stext("stress"), 0, 10, 5, key="screen_stress")

    st.subheader("💬 " + ui("free_text"))
    free_text = st.text_area(ui("free_text"), height=140)

    st.subheader("🎙️ Voice input → Speech-to-text")
    audio = st.audio_input("Record your voice")
    voice_text = ""
    if audio:
        audio_bytes = audio.getvalue()
        voice_text, err = speech_to_text(audio_bytes, LANGUAGES[st.session_state.language]["stt"])
        if voice_text:
            st.success("Voice converted to text.")
            st.text_area(stext("voice"), value=voice_text, height=100, key="transcribed_voice")
        elif err:
            st.warning("Could not convert this voice recording to text.")
            with st.expander("🔍 Voice-to-text details"):
                st.write(err)
            with st.expander("🔍 Voice-to-text details"):
                st.write(err)
                st.write("Check browser microphone permission, speak clearly, reduce background noise, and make sure internet access is available.")

    st.subheader("📋 " + stext("questionnaire"))
    q1 = st.slider(stext("q1"), 0, 10, 5, key="q1")
    q2 = st.slider(stext("q2"), 0, 10, 5, key="q2")
    q3 = st.slider(stext("q3"), 0, 10, 5, key="q3")
    q4 = st.slider(stext("q4"), 0, 10, 5, key="q4")
    q5 = st.slider(stext("q5"), 0, 10, 5, key="q5")

    st.subheader("🛡️ " + stext("safety_title"))
    safety = st.radio(
        stext("safety"),
        [stext("safe"), stext("unsure"), stext("unsafe")],
        horizontal=True,
        key="safety_choice",
    )
    st.session_state.safety = safety
    fear = st.text_input(
        stext("fear"),
        value=st.session_state.get("fear", ""),
        key="fear_input",
    )
    st.session_state.fear = fear
    wellbeing = st.slider(stext("wellbeing"), 0, 10, 5, key="wellbeing")

    st.subheader("❤️ " + stext("favorite_title"))
    favorite = st.selectbox(
        stext("favorite"),
        list(ACTIVITIES.keys()),
        index=list(ACTIVITIES.keys()).index(st.session_state.favorite_activity)
        if st.session_state.favorite_activity in ACTIVITIES else 0,
    )
    st.session_state.favorite_activity = favorite

    if safety != "I feel safe":
        st.info(
            f"Your selected activity is **{favorite}**. If you are physically unsafe, "
            "please use Emergency Support first. Otherwise, a short favorite activity "
            "can be suggested as a coping break."
        )

    final_text = free_text.strip()
    if voice_text:
        final_text = (final_text + " " + voice_text).strip()

    if st.button("🔍 " + ui("analyze"), type="primary", use_container_width=True):
        questionnaire = [q1, q2, q3, q4, q5]
        analysis = calculate_risk(
            final_text,
            selected_emotion,
            stress_slider,
            questionnaire,
            safety,
            wellbeing,
        )

        st.session_state.last_analysis = analysis
        st.session_state.risk_history.append(analysis)
        st.session_state.emotion_history.append({
            "timestamp": analysis["timestamp"],
            "emotion": analysis["emotion"],
            "stress_score": analysis["stress_score"],
        })

        if analysis["risk"] in ("HIGH", "URGENT"):
            add_staff_notification("Elevated risk screening", analysis["risk"])

        if analysis["risk"] == "URGENT":
            add_staff_notification("Immediate safety signal detected", "URGENT")

        st.rerun()

    if st.session_state.last_analysis:
        a = st.session_state.last_analysis
        st.divider()
        st.subheader("📌 Screening result")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(ui("risk"), a["risk"])
        m2.metric(ui("stress"), f'{a["stress_score"]}/10')
        m3.metric(ui("confidence"), f'{int(a["confidence"] * 100)}%')
        m4.metric("Emotion", a["emotion"])

        st.write(f"**Sentiment:** {a['sentiment']}")
        st.write(f"**Distress screening score:** {a['distress_score']}/10")
        st.write(f"**Context:** {', '.join(a['context'])}")
        st.write(f"**Safety signal:** {'Detected' if a['features']['safety_flag'] else 'Not detected'}")
        st.write(f"**Input consistency:** {a['consistency']}")
        st.write(f"**Detected language:** {a['detected_language']}")
        st.write(f"**Missing input:** {', '.join(a['missing_inputs']) if a['missing_inputs'] else 'None'}")

        with st.expander("🔬 Smart preprocessing / feature engineering"):
            st.write("✓ Language detection")
            st.write("✓ Multilingual Unicode normalization")
            st.write("✓ Speech-to-text processing")
            st.write("✓ Text normalization and noise cleanup")
            st.write("✓ Context extraction")
            st.write("✓ Temporal emotional tracking")
            st.write("✓ Emotional signal extraction")
            st.write("✓ Feature engineering")
            st.write("✓ Sensitive-data masking")
            st.write("✓ Ambiguity / missing-input detection")
            st.write("✓ Input consistency checking")
            st.write("✓ Confidence estimation")
            st.write("✓ Safety signal detection")
            st.json(a["features"])

        if a["risk"] == "URGENT":
            st.error(
                "🚨 URGENT safety signal. Please contact emergency services/trusted support "
                "now. Use the Emergency tab for quick call links."
            )
        elif a["risk"] == "HIGH":
            st.warning(
                f"High stress detected. Consider a break and your favorite activity: "
                f"**{favorite}**. Human support is recommended."
            )
        elif a["risk"] == "MODERATE":
            st.info("Moderate stress detected. Try a short grounding activity and re-check later.")
        else:
            st.success("Low current stress signal. Continue healthy routines and monitor changes.")


# ---------------------------------------------------------------------------
# TAB 2: AI CHAT
# ---------------------------------------------------------------------------

with tabs[1]:
    st.header("💬 " + ui("chat"))
    st.caption("Type a message or record a voice message. A recording is NOT sent automatically.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.subheader("🎙️ Voice message")
    chat_audio = st.audio_input("Record your message")

    if chat_audio:
        import hashlib as _hashlib
        audio_bytes = chat_audio.getvalue()
        audio_hash = _hashlib.sha256(audio_bytes).hexdigest()

        if audio_hash != st.session_state.get("chat_audio_hash", ""):
            voice_text, err = speech_to_text(
                audio_bytes, LANGUAGES[st.session_state.language]["stt"]
            )
            st.session_state.chat_audio_hash = audio_hash
            st.session_state.pending_chat_voice = voice_text or ""
            st.session_state.chat_voice_error = err or ""

    chat_voice_text = st.session_state.get("pending_chat_voice", "")
    chat_voice_error = st.session_state.get("chat_voice_error", "")

    if chat_voice_text:
        st.success("Voice converted to text. Press Send voice message to send it.")
        st.text_area(
            "Transcribed voice message",
            value=chat_voice_text,
            height=90,
            key="chat_voice_preview",
        )

        vc1, vc2 = st.columns(2)
        with vc1:
            send_voice = st.button("📤 Send voice message", type="primary", use_container_width=True)
        with vc2:
            clear_voice = st.button("🗑️ Clear voice message", use_container_width=True)

        if clear_voice:
            st.session_state.pending_chat_voice = ""
            st.session_state.chat_voice_error = ""
            st.session_state.chat_audio_hash = ""
            st.rerun()

        if send_voice:
            prompt = chat_voice_text.strip()
            if prompt:
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                response = support_response(prompt, st.session_state.last_analysis)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.pending_chat_voice = ""
                st.session_state.chat_voice_error = ""
                # Keep the hash so the same recording cannot be auto-sent on rerun.
                st.rerun()

    elif chat_voice_error:
        st.warning("Could not convert this voice recording to text.")
        with st.expander("🔍 Voice-to-text details"):
            st.write(chat_voice_error)

    st.subheader("⌨️ Text message")
    prompt = st.chat_input("Type your message here…")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        response = support_response(prompt, st.session_state.last_analysis)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    if st.session_state.chat_history:
        latest_ai = next(
            (m["content"] for m in reversed(st.session_state.chat_history)
             if m["role"] == "assistant"),
            None,
        )
        if latest_ai:
            st.subheader("🔊 AI voice response")
            if st.button("🔊 Speak latest AI response", use_container_width=True):
                speak_text(latest_ai, st.session_state.language)

    st.caption(
        "The chatbot provides supportive conversation and navigation, not diagnosis. "
        "If you are in immediate danger, use Emergency Support."
    )


# TAB 3: ACTIVITIES
# ---------------------------------------------------------------------------

with tabs[2]:
    st.header("🎯 " + ui("activities"))

    a = st.session_state.last_analysis or {}
    recommended = st.session_state.favorite_activity

    if a.get("risk") in ("HIGH", "URGENT") or st.session_state.safety != "I feel safe":
        st.warning(
            f"Personalized recommendation: **{recommended}**. "
            "Choose an activity you genuinely enjoy; emergency safety comes first."
        )

    activity = st.selectbox(
        "Choose your interest/domain",
        list(ACTIVITIES.keys()),
        index=list(ACTIVITIES.keys()).index(recommended)
        if recommended in ACTIVITIES else 0,
    )
    st.session_state.favorite_activity = activity

    st.write(ACTIVITIES[activity]["description"])
    if activity == "Music":
        st.info("🎵 StressCare Music — search and listen using a full online music catalog. Songs are provided by the music service rather than YouTube.")
        music_query = st.text_input(
            "🔎 Search songs, artists, albums or playlists",
            placeholder="Example: A.R. Rahman, Tamil melodies, lo-fi, Ilaiyaraaja...",
            key="music_search_query",
        )
        if music_query.strip():
            from urllib.parse import quote_plus
            spotify_search = f"https://open.spotify.com/search/{quote_plus(music_query.strip())}"
            st.markdown(f"### 🎧 Music results for **{music_query.strip()}**")
            st.markdown(f"[▶️ Open and play in Spotify Web Player]({spotify_search})")
            st.components.v1.iframe(spotify_search, height=520, scrolling=True)
        else:
            st.markdown("[🎧 Open Spotify Web Player](https://open.spotify.com/search)")
            st.caption("Search any song, artist, album, playlist or mood in the music app.")
    else:
        st.markdown(f"▶️ [Open personalized YouTube videos for {activity}]({youtube_search(activity)})")

    st.subheader("🎮 Games")
    st.write("Choose a game category instead of forcing one activity such as cooking.")
    game_cols = st.columns(4)
    for i, (name, link) in enumerate(GAME_LINKS.items()):
        with game_cols[i % 4]:
            st.markdown(f"[🎮 {name}]({link})")

    st.subheader("🎨 Drawing")
    st.write("Use the Drawing tab for a Windows-Paint-like freehand canvas.")

    st.subheader("💃 Dance")
    st.markdown("[💃 Open dance videos](https://www.youtube.com/results?search_query=beginner+dance+routine)")

    # Music is handled above as a dedicated online music-app experience.


    st.subheader("🧘 Grounding")
    st.write("Try: inhale slowly → hold briefly → exhale slowly → repeat several times.")

    st.subheader("⏸️ AI support resistance / pause")
    st.session_state.support_resistance = st.toggle(
        "Pause personalized AI suggestions",
        value=st.session_state.support_resistance,
    )
    if st.session_state.support_resistance:
        st.info("AI suggestions are paused. You can still use manual activities and emergency support.")


# ---------------------------------------------------------------------------
# TAB 4: SCHEDULE
# ---------------------------------------------------------------------------

with tabs[3]:
    st.header("⏰ " + ui("schedule"))
    st.write(
        "Create tasks for a client/patient, such as 'Take a 5-minute break' at a chosen time. "
        "This demo provides in-app reminders while the Streamlit session is open."
    )

    c1, c2 = st.columns(2)
    with c1:
        task = st.text_input("Task / instruction", placeholder="Do breathing exercise")
        task_date = st.date_input("Date", value=datetime.now().date())
    with c2:
        task_time = st.time_input("Time", value=(datetime.now() + timedelta(minutes=5)).time())
        priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])

    repeat = st.selectbox("Repeat", ["Once", "Daily", "Weekly"])
    if st.button("➕ Schedule task", use_container_width=True):
        if not task.strip():
            st.warning("Please enter a task/instruction before scheduling.")
        else:
            dt = datetime.combine(task_date, task_time)
            st.session_state.schedule.append({
                "id": hashlib.md5(os.urandom(8)).hexdigest()[:8],
                "task": task.strip(),
                "datetime": dt.isoformat(timespec="minutes"),
                "priority": priority,
                "repeat": repeat,
                "done": False,
                "created": datetime.now().isoformat(timespec="seconds"),
            })
            st.success("Task scheduled.")

    st.subheader("📋 Scheduled tasks")
    if st.session_state.schedule:
        for idx, item in enumerate(st.session_state.schedule):
            cols = st.columns([4, 2, 1, 1])
            cols[0].write(f"**{item['task']}**")
            cols[1].write(item["datetime"].replace("T", " "))
            cols[2].write(item["priority"])
            if cols[3].button("Done", key=f"done_{item['id']}"):
                st.session_state.schedule[idx]["done"] = True
                st.rerun()
    else:
        st.info("No tasks scheduled.")

    st.info(
        "Deployment note: true background push/SMS notifications require a "
        "notification service or native/mobile integration. This Streamlit version shows "
        "in-app reminders when the session is active."
    )


# ---------------------------------------------------------------------------
# TAB 5: PHOTO / VIDEO
# ---------------------------------------------------------------------------

with tabs[4]:
    st.header("📷 " + ui("media"))

    st.subheader("📸 Take a photo now")
    camera_photo = st.camera_input("Take a photo")
    if camera_photo:
        st.image(camera_photo, caption="Captured now")
        if st.button("Save captured photo to session"):
            st.session_state.photos.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "source": "camera",
            })
            st.success("Photo stored only in the current Streamlit session.")

    st.subheader("📤 Upload an extra photo")
    uploaded_photos = st.file_uploader(
        "Upload photo(s)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    if uploaded_photos:
        for photo in uploaded_photos:
            st.image(photo, caption=photo.name, width=250)
        if st.button("Save uploaded photos to session"):
            for photo in uploaded_photos:
                st.session_state.photos.append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "source": "upload",
                    "name": photo.name,
                })
            st.success("Uploaded photos stored in the current session.")

    st.subheader("🎥 Video input")
    video = st.file_uploader("Upload a short video", type=["mp4", "mov", "webm"])
    if video:
        st.video(video)
        if st.button("Save video event"):
            st.session_state.videos.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "name": video.name,
            })

    st.subheader("📹 Video-call prototype")
    if webrtc_streamer is not None:
        st.write("This enables browser camera/microphone streaming in the current app session.")
        webrtc_streamer(
            key="stresscare_video_room",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": True, "audio": True},
        )
        st.caption(
            "A real patient↔staff remote call requires a signaling/room service and usually "
            "TURN infrastructure. This component is the browser-streaming prototype."
        )
    else:
        st.warning(
            "Install streamlit-webrtc to enable the browser video/audio prototype."
        )

    st.subheader("🔗 Staff meeting URL")
    meeting = st.text_input(
        "Paste your approved video-call room URL (optional)",
        value=st.session_state.meeting_url,
        placeholder="https://…",
    )
    st.session_state.meeting_url = meeting
    if meeting:
        st.markdown(f"[Open staff video meeting]({meeting})")


# ---------------------------------------------------------------------------
# TAB 6: DRAWING
# ---------------------------------------------------------------------------

with tabs[5]:
    st.header("🎨 " + ui("draw"))
    st.write("Freehand canvas designed to feel similar to a simple Windows Paint drawing area.")

    if st_canvas is not None:
        stroke_width = st.slider("Brush size", 1, 30, 4)
        bg = st.color_picker("Background", "#FFFFFF")
        drawing = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=stroke_width,
            stroke_color="#000000",
            background_color=bg,
            height=500,
            width=900,
            drawing_mode="freedraw",
            key="paint_canvas",
            return_image_data=True,
        )
        if drawing.image_data is not None:
            st.caption("Use the canvas above to draw freely.")
            if st.button("💾 Save drawing to this session"):
                st.session_state.photos.append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "source": "drawing",
                })
                st.success("Drawing saved to the current session.")
    else:
        st.warning("Install streamlit-drawable-canvas for the built-in Paint-like canvas.")
        st.markdown("[Open JS Paint in a new tab](https://jspaint.app/)")


# ---------------------------------------------------------------------------
# TAB 7: EMERGENCY
# ---------------------------------------------------------------------------

with tabs[6]:
    st.header("🚨 Immediate Support")

    st.error(
        "If you are in immediate danger, contact emergency services now. "
        "Do not wait for the AI screening result."
    )

    for label, number in EMERGENCY_CONTACTS.items():
        st.markdown(f"### {label}")
        st.markdown(f"**[{number} — Call](tel:{number})**")

    st.subheader("📞 Local trusted / emergency contact")
    st.session_state.emergency_contact = st.text_input(
        "Trusted contact phone number",
        value=st.session_state.emergency_contact,
        placeholder="+91 …",
    )
    if st.session_state.emergency_contact:
        st.markdown(
            f"### [📞 Call trusted contact](tel:{st.session_state.emergency_contact})"
        )

    st.subheader("🧘 While getting help")
    st.write(
        "Move to a safer place if possible, stay with a trusted person, and use slow "
        "breathing while you wait for support."
    )

    st.caption(
        "For a production app, verify emergency resources for the user's actual country/state "
        "and provide a location-aware directory."
    )


# ---------------------------------------------------------------------------
# TAB 8: HUMAN IN THE LOOP
# ---------------------------------------------------------------------------

with tabs[7]:
    st.header("👩‍⚕️ " + ui("human"))

    st.write(
        "Human-in-the-loop features: staff notification, case review and support referral."
    )

    reason = st.text_area(
        "Why would you like human support?",
        placeholder="I would like to talk to a counselor/support person.",
    )
    if st.button("🙋 Request human support", use_container_width=True):
        add_staff_notification(reason or "User requested human support",
                               (st.session_state.last_analysis or {}).get("risk", ""))
        st.success("Support request added to the staff review queue.")

    st.subheader("📬 Staff notification queue")
    if st.session_state.staff_notifications:
        for i, note in enumerate(st.session_state.staff_notifications):
            with st.expander(
                f"{note['time']} | {note['risk'] or 'INFO'} | "
                f"{'Reviewed' if note['reviewed'] else 'Needs review'}"
            ):
                st.write(note["reason"])
                if not note["reviewed"]:
                    if st.button("Mark as reviewed", key=f"review_{i}"):
                        st.session_state.staff_notifications[i]["reviewed"] = True
                        st.rerun()
    else:
        st.info("No staff notifications yet.")

    st.subheader("🤝 Support referral")
    st.write(
        "For a real deployment, connect this queue to an authenticated counselor/staff "
        "dashboard, case-management system, secure audit log and approved notification channel."
    )


# ---------------------------------------------------------------------------
# TAB 9: DASHBOARD
# ---------------------------------------------------------------------------

with tabs[8]:
    st.header("📊 " + ui("dashboard"))

    history = st.session_state.risk_history

    if not history:
        st.info("Complete at least one screening to populate the dashboard.")
    else:
        df = pd.DataFrame(history)
        latest = history[-1]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Screenings", len(history))
        m2.metric("Latest risk", latest["risk"])
        m3.metric("Average stress", f"{df['stress_score'].mean():.1f}/10")
        m4.metric("Latest confidence", f"{latest['confidence'] * 100:.0f}%")

        st.subheader("📈 Risk / stress history")
        chart_df = df[["timestamp", "stress_score"]].copy()
        chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
        if px:
            fig = px.line(
                chart_df,
                x="timestamp",
                y="stress_score",
                markers=True,
                title="Stress score over time",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(chart_df.set_index("timestamp")["stress_score"])

        st.subheader("😊 Emotion trends")
        edf = pd.DataFrame(st.session_state.emotion_history)
        if not edf.empty:
            counts = edf["emotion"].value_counts().reset_index()
            counts.columns = ["emotion", "count"]
            if px:
                fig2 = px.bar(counts, x="emotion", y="count", title="Emotion frequency")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.bar_chart(counts.set_index("emotion"))

        st.subheader("📋 Analytics")
        analytics = df[[
            "timestamp", "risk", "stress_score", "distress_score",
            "emotion", "sentiment", "confidence", "consistency",
            "detected_language"
        ]]
        st.dataframe(analytics, use_container_width=True)


# ---------------------------------------------------------------------------
# TAB 10: REPORTS / PRIVACY
# ---------------------------------------------------------------------------

with tabs[9]:
    st.header("📄 " + ui("reports"))

    report = build_report()
    report_json = json.dumps(report, ensure_ascii=False, indent=2, default=str)

    st.download_button(
        "⬇️ Download screening report (JSON)",
        data=report_json,
        file_name=f"stresscare_report_{st.session_state.session_id}.json",
        mime="application/json",
        use_container_width=True,
    )

    if st.session_state.risk_history:
        csv_df = pd.DataFrame(st.session_state.risk_history)
        st.download_button(
            "⬇️ Download risk history (CSV)",
            data=csv_df.to_csv(index=False).encode("utf-8"),
            file_name="stresscare_risk_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

        latest = st.session_state.risk_history[-1]
        screening_text = f"""
STRESSCARE AI - SCREENING REPORT
Generated: {datetime.now().isoformat(timespec='seconds')}
Risk: {latest['risk']}
Stress score: {latest['stress_score']}/10
Distress score: {latest['distress_score']}/10
Emotion: {latest['emotion']}
Sentiment: {latest['sentiment']}
Confidence: {latest['confidence'] * 100:.0f}%
Context: {', '.join(latest['context'])}
Input consistency: {latest['consistency']}
Detected language: {latest['detected_language']}
Safety signal: {'Detected' if latest['features']['safety_flag'] else 'Not detected'}

NOTE:
This is a wellness-support tool and not a medical diagnosis.
"""
        st.download_button(
            "⬇️ Download human-readable screening report (TXT)",
            data=screening_text.strip(),
            file_name="stresscare_screening_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.subheader("✏️ Correction / feedback")
    feedback_text = st.text_area(
        "Tell us what was incorrect or what should be improved."
    )
    rating = st.slider("App/support rating", 1, 5, 4)
    if st.button("Submit feedback"):
        st.session_state.feedback.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "rating": rating,
            "text": feedback_text,
        })
        st.success("Feedback recorded for this session.")

    st.subheader("🗑️ Data control")
    st.write(
        "This app uses Streamlit session state and does not require a database. "
        "The controls below clear data from the current session."
    )
    if st.button("Delete current session data", type="secondary"):
        # Keep only the minimum app settings required to continue.
        keep = {
            "language": st.session_state.language,
            "anonymous": st.session_state.anonymous,
            "consent": st.session_state.consent,
        }
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        for key, value in keep.items():
            st.session_state[key] = value
        init_state()
        st.success("Current session data cleared.")
        st.rerun()

    st.subheader("🔒 Privacy checklist")
    st.write("✓ Anonymous session option")
    st.write("✓ No login/name required")
    st.write("✓ Sensitive pattern masking before NLP analytics")
    st.write("✓ Session-only storage by default")
    st.write("✓ Downloadable report")
    st.write("✓ User correction/feedback")
    st.write("✓ User-controlled AI suggestion pause")
    st.write("✓ Emergency support separated from AI diagnosis")


# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "StressCare AI • Wellness support only • "
    "For production: secure backend, authentication/roles, encrypted storage, "
    "audit logging, validated clinical workflows, verified local emergency resources, "
    "real push notifications and secure video-call infrastructure are required."
)
