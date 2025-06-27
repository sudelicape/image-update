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
    ("Görsel Güncelleme", "Termin Süresi Güncelleme", "2 Adet Siparişleri Listele")
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
        ('2.si 1 TL', '2.si 1 TL - Sarı Tonik Tester', '2.si 1 TL - Çok Yönlü Tester', '3 Al 1 Öde', '3 Al 1 Öde - Sarı Tonik Tester', '3 Al 1 Öde - Çok Yönlü Tester', '3 Al 2 Öde', '4 Al 2 Öde'  )
    )

    confirm = st.checkbox("Güncellemeyi başlatmak istediğinize emin olun.")

    if st.button("🔄 Görsel Güncellemeyi Başlat"):
        if not confirm:
            st.warning("⚠️ Lütfen önce 'Güncellemeyi başlatmak istediğinize emin olun.' kutusunu işaretleyin.")
            st.stop()

        st.write(f"Seçilen kampanya: **{kampanya}**")

        excel_url = st.secrets["EXCEL_URL"]
        response = requests.get(excel_url)
        excel_bytes = io.BytesIO(response.content)

        sheet_mapping = {
            '2.si 1 TL': st.secrets["EXCEL_SHEET_1"],
            '2.si 1 TL - Sarı Tonik Tester': st.secrets["EXCEL_SHEET_2"],
            '2.si 1 TL - Çok Yönlü Tester': st.secrets["EXCEL_SHEET_3"], 
            '3 Al 1 Öde': st.secrets["EXCEL_SHEET_4"],
            '3 Al 1 Öde - Sarı Tonik Tester': st.secrets["EXCEL_SHEET_5"],
            '3 Al 1 Öde - Çok Yönlü Tester': st.secrets["EXCEL_SHEET_6"],
            '3 Al 2 Öde': st.secrets["EXCEL_SHEET_7"],
            '4 Al 2 Öde': st.secrets["EXCEL_SHEET_8"]
        }

        df_kampanya = pd.read_excel(excel_bytes, sheet_name=sheet_mapping[kampanya])

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
            if page_num + 1 >= total_pages:
                break

            page_num += 1

        st.write(f"✅ Toplam {len(all_products)} ürün çekildi.")

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

        if updated_count > 0:
            st.write(f"📝 {updated_count} ürün güncellemeye hazırlanıyor...")
            st.write("🚀 Güncellemeler gönderiliyor...")

            update_url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products"
            put_response = requests.put(update_url, auth=HTTPBasicAuth(api_key, api_secret), json={"items": update_payload})

            if put_response.status_code == 200:
                st.success("✅ Tüm ürünler başarıyla güncellendi!")
            else:
                st.error(f"❌ Güncelleme sırasında hata oluştu! Status code: {put_response.status_code}")
                st.error(put_response.text)
        else:
            st.warning("⚠️ Bu kampanya için güncellenecek ürün bulunamadı.")

