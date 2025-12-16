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
st.write("Загрузи фото товара — мы попробуем считать штрихкод и найти информацию.")
st.divider()

# ----------------------------
# ФУНКЦИЯ: поиск товара в OpenFoodFacts
# ----------------------------
def get_product_info(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
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

    # ----------------------------
    # ОТОБРАЖЕНИЕ ФОТО
    # ----------------------------
    with col1:
        st.image(uploaded_file, caption="Исходное фото", use_container_width=True)

    try:
        # ----------------------------
        # ПОДГОТОВКА ИЗОБРАЖЕНИЯ
        # ----------------------------
        pil_image = Image.open(uploaded_file).convert("RGB")
        img = np.array(pil_image)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # ----------------------------
        # ПОИСК ШТРИХКОДА (OpenCV)
        # ----------------------------
        detector = cv2.barcode.BarcodeDetector()

        with st.spinner("Ищем штрихкод..."):
            result = detector.detectAndDecode(gray)

        # Совместимость с разными версиями OpenCV
        if len(result) == 4:
            success, decoded_info, points, _ = result
        else:
            success, decoded_info, points = result

        with col2:
            st.subheader("Результат анализа")

            if success and decoded_info:
                barcode = decoded_info.strip()
                st.success("✅ Штрихкод найден!")
                st.info(f"**Тип:** EAN / UPC\n\n**Номер:** `{barcode}`")

                st.divider()

                # ----------------------------
                # ПОИСК ТОВАРА
                # ----------------------------
                with st.spinner("Ищем товар в базе..."):
                    product_data = get_product_info(barcode)

                if product_data and product_data.get("status") == 1:
                    product = product_data.get("product", {})

                    st.subheader("🧾 Информация о товаре")
                    st.write(f"**Название:** {product.get('product_name', 'Не указано')}")
                    st.write(f"**Бренд:** {product.get('brands', 'Не указано')}")

                    categories = product.get("categories", "Не указано")
                    if len(categories) > 120:
                        categories = categories[:120] + "..."
                    st.write(f"**Категории:** {categories}")

                    image_url = product.get("image_front_url")
                    if image_url:
                        st.image(image_url, width=220, caption="Фото из базы OpenFoodFacts")
                    else:
                        st.caption("Фото товара отсутствует в базе.")

                elif product_data and product_data.get("status") == 0:
                    st.warning("Товар с таким штрихкодом не найден в OpenFoodFacts.")
                else:
                    st.error("Ошибка при подключении к базе товаров.")

            else:
                st.warning("⚠️ Штрихкод не найден.")
                st.write(
                    "- Убедись, что штрихкод полностью в кадре\n"
                    "- Избегай бликов\n"
                    "- Попробуй сделать фото ровнее"
                )

    except Exception as e:
        st.error("❌ Ошибка обработки изображения")
        st.code(str(e))
