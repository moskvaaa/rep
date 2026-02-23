import streamlit as st
import fitz  # PyMuPDF
import tempfile
import os

# Константы
A4_WIDTH = 595
A4_HEIGHT = 842
MM_TO_POINTS = 72 / 25.4
IMG_WIDTH_MM = 68
IMG_HEIGHT_MM = 60
IMG_WIDTH_PT = IMG_WIDTH_MM * MM_TO_POINTS
IMG_HEIGHT_PT = IMG_HEIGHT_MM * MM_TO_POINTS

st.set_page_config(page_title="Извлечение этикеток EMEX", layout="centered")
st.title("📄 Извлечение этикеток EMEX из PDF")

with st.sidebar:
    st.header("Настройки")
    mode = st.radio(
        "Выберите режим:",
        options=[
            "Страница A4, этикетка 68×60 мм в левом верхнем углу",
            "Страница 68×60 мм, этикетка на всю страницу"
        ]
    )
    mode_a4 = (mode == "Страница A4, этикетка 68×60 мм в левом верхнем углу")
    compress = st.checkbox("Сжать выходной PDF", value=True)

uploaded_file = st.file_uploader("Загрузите PDF файл", type=['pdf'])

if uploaded_file:
    with st.spinner("Обработка..."):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name

            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name

            src_pdf = fitz.open(input_path)
            dst_pdf = fitz.open()

            images_found = 0
            images_extracted = 0

            for page_num in range(len(src_pdf)):
                page = src_pdf[page_num]
                image_list = page.get_images()
                images_found += len(image_list)

                for img in image_list:
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(src_pdf, xref)

                        if pix.colorspace and pix.colorspace.name not in (fitz.csRGB.name, fitz.csGRAY.name):
                            pix = fitz.Pixmap(fitz.csRGB, pix)

                        if mode_a4:
                            new_page = dst_pdf.new_page(width=A4_WIDTH, height=A4_HEIGHT)
                            rect = fitz.Rect(0, 0, IMG_WIDTH_PT, IMG_HEIGHT_PT)
                        else:
                            new_page = dst_pdf.new_page(width=IMG_WIDTH_PT, height=IMG_HEIGHT_PT)
                            rect = fitz.Rect(0, 0, IMG_WIDTH_PT, IMG_HEIGHT_PT)

                        new_page.insert_image(rect, pixmap=pix)
                        images_extracted += 1
                        pix = None
                    except Exception as e:
                        st.warning(f"Ошибка обработки изображения: {e}")
                        continue

            src_pdf.close()

            if images_extracted > 0:
                if compress:
                    dst_pdf.save(output_path, garbage=4, deflate=True)
                else:
                    dst_pdf.save(output_path)
                dst_pdf.close()

                st.success(f"✅ Готово! Найдено: {images_found}, извлечено: {images_extracted}")

                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="📥 Скачать результат",
                        data=f,
                        file_name="result.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("В файле не найдено изображений")

            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

        except Exception as e:
            st.error(f"Ошибка: {str(e)}")