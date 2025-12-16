import streamlit as st
from PIL import Image
import requests

from pyzbar.pyzbar import decode
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
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None


# ----------------------------
# ЗАГРУЗКА ФОТО
# ----------------------------
uploaded_file = st.file_uploader(
    "Загрузи фото со штрихкодом",
    type=["jpg", "jpeg", "png", "DNG"]  # ❗ DNG УБРАН
)

if uploaded_file:

    col1, col2 = st.columns(2)

    with col1:
        st.image(uploaded_file, caption="Исходное фото", use_container_width=True)

    try:
        # ----------------------------
        # ПОДГОТОВКА ИЗОБРАЖЕНИЯ
        # ----------------------------
        pil_image = Image.open(uploaded_file).convert("RGB")
        img = np.array(pil_image)

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Улучшаем контраст
        gray = cv2.equalizeHist(gray)

        # Бинаризация (очень помогает)
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # ----------------------------
        # ПОИСК ШТРИХКОДА
        # ----------------------------
        with st.spinner("Ищем штрихкод..."):
            decoded_objects = decode(thresh)

        with col2:
            st.subheader("Результат анализа")

            if not decoded_objects:
                st.warning("⚠️ Штрихкод не найден")
                st.markdown(
                    """
                    **Попробуй:**
                    - лучшее освещение  
                    - без бликов  
                    - приблизить камеру  
                    - ровный кадр
                    """
                )
            else:
                obj = decoded_objects[0]
                barcode = obj.data.decode("utf-8")
                barcode_type = obj.type

                st.success("✅ Штрихкод найден!")
                st.info(f"**Тип:** {barcode_type}\n\n**Номер:** `{barcode}`")

                st.divider()

                # ----------------------------
                # ПОИСК В OPENFOODFACTS
                # ----------------------------
                with st.spinner("Ищем товар в базе OpenFoodFacts..."):
                    product_data = get_product_info(barcode)

                if product_data is None:
                    st.error("❌ Не удалось подключиться к базе OpenFoodFacts")

                elif product_data.get("status") == 1:
                    product = product_data.get("product", {})

                    st.subheader("🧾 Информация о товаре")

                    st.write("**Название:**", product.get("product_name", "Не указано"))
                    st.write("**Бренд:**", product.get("brands", "Не указано"))
                    st.write("**Страна:**", product.get("countries", "Не указано"))

                    categories = product.get("categories")
                    if categories:
                        st.write("**Категории:**", categories.split(",")[0])
                    else:
                        st.write("**Категории:** Не указано")

                    image_url = product.get("image_front_url")
                    if image_url:
                        st.image(image_url, width=220, caption="Фото из базы")
                    else:
                        st.caption("Фото товара отсутствует в базе")

                else:
                    st.warning(
                        "⚠️ Товар с таким штрихкодом найден, "
                        "но информации о нём нет.\n\n"
                        "Скорее всего, это **не продукт питания**."
                    )

    except Exception as e:
        st.error("❌ Ошибка при обработке изображения")
        st.code(str(e))
