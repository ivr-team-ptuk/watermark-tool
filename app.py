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
    layout="wide"
)

# =========================
# LOAD CSS
# =========================

with open("styles/style.css", encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

# ROW 1 - NAVBAR
st.markdown("""
<div class="ivr-navbar">
    <a href="https://ivr-home.streamlit.app" target="_blank">Home</a>
    <a href="https://ivr-merge-tool.streamlit.app" target="_blank">Merge PDF</a>
    <a href="https://ivr-watermark-tool.streamlit.app" target="_blank">Watermark PDF</a>
    <a href="https://ivr-imagetopdf-tool.streamlit.app" target="_blank">Image to PDF</a>
</div>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

st.title("")
st.title("تعليم ملفات PDF")
st.caption("أضف علامة مائية احترافية مع معاينة مباشرة")

controls_col, preview_col = st.columns(
    [1, 1.2],
    gap="large"
)

# =========================
# CONTROLS CARD
# =========================

with controls_col:

    uploaded_pdfs = st.file_uploader(
        "رفع ملفات PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="يمكنك رفع عدة ملفات دفعة واحدة"
    )

    st.markdown("<br>", unsafe_allow_html=True)

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
    # OPACITY
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
    # EXCLUDED PAGES
    # =========================

    st.markdown("### الصفحات المستثناة")

    exclude_input = st.text_area(
        "أدخل الصفحات أو النطاقات",
        placeholder=
        "مثال:\n"
        "2\n"
        "5-8\n"
        "11\n"
        "15-20",
        height=180,
        label_visibility="collapsed"
    )

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================

def calculate_rotation(width, height):

    angle_rad = math.atan(height / width)

    return math.degrees(angle_rad)

def calculate_font_size(width, height):

    diagonal = math.sqrt(width**2 + height**2)

    return diagonal / 18

# =========================
# GET LOGO PATH
# =========================

def get_logo_path(opacity):

    percentage = int(opacity * 100)

    percentage = max(1, min(100, percentage))

    return f"logos/logo_{percentage}.png"

# =========================
# PARSE EXCLUDED PAGES
# =========================

def parse_excluded_pages(text):

    excluded = set()

    lines = text.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if "-" in line:

            try:

                start, end = line.split("-")

                start = int(start.strip())
                end = int(end.strip())

                for page in range(start, end + 1):

                    excluded.add(page)

            except:
                pass

        else:

            try:

                excluded.add(int(line))

            except:
                pass

    return excluded

excluded_pages = parse_excluded_pages(
    exclude_input
)

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
    # CORNER MODE
    # =========================

    if mode == "في الزاوية":

        base_size = min(w, h)

        margin = base_size * 0.04

        logo_size = base_size * 0.14

        x = w - logo_size - margin
        y = h - logo_size - margin

        if wm_type == "نص":

            draw_text(
                (x, y),
                base_size * 0.035
            )

        else:

            draw_image(
                fitz.Rect(
                    x,
                    y,
                    x + logo_size,
                    y + logo_size
                )
            )

    # =========================
    # REPEATED MODE
    # =========================

    elif mode == "تكراري":

        base_size = min(w, h)

        spacing_x = base_size * 0.32
        spacing_y = base_size * 0.22

        item_size = base_size * 0.06

        x = -spacing_x

        while x < w + spacing_x:

            y = -spacing_y

            while y < h + spacing_y:

                if wm_type == "نص":

                    draw_text(
                        (x, y),
                        item_size,
                        matrix
                    )

                else:

                    draw_image(
                        fitz.Rect(
                            x,
                            y,
                            x + item_size * 2.2,
                            y + item_size * 2.2
                        )
                    )

                y += spacing_y

            x += spacing_x

    # =========================
    # FULL PAGE
    # =========================

    elif mode == "كامل الصفحة":

        diagonal = math.sqrt(w**2 + h**2)

        font_size = diagonal / (len(wm_text) * 0.6)

        start_point = (
            font_size / 2,
            h
        )

        if wm_type == "نص":

            draw_text(
                start_point,
                font_size * 0.85,
                matrix
            )

        else:

            margin = min(w, h) * 0.06

            draw_image(
                fitz.Rect(
                    margin,
                    margin,
                    w - margin,
                    h - margin
                )
            )

# =========================
# PREVIEW
# =========================

with preview_col:

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

            preview_page_number = st.slider(
                "التنقل بين الصفحات",
                min_value=1,
                max_value=total_pages,
                value=1
            )

            preview_page_number = st.number_input(
                "رقم الصفحة",
                min_value=1,
                max_value=total_pages,
                value=preview_page_number,
                step=1
            )

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
            # PAGE IMAGE
            # =========================

            pix = preview_page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5)
            )

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

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

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# PROCESS BUTTON
# =========================

with controls_col:

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("إنشاء وتحميل"):

        if not uploaded_pdfs:

            st.error("قم بتحميل ملفات PDF أولاً")

        else:

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
                # SAVE
                # =========================

                output_pdf = io.BytesIO()

                doc.save(output_pdf)

                output_pdf.seek(0)

                original_name = uploaded_file.name

                new_name = original_name.replace(
                    ".pdf",
                    "_معلَّم.pdf"
                )

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

                progress.progress(
                    (index + 1) / total_files
                )

            st.success("تم تعليم الملفات بنجاح 🔥")