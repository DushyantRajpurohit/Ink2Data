import re
from digit_utils import normalize_digits

def clean_aadhaar(text):
    text = normalize_digits(text)
    text = re.sub(r"\D", "", text)
    return text[:12]