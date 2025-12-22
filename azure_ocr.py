import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from digit_utils import normalize_digits

VISION_KEY = "5Uc7It14ndBIbYUJTizEkDSEGfZlPp0MbyiF5kvkB3JBv3ODxIJGJQQJ99BLACGhslBXJ3w3AAAFACOGjwEY"
VISION_ENDPOINT = "https://hindi-form-ocr.cognitiveservices.azure.com/"

client = ComputerVisionClient(
    VISION_ENDPOINT,
    CognitiveServicesCredentials(VISION_KEY)
)

def ocr_with_boxes(image_path):
    with open(image_path, "rb") as img:
        response = client.read_in_stream(img, raw=True)

    operation_id = response.headers["Operation-Location"].split("/")[-1]

    while True:
        result = client.get_read_result(operation_id)
        if result.status not in ["running", "notStarted"]:
            break
        time.sleep(1)

    elements = []
    for page in result.analyze_result.read_results:
        for line in page.lines:
            elements.append({
                "text": normalize_digits(line.text),
                "box": line.bounding_box,
                "confidence": min(w.confidence for w in line.words)
            })
    return elements