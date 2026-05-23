"""
IVR PDF Watermark Tool
أداة تعليم ملفات PDF
"""

import base64
import io
import math
import os

import fitz
import streamlit as st
from PIL import Image


# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="أداة تعليم الملفات - IVR",
    page_icon="Black_Square-01.svg",
    layout="wide",
)

# =========================
# CONSTANTS
# =========================

LOGO_URL = (
    "https://raw.githubusercontent.com/"
    "ivr-team-ptuk/home-page/main/Black_Square-01.svg"
)

# ──────────────────────────────────────────────
# INJECT CSS
# ──────────────────────────────────────────────

_css_path = os.path.join("styles", "style.css")
if os.path.exists(_css_path):
    with open(_css_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)


# =========================
# NAVBAR (fixed via CSS — no iframe needed)
# =========================

st.markdown(f"""
<nav class="ivr-navbar">
    <a href="https://ivr-home-page.streamlit.app" class="nav-logo">
        <img src="{LOGO_URL}" class="nav-logo-img" alt="IVR">
    </a>
    <div class="nav-links">
        <a href="https://ivr-watermark-tool.streamlit.app">تعليم الملفات</a>
        <a href="https://ivr-merge-tool.streamlit.app">دمج الملفات</a>
        <a href="https://ivr-imagetopdf-tool.streamlit.app">الصور إلى PDF</a>
    </div>
</nav>
""", unsafe_allow_html=True)

# =========================
# PAGE HEADER
# =========================

