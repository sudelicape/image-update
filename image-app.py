import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import io
import time

# --- Şifre Kontrol ---
password = st.text_input("Şifre giriniz:", type="password")

if password != st.secrets["APP_PASSWORD"]:
    st.error("Geçersiz şifre!")
    st.stop()

# --- App Başlık ---
st.title("🛍️ Trendyol Ürün Güncelleme Paneli")

# --- Sayfa Seçimi ---
st.sidebar.header("📂 Sayfa Menüsü")
page = st.sidebar.radio(
    "Sayfa Seçiniz:",
    ("Görsel Güncelleme", "Termin Süresi Güncelleme")
)

# --- Ortak Bilgiler ---
api_key = st.secrets["API_KEY"]
api_secret = st.secrets["API_SECRET"]
supplierid = st.secrets["SUPPLIER_ID"]

# --- Görsel Güncelleme Bölümü ---
if page == "Görsel Güncelleme":
    st.header("🖼️ Görsel Güncelleme")

    kampanya = st.radio(
        "Kampanya Seçiniz:",
        ('2.si 1 TL', '2.si 1 TL - Sarı Tonik Tester', '2.si 1 TL - Çok Yönlü Tester')
    )

    confirm = st.checkbox("Emin misiniz? Güncellemeyi başlatmak istediğinize emin olun.")

    if st.button("🔄 Görsel Güncellemeyi Başlat"):
        if not confirm:
            st.warning("⚠️ Lütfen önce 'Emin misiniz?' kutusunu işaretleyin.")
            st.stop()

        st.write(f"Seçilen kampanya: **{kampanya}**")

        # --- Excel Dosyasını Yükle ---
        excel_url = st.secrets["EXCEL_URL"]
        response = requests.get(excel_url)
        excel_bytes = io.BytesIO(response.content)

        sheet_mapping = {
            '2.si 1 TL': st.secrets["EXCEL_SHEET_1"],
            '2.si 1 TL - Sarı Tonik Tester': st.secrets["EXCEL_SHEET_2"],
            '2.si 1 TL - Çok Yönlü Tester': st.secrets["EXCEL_SHEET_3"]
        }

        df_kampanya = pd.read_excel(excel_bytes, sheet_name=sheet_mapping[kampanya])

        # --- Ürünleri Çek ---
        page_num = 0
        page_size = 100
        all_products = []

        st.write("📡 Trendyol ürünleri çekiliyor...")

        while True:
            url = f"https://apigw.trendyol.com/integrati


