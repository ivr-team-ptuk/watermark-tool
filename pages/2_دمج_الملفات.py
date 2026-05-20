import streamlit as st
import fitz
import io

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="دمج ملفات PDF - IVR",
    layout="centered"
)

st.title("دمج ملفات PDF")
st.caption("قم بترتيب الملفات ثم دمجها في ملف واحد")

# =========================
# UPLOAD FILES
# =========================

uploaded_pdfs = st.file_uploader(
    "رفع ملفات PDF",
    type=["pdf"],
    accept_multiple_files=True
)

# =========================
# FILE ORDERING
# =========================

if uploaded_pdfs:

    st.subheader("ترتيب الملفات")

    file_names = [file.name for file in uploaded_pdfs]

    ordered_files = st.multiselect(
        "اختر الترتيب النهائي للملفات",
        options=file_names,
        default=file_names
    )

    # =========================
    # OUTPUT FILE NAME
    # =========================

    output_name = st.text_input(
        "اسم الملف النهائي",
        value="merged_file"
    )

    # =========================
    # MERGE BUTTON
    # =========================

    if st.button("دمج وتحميل"):

        if len(ordered_files) != len(file_names):

            st.error("يجب اختيار جميع الملفات")

        else:

            merged_doc = fitz.open()

            progress = st.progress(0)

            total = len(ordered_files)

            # =========================
            # MERGE FILES
            # =========================

            for index, selected_name in enumerate(ordered_files):

                for uploaded_file in uploaded_pdfs:

                    if uploaded_file.name == selected_name:

                        pdf_bytes = uploaded_file.getvalue()

                        pdf_doc = fitz.open(
                            stream=pdf_bytes,
                            filetype="pdf"
                        )

                        merged_doc.insert_pdf(pdf_doc)

                        pdf_doc.close()

                        break

                progress.progress(
                    (index + 1) / total
                )

            # =========================
            # SAVE OUTPUT
            # =========================

            output_buffer = io.BytesIO()

            merged_doc.save(output_buffer)

            output_buffer.seek(0)

            merged_doc.close()

            # =========================
            # DOWNLOAD
            # =========================

            st.download_button(
                label="تحميل الملف المدمج",
                data=output_buffer,
                file_name=f"{output_name}.pdf",
                mime="application/pdf"
            )

            st.success("تم الدمج بنجاح 🔥")

else:

    st.info("قم برفع ملفات PDF أولاً.")