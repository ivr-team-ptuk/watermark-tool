import streamlit as st
import fitz
import math
import io
import base64
from PIL import Image
from streamlit_pdf_viewer import pdf_viewer

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
# LAYOUT
# =========================

controls_col, preview_col = st.columns(
    [1, 1.2]
)

# =========================
# UI
# =========================
with controls_col:

    uploaded_pdfs = st.file_uploader(
        "رفع ملفات PDF",
        type=["pdf"],
        accept_multiple_files=True
    )

with controls_col:

    watermark_type = st.selectbox(
        "نوع العلامة المائية",
        ["نص", "شعار"]
    )

watermark_text = "IVR TEAM"

with controls_col:

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
    with controls_col:
        opacity = st.slider(
            "شفافية النص",
            min_value=0.01,
            max_value=0.50,
            value=0.10
        )

else:
    with controls_col:
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
with controls_col:
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
with controls_col:
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
    # PARSE EXCLUDED PAGES
    # =========================

with controls_col:

    def parse_excluded_pages(text):

        excluded = set()

        lines = text.splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                continue

            # =========================
            # RANGE
            # =========================

            if "-" in line:

                try:

                    start, end = line.split("-")

                    start = int(start.strip())
                    end = int(end.strip())

                    for page in range(start, end + 1):

                        excluded.add(page)

                except:
                    pass

            # =========================
            # SINGLE PAGE
            # =========================

            else:

                try:

                    excluded.add(int(line))

                except:
                    pass

        return excluded

# =========================
# EXCLUDED PAGES
# =========================
with controls_col:

    exclude_input = st.text_area(
        "الصفحات المستثناة",
        placeholder=
        "مثال:\n"
        "2\n"
        "5-8\n"
        "11\n"
        "15-20"
    )

with controls_col:
    excluded_pages = parse_excluded_pages(
        exclude_input
    )

# =========================
# LIVE PREVIEW
# =========================

with preview_col:

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

            total_pages = len(preview_doc)

            # =========================
            # PAGE SELECTOR
            # =========================
            with controls_col:
                st.markdown("### اختر الصفحة التي تريد عرضها")

                preview_page_number = st.slider(
                    " التنقل السريع بين الصفحات",
                    min_value=1,
                    max_value=total_pages,
                    value=1
                )
            with controls_col:
                preview_page_number = st.number_input(
                    "أو اكتب رقم الصفحة التي تريد عرضها",
                    min_value=1,
                    max_value=total_pages,
                    value=preview_page_number,
                    step=1
                )

            # =========================
            # GET PAGE
            # =========================

            preview_page = preview_doc[
                preview_page_number - 1
            ]

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

            if preview_page_number not in excluded_pages:

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
                caption=f"معاينة الصفحة {preview_page_number}",
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

with controls_col:

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

                for page_index, page in enumerate(doc, start=1):

                    if page_index in excluded_pages:
                        continue

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
