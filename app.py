import streamlit as st
from PIL import Image
import requests
import cv2
import numpy as np

# ----------------------------
# НАСТРОЙКИ СТРАНИЦЫ
# ----------------------------
st.set_page_config(
    page_title="Product Scanner",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Product Scanner")
st.write("Загрузи фото товара — мы считаем штрихкод и найдём информацию.")
st.divider()


# ----------------------------
# ФУНКЦИЯ: поиск товара
# ----------------------------
def get_product_info(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


# ----------------------------
# ЗАГРУЗКА ФОТО
# ----------------------------
uploaded_file = st.file_uploader(
    "Загрузи фото со штрихкодом",
    type=["jpg", "jpeg", "png", "dng"]
)

if uploaded_file:
    col1, col2 = st.columns(2)

    with col1:
        st.image(uploaded_file, caption="Исходное фото", use_container_width=True)

    try:
        # PIL → OpenCV
        image = Image.open(uploaded_file).convert("RGB")
        img = np.array(image)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Улучшение контраста
        gray = cv2.equalizeHist(gray)

        # ----------------------------
        # СКАНЕР OPENCV
        # ----------------------------
        detector = cv2.barcode.BarcodeDetector()

        with st.spinner("Ищем штрихкод..."):
            success, decoded_info, points, _ = detector.detectAndDecode(gray)

        with col2:
            st.subheader("Результат")

            if not success or not decoded_info:
                st.warning("⚠️ Штрихкод не найден")
                st.markdown("""
                **Попробуй:**
                - лучшее освещение  
                - без бликов  
                - ровный кадр  
                - приблизить камеру
                """)
            else:
                barcode = decoded_info[0]
                st.success("✅ Штрихкод найден")
                st.code(barcode)

                st.divider()

                # ----------------------------
                # ПОИСК В БАЗЕ
                # ----------------------------
                with st.spinner("Ищем товар в базе..."):
                    product_data = get_product_info(barcode)

                if product_data is None:
                    st.error("❌ Ошибка подключения к базе")

                elif product_data.get("status") == 1:
                    product = product_data.get("product", {})

                    st.subheader("🧾 Информация о товаре")
                    st.write("**Название:**", product.get("product_name", "—"))
                    st.write("**Бренд:**", product.get("brands", "—"))
                    st.write("**Страна:**", product.get("countries", "—"))

                    image_url = product.get("image_front_url")
                    if image_url:
                        st.image(image_url, width=220)

                else:
                    st.warning(
                        "⚠️ Товар не найден в базе.\n\n"
                        "Скорее всего, это не продукт питания."
                    )

    except Exception as e:
        st.error("Ошибка обработки изображения")
        st.code(str(e))
