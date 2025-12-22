import streamlit as st
import pandas as pd
import os
import cv2
import tempfile
from PIL import Image

from process_single import process_form
from azure_ocr import ocr_with_boxes
from heatmap import draw_confidence_heatmap
from pdf_utils import save_as_pdf
from validators import clean_aadhaar
from digit_utils import normalize_digits

st.set_page_config(layout="wide")
st.title("📄 Hindi Form OCR System")

uploaded = st.file_uploader("Upload form", type=["jpg", "png"])

if uploaded:
    # -----------------------------
    # Save uploaded image
    # -----------------------------
    os.makedirs("input_forms", exist_ok=True)
    path = f"input_forms/{uploaded.name}"

    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.image(Image.open(path), width=800)

    # -----------------------------
    # OCR + Field Extraction
    # -----------------------------
    data = process_form(path)
    final_data = {}

    st.subheader("Extracted Fields (Editable)")

    for field, obj in data.items():
        conf = obj["confidence"]
        color = "🟢" if conf > 0.85 else "🟡" if conf > 0.7 else "🔴"
        st.markdown(f"**{field}** {color} ({conf})")
        final_data[field] = st.text_input(field, obj["value"])

    # -----------------------------
    # Heatmap (optional)
    # -----------------------------
    if st.checkbox("🔥 Show Confidence Heatmap"):
        elements = ocr_with_boxes(path)
        heatmap_img = draw_confidence_heatmap(path, elements)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(tmp.name, heatmap_img)
        st.image(tmp.name, width=800)

    # -----------------------------
    # Approve & Save
    # -----------------------------
    if st.button("✅ Approve & Save"):
        # 🔹 Normalize & clean
        final_data["Aadhaar"] = clean_aadhaar(final_data.get("Aadhaar", ""))

        for k in final_data:
            final_data[k] = normalize_digits(final_data[k])

        df = pd.DataFrame([final_data])

        # -----------------------------
        # Save to Excel (APPEND SAFE)
        # -----------------------------
        os.makedirs("output", exist_ok=True)
        excel = "output/approved_forms.xlsx"

        if os.path.exists(excel):
            with pd.ExcelWriter(
                excel,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="overlay"
            ) as writer:
                startrow = writer.sheets["Sheet1"].max_row
                df.to_excel(
                    writer,
                    index=False,
                    header=False,
                    startrow=startrow
                )
        else:
            df.to_excel(excel, index=False)

        # -----------------------------
        # Save PDF with name
        # -----------------------------
        name = final_data.get("Applicant Name", "form").replace(" ", "_")
        save_as_pdf(path, f"{name}.pdf")

        st.success("✅ Saved Excel row + PDF successfully")