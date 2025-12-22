from azure_ocr import ocr_with_boxes
from spatial_parser import extract_fields_spatial

def process_form(image_path):
    elements = ocr_with_boxes(image_path)
    return extract_fields_spatial(elements)