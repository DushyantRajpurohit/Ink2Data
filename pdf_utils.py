import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def save_as_pdf(image_path, filename):
    os.makedirs("output/pdfs", exist_ok=True)
    pdf_path = os.path.join("output/pdfs", filename)

    c = canvas.Canvas(pdf_path, pagesize=A4)

    page_width, page_height = A4

    # Load image size
    from PIL import Image as PILImage
    img = PILImage.open(image_path)
    img_width, img_height = img.size

    # Scale image to fit page
    scale = min(
        page_width / img_width,
        page_height / img_height
    )

    draw_width = img_width * scale
    draw_height = img_height * scale

    x = (page_width - draw_width) / 2
    y = (page_height - draw_height) / 2

    # 🔹 Draw image directly (NO FLOW, NO SPLIT)
    c.drawImage(
        image_path,
        x,
        y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto"
    )

    c.showPage()
    c.save()

