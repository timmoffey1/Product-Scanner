import streamlit as st
from PIL import Image
import requests
import cv2
import numpy as np

st.set_page_config(page_title="Product Scanner", page_icon="📦")

st.title("📦 Product Scanner")
st.write("Загрузи фото товара — мы попробуем считать штрихкод и найти информацию.")
st.divider()

def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )
    return gray, thresh

uploaded_file = st.file_uploader(
    "Загрузи фото со штрихкодом",
    type=["jpg", "jpeg", "png", "dng"]
)

if uploaded_file:
    col1, col2 = st.columns(2)

    with col1:
        st.image(uploaded_file, caption="Исходное фото", use_container_width=True)

    try:
        img = np.array(Image.open(uploaded_file).convert("RGB"))
        detector = cv2.barcode.BarcodeDetector()
        gray, thresh = preprocess(img)

        with st.spinner("Ищем штрихкод..."):
            result = detector.detectAndDecode(gray)
            if len(result) == 4:
                success, decoded, _, _ = result
            else:
                decoded, _, _ = result
                success = bool(decoded)

            if not success:
                result = detector.detectAndDecode(thresh)
                if len(result) == 4:
                    success, decoded, _, _ = result
                else:
                    decoded, _, _ = result
                    success = bool(decoded)

        with col2:
            st.subheader("Результат анализа")

            if success and decoded:
                barcode = decoded.strip()
                st.success("✅ Штрихкод найден!")
                st.info(f"**Номер:** `{barcode}`")

                st.divider()

                product_data = get_product_info(barcode)

                if product_data and product_data.get("status") == 1:
                    product = product_data["product"]
                    st.subheader("🧾 Информация о товаре")
                    st.write(f"**Название:** {product.get('product_name', 'Не указано')}")
                    st.write(f"**Бренд:** {product.get('brands', 'Не указано')}")

                    if product.get("image_front_url"):
                        st.image(product["image_front_url"], width=220)
                else:
                    st.warning("Товар не найден в базе OpenFoodFacts.")
            else:
                st.warning("⚠️ Штрихкод не найден.")
                st.markdown("""
                **Советы:**
                - Штрихкод должен быть полностью в кадре  
                - Не обрезай сверху и снизу  
                - Избегай бликов  
                """)

    except Exception as e:
        st.error("Ошибка обработки изображения")
        st.code(str(e))