# --- Termin Süresi Güncelleme Bölümü ---
elif page == "Termin Süresi Güncelleme":
    st.header("⏳ Termin Süresi Güncelleme")

    delivery_duration_choice = st.radio(
        "Termin Süresini Seçiniz:",
        (1, 2)
    )

    confirm = st.checkbox("Güncellemeyi başlatmak istediğinize emin olun.")

    if st.button("🔄 Termin Süresi Güncellemeyi Başlat"):
        if not confirm:
            st.warning("⚠️ Lütfen önce 'Güncellemeyi başlatmak istediğinize emin olun.' kutusunu işaretleyin.")
            st.stop()

        st.write(f"Seçilen termin süresi: **{delivery_duration_choice}** gün")

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
            if page_num + 1 >= total_pages:
                break

            page_num += 1

        st.write(f"✅ Toplam {len(all_products)} ürün çekildi.")

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

        if updated_count > 0:
            st.write(f"📝 {updated_count} ürün güncellemeye hazırlanıyor...")
            st.write("🚀 Güncellemeler gönderiliyor...")

            update_url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products"
            put_response = requests.put(update_url, auth=HTTPBasicAuth(api_key, api_secret), json={"items": update_payload})

            if put_response.status_code == 200:
                response_json = put_response.json()
                batch_request_id = response_json.get('batchRequestId')
                st.success("✅ Termin süresi güncellemesi başarılı!")

                if batch_request_id:
                    st.info(f"Batch ID: {batch_request_id}")

                    check_url = f"https://apigw.trendyol.com/integration/product/sellers/{supplierid}/products/batch-requests/{batch_request_id}"

                    while True:
                        check_response = requests.get(check_url, auth=HTTPBasicAuth(api_key, api_secret))
                        if check_response.status_code != 200:
                            st.error(f"❌ Batch sorgulama hatası: {check_response.status_code}")
                            st.error(check_response.text)
                            break

                        data = check_response.json()
                        st.write(f"Batch ID: {data['batchRequestId']}")
                        st.write(f"Toplam ürün: {data['itemCount']}")
                        st.write(f"Başarısız ürün: {data['failedItemCount']}")
                        st.write(f"Durum: {data['status']}")

                        if data['status'] == "COMPLETED":
                            for item in data['items']:
                                if item['status'] != "APPROVED":
                                    barcode = item['requestItem']['barcode']
                                    failure_reasons = item.get('failureReasons', [])
                                    if failure_reasons:  # Eğer boş değilse
                                        st.write(f"🚫 {barcode}: {failure_reasons}")

                            break
                        else:
                            st.write("⏳ Batch işlemi devam ediyor, 5 sn bekleniyor...")
                            time.sleep(5)
                else:
                    st.warning("⚠️ Batch ID alınamadı!")
            else:
                st.error(f"❌ Güncelleme sırasında hata oluştu! Status code: {put_response.status_code}")
                st.error(put_response.text)
        else:
            st.warning("⚠️ Güncellenecek ürün bulunamadı.")
# --- 2 Adet Siparişleri Listele Bölümü ---
elif page == "2 Adet Siparişleri Listele":
    st.header("📦 2 Adet Siparişleri Listeleme")

    trendyol_filter = st.radio(
        "Trendyol Express dahil olsun mu?",
        ("yes", "no"),
        horizontal=True
    )

    if st.button("📋 Listeyi Getir"):
        st.write("📡 Siparişler çekiliyor...")

        now = int(time.time() * 1000)
        two_weeks_ago = now - (14 * 24 * 60 * 60 * 1000)

        status = "Created"
        orderByField = "PackageLastModifiedDate"
        orderByDirection = "DESC"
        page_size = 50

        all_orders = []
        page_num = 0

        while True:
            url = (
                f"https://apigw.trendyol.com/integration/order/sellers/{supplierid}/orders"
                f"?status={status}"
                f"&startDate={two_weeks_ago}"
                f"&endDate={now}"
                f"&orderByField={orderByField}"
                f"&orderByDirection={orderByDirection}"
                f"&page={page_num}"
                f"&size={page_size}"
            )
            
            response = requests.get(url, auth=HTTPBasicAuth(api_key, api_secret))
            data = response.json()
            
            if response.status_code != 200:
                st.error(f"ERROR: {response.status_code}")
                st.error(data)
                break
            
            content = data.get("content", [])
            if not content:
                break
            
            all_orders.extend(content)
            
            if (page_num + 1) >= data.get("totalPages", 1):
                break
            
            page_num += 1

        st.write(f"✅ Toplam {len(all_orders)} sipariş çekildi.")

        summary = {}

        for order in all_orders:
            if trendyol_filter == "no" and order.get("cargoProviderName") == "Trendyol Express Marketplace":
                continue
            
            lines = order.get("lines", [])
            
            if len(lines) == 1 and lines[0]["quantity"] == 2:
                urun_adi = lines[0].get("productName", "Bilinmeyen Ürün")
                if urun_adi in summary:
                    summary[urun_adi] += 1
                else:
                    summary[urun_adi] = 1

        summary_df = pd.DataFrame(summary.items(), columns=["Ürün Adı", "Sipariş Sayısı"])
        summary_df = summary_df.sort_values(by="Sipariş Sayısı", ascending=False)

        if summary_df.empty:
            st.warning("⚠️ Uygun sipariş bulunamadı.")
        else:
            st.write("### 📋 2 ADET AYNI ÜRÜN OLAN SİPARİŞLER")
            st.dataframe(summary_df, use_container_width=True)

