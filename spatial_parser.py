from field_config import FIELDS
from digit_utils import normalize_digits
import re
from datetime import datetime

def calculate_age_from_dob(dob_text):
    try:
        dob_text = dob_text.replace("/", "-")
        dob = datetime.strptime(dob_text.strip(), "%d-%m-%Y")
        today = datetime.today()
        return str(today.year - dob.year -
                   ((today.month, today.day) < (dob.month, dob.day)))
    except:
        return ""


def extract_height(elements, idx):
    for i in range(idx, min(idx + 4, len(elements))):
        text = normalize_digits(elements[i]["text"])

        # 5'3 , 5/3 , 5-3
        m = re.search(r"(\d)\s*[/\'\-\s]\s*(\d{1,2})", text)
        if m:
            return f"{m.group(1)}'{m.group(2)}", 0.9

        # 6 फीट
        m = re.search(r"\b(\d)\s*फीट", text)
        if m:
            return f"{m.group(1)}'0", 0.9

    return "", 0.0


def extract_weight(elements, idx):
    for i in range(idx, min(idx + 4, len(elements))):
        text = normalize_digits(elements[i]["text"])
        m = re.search(r"\b(\d{2,3})\b", text)
        if m:
            return m.group(1), 0.9
    return "", 0.0

def extract_inline(text):
    text = normalize_digits(text)
    parts = re.split(r"[-:]", text, 1)
    return parts[1].strip() if len(parts) > 1 else ""


def extract_multiline(elements, idx):
    base_y = elements[idx]["box"][1]
    lines = []
    for i in range(idx + 1, min(idx + 6, len(elements))):
        if abs(elements[i]["box"][1] - base_y) < 150:
            lines.append(elements[i]["text"])
    return " ".join(lines)

def is_date_like(digits: str) -> bool:
    try:
        day = int(digits[:2])
        month = int(digits[2:4])
        year = int(digits[4:8])
        if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
            return True
    except:
        pass
    return False

def extract_mobile_whatsapp_from_text(text):
    text = normalize_digits(text)

    mobile = ""
    whatsapp = ""
    mobile_conf = 0.0
    whatsapp_conf = 0.0

    parts = re.split(r"WhatsApp", text, flags=re.IGNORECASE)

    def find_number(digits):
        # 1️⃣ Prefer 10-digit
        for i in range(0, len(digits) - 9):
            chunk = digits[i:i+10]
            if chunk.startswith(("6","7","8","9")):
                return chunk, 0.95

        # 2️⃣ Fallback to 9-digit (OCR miss)
        for i in range(0, len(digits) - 8):
            chunk = digits[i:i+9]
            if chunk.startswith(("6","7","8","9")):
                return chunk, 0.6

        return "", 0.0

    # LEFT → Mobile
    if len(parts) >= 1:
        left_digits = re.sub(r"\D", "", parts[0])
        mobile, mobile_conf = find_number(left_digits)

    # RIGHT → WhatsApp
    if len(parts) >= 2:
        right_digits = re.sub(r"\D", "", parts[1])
        whatsapp, whatsapp_conf = find_number(right_digits)

    return mobile, whatsapp, mobile_conf, whatsapp_conf

def extract_aadhaar_from_elements(elements):
    candidates = []

    for idx, el in enumerate(elements):
        text = normalize_digits(el["text"])

        # ✅ ONLY look near Aadhaar label
        if "आधार" not in text:
            continue

        # Scan this line + next few lines
        for j in range(idx, min(idx + 4, len(elements))):
            t = normalize_digits(elements[j]["text"])
            digits = re.sub(r"\D", "", t)

            # ✅ Must be exactly 12 digits
            if len(digits) == 12 and not is_date_like(digits):
                candidates.append((digits, elements[j]["confidence"]))

    if candidates:
        # pick highest confidence candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0], max(0.9, candidates[0][1])

    return "", 0.0


def extract_age(elements, label_idx):
    for i in range(label_idx, min(label_idx + 6, len(elements))):
        text = normalize_digits(elements[i]["text"])
        nums = re.findall(r"\b\d{2}\b", text)
        if nums:
            return nums[0], 0.85
    return "", 0.0


def extract_fields_spatial(elements):
    result = {}

    # 🔹 Aadhaar is GLOBAL
    aadhaar_value, aadhaar_conf = extract_aadhaar_from_elements(elements)

    for field, keys in FIELDS.items():
        value = ""
        confidence = 0.0

        # 🔹 Aadhaar (special case)
        if field == "Aadhaar":
            result[field] = {
                "value": aadhaar_value,
                "confidence": round(aadhaar_conf, 2)
            }
            continue

        for idx, el in enumerate(elements):
            text = normalize_digits(el["text"])

            if any(k in text for k in keys):

                # 🔹 Mobile & WhatsApp
                # 🔹 Mobile & WhatsApp
                if field in ("Mobile", "WhatsApp"):
                    mob, wa, mob_conf, wa_conf = extract_mobile_whatsapp_from_text(text)

                    if field == "Mobile" and mob:
                        value = mob
                        confidence = mob_conf
                        break

                    if field == "WhatsApp" and wa:
                        value = wa
                        confidence = wa_conf
                        break


                # 🔹 Address
                if field == "Address":
                    value = extract_multiline(elements, idx)
                    confidence = max(0.85, el["confidence"])
                    break

                # 🔹 Age
                # 🔹 Age (inline OR from DOB)
                if field == "Age":
                    m = re.search(r"\b(\d{2})\b", text)
                    if m:
                        value = m.group(1)
                        confidence = 0.95
                    else:
                        dob = result.get("DOB", {}).get("value", "")
                        age = calculate_age_from_dob(dob)
                        if age:
                            value = age
                            confidence = 0.9
                    break

                if field == "Height":
                    value, confidence = extract_height(elements, idx)
                    break

                if field == "Weight":
                    value, confidence = extract_weight(elements, idx)
                    break


                # 🔹 Inline default
                inline = extract_inline(text)
                if inline:
                    value = inline
                    confidence = max(0.85, el["confidence"])
                    break

        result[field] = {
            "value": value,
            "confidence": round(confidence, 2)
        }

    return result