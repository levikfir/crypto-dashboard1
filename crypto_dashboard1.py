import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from plyer import notification
import time
from twilio.rest import Client
import os

# התקנת הספריות החסרות
try:
    import plotly.express as px
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "plotly"])
    import plotly.express as px

try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "openpyxl"])
    import openpyxl

# פונקציה לקבלת מחירי מטבעות בזמן אמת
API_URL = "https://api.coingecko.com/api/v3/simple/price"
def get_crypto_price(symbol, currency="usd"):
    try:
        response = requests.get(API_URL, params={"ids": symbol, "vs_currencies": currency})
        data = response.json()
        return data.get(symbol, {}).get(currency, None)
    except Exception as e:
        st.error(f"שגיאה בשליפת מחירי מטבעות: {e}")
        return None

# בדיקה אם קובץ הנתונים קיים
file_path = "/mnt/data/INVEST GPT 2.xlsx"
sheet_name = "חישובים"

if not os.path.exists(file_path):
    st.error(f"❌ קובץ הנתונים לא נמצא: {file_path}. ודא שהעלית את הקובץ ל-Streamlit Cloud או שהנתיב נכון.")
    st.stop()

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
except Exception as e:
    st.error(f"❌ שגיאה בטעינת קובץ ה-Excel: {e}")
    st.stop()

# המרת עמודות מספריות למספרים, והתעלמות משגיאות
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# הגדרת מבנה הדאשבורד
st.set_page_config(page_title="Crypto Dashboard", layout="wide")
st.title("📊 Crypto Investment Dashboard")

# בחירת מטבע לתצוגה
coin_options = df.iloc[1:, 0].dropna().unique()
selected_coin = st.selectbox("בחר מטבע:", coin_options)

# סינון הנתונים לפי המטבע הנבחר
coin_data = df[df.iloc[:, 0] == selected_coin]

# קבלת מחיר השוק בזמן אמת
current_market_price = get_crypto_price(selected_coin.lower())
if current_market_price is not None:
    st.metric(label="💲 מחיר שוק בזמן אמת (USD)", value=f"${current_market_price:,.2f}")

# הצגת נתונים מרכזיים עם המרת ערכים למספרים
investment_total = float(coin_data.iloc[0, 1]) if not pd.isna(coin_data.iloc[0, 1]) else 0
investment_percentage = float(coin_data.iloc[0, 2]) * 100 if not pd.isna(coin_data.iloc[0, 2]) else 0
avg_buy_price = float(coin_data.iloc[0, 4]) if not pd.isna(coin_data.iloc[0, 4]) else 0

st.metric(label="💰 סך ההשקעה (USD)", value=f"${investment_total:,.2f}")
st.metric(label="📈 אחוז מסך ההשקעה", value=f"{investment_percentage:.2f}%")
st.metric(label="🔢 ממוצע מחיר קנייה", value=f"${avg_buy_price:,.4f}")

# גרף התפלגות השקעות
fig = px.pie(df.iloc[1:], names=df.columns[0], values=df.iloc[:, 1], title="התפלגות השקעות")
st.plotly_chart(fig, use_container_width=True)

# הצגת טבלת נתונים
st.dataframe(df.iloc[1:], use_container_width=True)

# פונקציה לשליחת התראות
def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="Crypto Dashboard",
        timeout=5
    )

# פונקציה לשליחת הודעה ב-WhatsApp
def send_whatsapp_message(message):
    account_sid = "your_twilio_account_sid"
    auth_token = "your_twilio_auth_token"
    client = Client(account_sid, auth_token)
    
    client.messages.create(
        body=message,
        from_="whatsapp:+14155238886",  # מספר ה-WhatsApp של Twilio
        to="whatsapp:+YourPhoneNumber"  # מספר ה-WhatsApp שלך
    )

# מחיר יעד למטבע (מתוך הגיליון, אם קיים)
if "Target Price" in df.columns:
    target_price = float(coin_data.iloc[0, df.columns.get_loc("Target Price")]) if not pd.isna(coin_data.iloc[0, df.columns.get_loc("Target Price")]) else None
else:
    target_price = None

# מעקב אחר הגעה ליעד
if current_market_price and target_price and current_market_price >= target_price * 0.9 and current_market_price < target_price:
    alert_message = f"📢 קרוב למחיר היעד! ההשקעה ב-{selected_coin} במרחק 10% ממחיר היעד!"
    send_notification("📢 קרוב ליעד!", alert_message)
    send_whatsapp_message(alert_message)

st.session_state.previous_value = current_market_price
