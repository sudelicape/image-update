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
        ('2.si 1 TL', '2.si 1 TL - Sarı Tonik Tester', '2.si 1 TL - Çok Yönlü Tester', '3 Al 1 Öde', '3 Al 1 Öde - Sarı Tonik Tester', '3 Al 1 Öde - Çok Yönlü Tester'  )
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
            '2.si 1 TL - Çok Yönlü Tester': st.secrets["EXCEL_SHEET_3"], 
            '3 Al 1 Öde': st.secrets["EXCEL_SHEET_4"],
            '3 Al 1 Öde - Sarı Tonik Tester': st.secrets["EXCEL_SHEET_5"],
            '3 Al 1 Öde - Çok Yönlü Tester': st.secrets["EXCEL_SHEET_6"]
        }

        df_kampanya = pd.read_excel(excel_bytes, sheet_name=sheet_mapping[kampanya])

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

# --- Termin Süresi Güncelleme Bölümü ---
elif page == "Termin Süresi Güncelleme":
    st.header("⏳ Termin Süresi Güncelleme")

    delivery_duration_choice = st.radio(
        "Termin Süresini Seçiniz:",
        (1, 2)
    )

    confirm = st.checkbox("Emin misiniz? Güncellemeyi başlatmak istediğinize emin olun.")

    if st.button("🔄 Termin Süresi Güncellemeyi Başlat"):
        if not confirm:
            st.warning("⚠️ Lütfen önce 'Emin misiniz?' kutusunu işaretleyin.")
            st.stop()

        st.write(f"Seçilen termin süresi: **{delivery_duration_choice}** gün")

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
            update_payload.append({
                "barcode": product['barcode'],
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
                "deliveryDuration": delivery_duration_choice,
                "images": product.get('images', []),
                "attributes": product['attributes']
            })

            updated_count += 1
            st.write(f"[OK] Güncellenecek ürün: {product['barcode']} → deliveryDuration: {delivery_duration_choice}")

        st.write(f"\n📝 Güncellenecek toplam ürün sayısı: {updated_count}")

        # --- PUT Update ---
        if update_payload:
            update_url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products"
            body = {"items": update_payload}

            st.write("🚀 Güncellemeler gönderiliyor...")

            put_response = requests.put(update_url, auth=HTTPBasicAuth(api_key, api_secret), json=body)

            if put_response.status_code == 200:
                response_json = put_response.json()
                batch_request_id = response_json.get('batchRequestId')
                st.success("✅ Update başarılı!")
                if batch_request_id:
                    st.info(f"BatchRequestId: {batch_request_id}")

                    st.write("⏳ Batch sonucu sorgulanıyor, lütfen bekleyin...")
                    time.sleep(10)

                    check_url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products/batch-requests/{batch_request_id}"
                    check_response = requests.get(check_url, auth=HTTPBasicAuth(api_key, api_secret))

                    if check_response.status_code == 200:
                        data = check_response.json()

                        st.write(f"BatchRequestId: {data['batchRequestId']}")
                        st.write(f"Toplam item: {data['itemCount']}")
                        st.write(f"Başarısız item: {data['failedItemCount']}")
                        st.write(f"Genel status: {data['status']}")

                        for item in data['items']:
                            barcode = item['requestItem']['barcode']
                            item_status = item['status']
                            failure_reasons = item.get('failureReasons', [])

                            st.write(f"- {barcode}: {item_status}")
                            if failure_reasons:
                                st.write(f"  🚫 FailureReasons: {failure_reasons}")
                    else:
                        st.error(f"❌ Batch sorgulama hatası: {check_response.status_code}")
                        st.error(check_response.text)
                else:
                    st.warning("⚠️ BatchRequestId dönmedi!")
            else:
                st.error(f"❌ Update hatası: {put_response.status_code}")
                st.error(put_response.text)
        else:
            st.warning("⚠️ Güncellenecek ürün bulunamadı.")


