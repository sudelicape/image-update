import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import io

# --- Şifre Kontrol ---
password = st.text_input("Şifre giriniz:", type="password")

if password != st.secrets["APP_PASSWORD"]:
    st.error("Geçersiz şifre!")
    st.stop()

# --- App Başlık ---
st.title("🛍️ Trendyol Görsel Güncelleme Paneli")

# Kampanya Seçimi
kampanya = st.radio(
    "Kampanya Seçiniz:",
    ('kampanya1', 'kampanya1-sarı-tonik', 'kampanya1-cok-yonlu')
)

if st.button("🔄 Güncellemeyi Başlat"):
    st.write(f"Seçilen kampanya: **{kampanya}**")
    
    # --- Excel Dosyasını Yükle ---
    excel_url = st.secrets["EXCEL_URL"]
    
    response = requests.get(excel_url)
    excel_bytes = io.BytesIO(response.content)
    
    # --- Sheet seçimi ---
    sheet_mapping = {
        'kampanya1': st.secrets["EXCEL_SHEET_1"],
        'kampanya1-sarı-tonik': st.secrets["EXCEL_SHEET_2"],
        'kampanya1-cok-yonlu': st.secrets["EXCEL_SHEET_3"]
    }
    
    df_kampanya = pd.read_excel(excel_bytes, sheet_name=sheet_mapping[kampanya])
    
    # --- Trendyol API bilgileri ---
    api_key = st.secrets["API_KEY"]
    api_secret = st.secrets["API_SECRET"]
    supplierid = st.secrets["SUPPLIER_ID"]
    
    # --- Ürünleri Çek ---
    page_num = 0
    page_size = 100
    all_products = []
    
    st.write("📡 Trendyol ürünleri çekiliyor...")
    
    while True:
        url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products?page={page_num}&size={page_size}"
        response = requests.get(url, auth=HTTPBasicAuth(api_key, api_secret))
        
        if response.status_code != 200:
            st.error(f"Request failed at page {page_num}: {response.status_code}")
            st.error(response.text)
            break
        
        data = response.json()
        products = data.get('content', [])
        
        if not products:
            break
        
        all_products.extend(products)
        
        total_pages = data.get('totalPages')
        st.write(f"Fetched page {page_num + 1} / {total_pages}")
        
        if page_num + 1 >= total_pages:
            break
        
        page_num += 1
    
    st.write(f"✅ Toplam ürün çekildi: {len(all_products)}")
    
    # --- Update Payload ---
    update_payload = []
    updated_count = 0
    
    for product in all_products:
        barcode = product['barcode']
        
        match = df_kampanya[df_kampanya['Barkod'] == barcode]
        
        if not match.empty:
            new_image_url = match.iloc[0]['link']
            
            original_images = product.get('images', [])
            
            new_images_list = [{"url": new_image_url}]
            
            if len(original_images) > 1:
                new_images_list.extend(original_images[1:])
            
            update_payload.append({
                "barcode": barcode,
                "title": product['title'],
                "productMainId": product['productMainId'],
                "brandId": product['brandId'],
                "categoryId": product.get('categoryId', 0),
                "stockCode": product['stockCode'],
                "dimensionalWeight": product.get('dimensionalWeight', 0),
                "description": product['description'],
                "currencyType": "TRY",
                "cargoCompanyId": product.get('cargoCompanyId', 0),
                "vatRate": product['vatRate'],
                "images": new_images_list,
                "attributes": product['attributes']
            })
            
            updated_count += 1
            st.write(f"[OK] Güncellenecek ürün: {barcode} → yeni görsel: {new_image_url}")
    
    st.write(f"\n📝 Güncellenecek toplam ürün sayısı: {updated_count}")
    
    # --- PUT Update ---
    if update_payload:
        update_url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products"
        body = {"items": update_payload}
        
        st.write("🚀 Güncellemeler gönderiliyor...")
        
        put_response = requests.put(update_url, auth=HTTPBasicAuth(api_key, api_secret), json=body)
        
        if put_response.status_code == 200:
            st.success("✅ Update başarılı!")
        else:
            st.error(f"❌ Update hatası: {put_response.status_code}")
            st.error(put_response.text)
    else:
        st.warning("⚠️ Güncellenecek ürün bulunamadı.")