st.markdown(f"""
<div class="page-header">
    <img src="{LOGO_URL}" class="hero-logo" alt="IVR Logo">
    <h1>تعليم ملفات PDF</h1>
    <p>أضف علامة مائية احترافية مع معاينة مباشرة</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _rotation_deg(w: float, h: float) -> float:
    """Diagonal angle of a rectangle in degrees."""
    return math.degrees(math.atan(h / w))


def _logo_path(opacity: float) -> str:
    """Return the pre-rendered logo PNG for the given opacity level."""
    pct = max(1, min(100, int(opacity * 100)))
    return os.path.join("logos", f"logo_{pct}.png")


def parse_excluded_pages(raw: str) -> set[int]:
    """Parse a multiline string of page numbers / ranges into a set of ints."""
    pages: set[int] = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "-" in line:
            try:
                a, b = line.split("-", maxsplit=1)
                pages.update(range(int(a.strip()), int(b.strip()) + 1))
            except ValueError:
                pass
        else:
            try:
                pages.add(int(line))
            except ValueError:
                pass
    return pages


def apply_watermark(
    page: fitz.Page,
    wm_type: str,
    wm_text: str,
    opacity: float,
    mode: str,
    image_bytes: bytes | None = None,
) -> None:
    """Stamp a single fitz.Page with the chosen watermark style."""
    w, h = page.rect.width, page.rect.height
    base = min(w, h)
    morph_matrix = fitz.Matrix(1, 1).prerotate(_rotation_deg(w, h))

    def _draw_text(pt: tuple[float, float], fs: float, rotate: bool = False) -> None:
        page.insert_text(
            pt,
            wm_text,
            fontsize=fs,
            color=(1, 0, 0),
            fill_opacity=opacity,
            morph=((fitz.Point(*pt), morph_matrix) if rotate else None),
        )

    def _draw_image(rect: fitz.Rect) -> None:
        if image_bytes:
            page.insert_image(rect, stream=image_bytes, overlay=True, keep_proportion=True)

    # ── Corner ───────────────────────────────
    if mode == "في الزاوية":
        margin  = base * 0.04
        logo_sz = base * 0.14
        x = w - logo_sz - margin
        y = h - logo_sz - margin
        if wm_type == "نص":
            _draw_text((x, y), base * 0.035)
        else:
            _draw_image(fitz.Rect(x, y, x + logo_sz, y + logo_sz))

    # ── Tiled / Repeated ─────────────────────
    elif mode == "تكراري":
        sp_x     = base * 0.32
        sp_y     = base * 0.22
        item_sz  = base * 0.06
        x = -sp_x
        while x < w + sp_x:
            y = -sp_y
            while y < h + sp_y:
                if wm_type == "نص":
                    _draw_text((x, y), item_sz, rotate=True)
                else:
                    _draw_image(fitz.Rect(x, y, x + item_sz * 2.2, y + item_sz * 2.2))
                y += sp_y
            x += sp_x

    # ── Full-page ────────────────────────────
    elif mode == "كامل الصفحة":
        if wm_type == "نص":
            fs = math.hypot(w, h) / (len(wm_text) * 0.6)
            _draw_text((fs / 2, h), fs * 0.85, rotate=True)
        else:
            margin = base * 0.06
            _draw_image(fitz.Rect(margin, margin, w - margin, h - margin))


def _load_image_bytes(opacity: float) -> bytes | None:
    """Read the pre-rendered logo PNG for a given opacity; return None if missing."""
    path = _logo_path(opacity)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def _watermark_doc(doc: fitz.Document, wm_type, wm_text, opacity, mode, excluded) -> bytes:
    """Apply watermark to all non-excluded pages and return the PDF bytes."""
    image_bytes = _load_image_bytes(opacity) if wm_type == "شعار" else None
    for idx, page in enumerate(doc, start=1):
        if idx not in excluded:
            apply_watermark(page, wm_type, wm_text, opacity, mode, image_bytes)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ──────────────────────────────────────────────
# SESSION STATE — page-navigation sync
# ──────────────────────────────────────────────

if "preview_page" not in st.session_state:
    st.session_state.preview_page = 1


# ──────────────────────────────────────────────
# MAIN LAYOUT
# ──────────────────────────────────────────────

controls_col, preview_col = st.columns([1, 1.2], gap="large")


# ──────────────────────────────────────────────
# CONTROLS
# ──────────────────────────────────────────────

with controls_col:

    uploaded_pdfs = st.file_uploader(
        "رفع ملفات PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="يمكنك رفع عدة ملفات دفعة واحدة",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    watermark_type = st.selectbox("نوع العلامة المائية", ["نص", "شعار"])
    watermark_text = "IVR TEAM"

    mode = st.selectbox("الوضعية", ["في الزاوية", "كامل الصفحة", "تكراري"])

    opacity = st.slider(
        "الشفافية",
        min_value=0.01,
        max_value=0.50 if watermark_type == "نص" else 1.00,
        value=0.10,
    )

    st.markdown("### الصفحات المستثناة")
    exclude_input = st.text_area(
        "الصفحات المستثناة",
        placeholder="مثال:\n2\n5-8\n11\n15-20",
        height=180,
        label_visibility="collapsed",
    )

    excluded_pages = parse_excluded_pages(exclude_input)

    st.markdown("<br>", unsafe_allow_html=True)

    process_clicked = st.button("إنشاء وتحميل", use_container_width=True)


# ──────────────────────────────────────────────
# PREVIEW
# ──────────────────────────────────────────────

with preview_col:
    st.subheader("المعاينة المباشرة")

    if not uploaded_pdfs:
        st.info("قم برفع ملف PDF لرؤية المعاينة.")
    else:
        try:
            preview_bytes = uploaded_pdfs[0].getvalue()
            preview_doc   = fitz.open(stream=preview_bytes, filetype="pdf")
            total_pages   = len(preview_doc)

            # Clamp session state to valid range whenever total_pages changes
            st.session_state.preview_page = min(
                st.session_state.preview_page, total_pages
            )

            # Slider and number_input share the same session-state key
            st.slider(
                "التنقل بين الصفحات",
                min_value=1,
                max_value=total_pages,
                key="preview_page",
            )
            st.number_input(
                "رقم الصفحة",
                min_value=1,
                max_value=total_pages,
                step=1,
                key="preview_page",  # same key → stays in sync automatically
            )

            current_page = st.session_state.preview_page

            # Build a temporary copy so we don't mutate the original bytes
            tmp_doc  = fitz.open(stream=preview_bytes, filetype="pdf")
            tmp_page = tmp_doc[current_page - 1]

            if current_page not in excluded_pages:
                img_bytes = _load_image_bytes(opacity) if watermark_type == "شعار" else None
                apply_watermark(tmp_page, watermark_type, watermark_text, opacity, mode, img_bytes)

            pix = tmp_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            st.image(
                pil_img,
                caption=f"معاينة الصفحة {current_page} من {total_pages}",
                use_container_width=True,
            )
            tmp_doc.close()
            preview_doc.close()

        except Exception as exc:
            st.error(f"خطأ في المعاينة: {exc}")


# ──────────────────────────────────────────────
# PROCESS & DOWNLOAD
# ──────────────────────────────────────────────

if process_clicked:
    if not uploaded_pdfs:
        st.error("قم بتحميل ملفات PDF أولاً")
    else:
        progress_bar = st.progress(0)
        total        = len(uploaded_pdfs)

        for i, uploaded_file in enumerate(uploaded_pdfs):
            doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            pdf_bytes = _watermark_doc(
                doc, watermark_type, watermark_text, opacity, mode, excluded_pages
            )
            doc.close()

            out_name = uploaded_file.name.replace(".pdf", "_معلَّم.pdf")
            b64_data = base64.b64encode(pdf_bytes).decode()

            st.markdown(
                f'<a href="data:application/pdf;base64,{b64_data}" '
                f'download="{out_name}">⬇ تحميل {out_name}</a>',
                unsafe_allow_html=True,
            )
            progress_bar.progress((i + 1) / total)

        st.success("تم تعليم الملفات بنجاح 🔥")


# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.markdown(
    '<div class="footer">IVR Engineering Society &copy; 2026</div>',
    unsafe_allow_html=True,
)
