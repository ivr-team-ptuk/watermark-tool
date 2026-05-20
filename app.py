import streamlit as st
import fitz
import math
import io
import base64
from PIL import Image

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="أداة تعليم الملفات - IVR",
    layout="centered"
)

st.title("تعليم ملفات PDF - IVR Scientific")
st.caption("يتم تحديث المعاينة تلقائيًا عند تغيير الإعدادات")

# =========================
# UI
# =========================

uploaded_pdfs = st.file_uploader(
    "رفع ملفات PDF",
    type=["pdf"],
    accept_multiple_files=True
)

watermark_type = st.selectbox(
    "نوع العلامة المائية",
    ["نص", "شعار"]
)

watermark_text = "IVR TEAM"

mode = st.selectbox(
    "الوضعية",
    [
        "في الزاوية",
        "كامل الصفحة",
        "تكراري"
    ]
)

# =========================
# OPACITY SLIDER
# =========================

if watermark_type == "نص":

    opacity = st.slider(
        "شفافية النص",
        min_value=0.01,
        max_value=0.50,
        value=0.10
    )

else:

    opacity = st.slider(
        "شفافية الشعار",
        min_value=0.01,
        max_value=1.00,
        value=0.10
    )

# =========================
# HELPERS
# =========================

def calculate_rotation(width, height):

    angle_rad = math.atan(height / width)
    angle_deg = math.degrees(angle_rad)

    return angle_deg

def calculate_font_size(width, height):

    diagonal = math.sqrt(width**2 + height**2)

    return diagonal / 18

# =========================
# GET LOGO PATH
# =========================

def get_logo_path(opacity):

    percentage = int(opacity * 100)

    if percentage < 1:
        percentage = 1

    if percentage > 100:
        percentage = 100

    return f"logos/logo_{percentage}.png"

# =========================
# WATERMARK FUNCTION
# =========================

def insert_watermark(
    page,
    wm_type,
    wm_text,
    opacity,
    mode,
    image_bytes=None
):

    rect = page.rect

    w = rect.width
    h = rect.height

    rotation = calculate_rotation(w, h)

    font_size = calculate_font_size(w, h)

    matrix = fitz.Matrix(1,1).prerotate(rotation)

    # =========================
    # DRAW TEXT
    # =========================

    def draw_text(p, fs, morph_matrix=None):

        page.insert_text(
            p,
            wm_text,
            fontsize=fs,
            color=(1,0,0),
            fill_opacity=opacity,
            morph=(
                (fitz.Point(*p), morph_matrix)
                if morph_matrix
                else None
            )
        )

    # =========================
    # DRAW IMAGE
    # =========================

    def draw_image(r):

        page.insert_image(
            r,
            stream=image_bytes,
            overlay=True,
            keep_proportion=True
        )

    # =========================
    # CORNERS MODE
    # =========================

    if mode == "في الزاوية":

        points = [
            (w-150, h-120)
        ]

        for p in points:

            if wm_type == "نص":

                draw_text(
                    p,
                    font_size/2
                )

            else:

                draw_image(
                    fitz.Rect(
                        p[0],
                        p[1],
                        p[0]+120,
                        p[1]+120
                    )
                )

    # =========================
    # ADAPTIVE DIAGONAL
    # =========================

    elif mode == "تكراري":

        x = 0

        while x < w:

            y = 0

            while y < h:

                if wm_type == "نص":

                    draw_text(
                        (x,y),
                        font_size,
                        matrix
                    )

                else:

                    size = font_size * 3

                    draw_image(
                        fitz.Rect(
                            x,
                            y,
                            x+size,
                            y+size
                        )
                    )

                y += 120

            x += 180

    # =========================
    # FULL PAGE
    # =========================

    elif mode == "كامل الصفحة":

        diagonal = math.sqrt(w**2 + h**2)

        font_size = diagonal / (len(wm_text) * 0.6)

        start_point = (
            font_size/2,
            h
        )

        if wm_type == "نص":

            draw_text(
                start_point,
                font_size * 0.85,
                matrix
            )

        else:

            margin = 40

            draw_image(
                fitz.Rect(
                    margin,
                    margin,
                    w - margin,
                    h - margin
                )
            )

# =========================
# LIVE PREVIEW
# =========================

st.divider()

st.subheader("المعاينة المباشرة")

if uploaded_pdfs:

    try:

        preview_file = uploaded_pdfs[0]

        preview_bytes = preview_file.getvalue()

        preview_doc = fitz.open(
            stream=preview_bytes,
            filetype="pdf"
        )

        preview_page = preview_doc[0]

        image_bytes = None

        # =========================
        # LOAD LOGO
        # =========================

        if watermark_type == "شعار":

            image_path = get_logo_path(opacity)

            with open(image_path, "rb") as f:

                image_bytes = f.read()

        # =========================
        # APPLY WATERMARK
        # =========================

        insert_watermark(
            preview_page,
            watermark_type,
            watermark_text,
            opacity,
            mode,
            image_bytes
        )

        # =========================
        # CONVERT TO IMAGE
        # =========================

        pix = preview_page.get_pixmap(
            matrix=fitz.Matrix(1.5, 1.5)
        )

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        # =========================
        # SHOW IMAGE
        # =========================

        st.image(
            img,
            caption="معاينة مباشرة لأول صفحة",
            use_container_width=True
        )

        preview_doc.close()

    except Exception as e:

        st.error(f"خطأ في المعاينة: {e}")

else:

    st.info("قم برفع ملف PDF لرؤية المعاينة.")

# =========================
# PROCESS BUTTON
# =========================

if st.button("إنشاء وتحميل"):

    if not uploaded_pdfs:

        st.error("قم بتحميل ملفات PDF أولاً")

    else:

        st.success("يتم تعليم الملفات...")

        progress = st.progress(0)

        total_files = len(uploaded_pdfs)

        for index, uploaded_file in enumerate(uploaded_pdfs):

            pdf_bytes = uploaded_file.getvalue()

            doc = fitz.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            image_bytes = None

            # =========================
            # LOAD LOGO
            # =========================

            if watermark_type == "شعار":

                image_path = get_logo_path(opacity)

                with open(image_path, "rb") as f:

                    image_bytes = f.read()

            # =========================
            # APPLY WATERMARK
            # =========================

            for page in doc:

                insert_watermark(
                    page,
                    watermark_type,
                    watermark_text,
                    opacity,
                    mode,
                    image_bytes
                )

            # =========================
            # SAVE OUTPUT
            # =========================

            output_pdf = io.BytesIO()

            doc.save(output_pdf)

            output_pdf.seek(0)

            # =========================
            # FILE NAME
            # =========================

            original_name = uploaded_file.name

            new_name = original_name.replace(
                ".pdf",
                "_معلَّم.pdf"
            )

            # =========================
            # AUTO DOWNLOAD LINK
            # =========================

            b64 = base64.b64encode(
                output_pdf.read()
            ).decode()

            href = f'''
                <a href="data:application/pdf;base64,{b64}"
                download="{new_name}">
                تحميل {new_name}
                </a>
            '''

            st.markdown(
                href,
                unsafe_allow_html=True
            )

            # =========================
            # UPDATE PROGRESS
            # =========================

            progress.progress(
                (index + 1) / total_files
            )

        st.success("جاهز 🔥")