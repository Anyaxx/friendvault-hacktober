from PIL import Image
import pytesseract
import re
import dateparser
import cv2
import numpy as np
from typing import List, Dict


def preprocess_image(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL image to OpenCV image, deskew, convert to grayscale, and enhance contrast."""
    img = np.array(pil_image.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    max_dim = 1600
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    coords = np.column_stack(np.where(th > 0))
    angle = 0.0
    if coords.shape[0] > 0:
        try:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
        except Exception:
            angle = 0.0

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    gray_rot = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray_rot)

    return enhanced


def ocr_image(image: Image.Image) -> str:
    """Run preprocessing then Tesseract OCR on a PIL Image and return extracted text."""
    try:
        proc = preprocess_image(image)
        text = pytesseract.image_to_string(proc, lang='eng')
    except Exception:
        text = pytesseract.image_to_string(image)
    return text


def suggest_amount(text: str) -> str:
    """Try to find the total amount in OCR text using stronger heuristics."""
    if not text:
        return ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    keywords = ['total', 'amount', 'balance', 'amt']
    price_pattern = r"([0-9]{1,3}(?:[,\.][0-9]{3})*(?:[\.,][0-9]{2}))"
    for line in reversed(lines[-20:]):
        for k in keywords:
            if k in line.lower():
                m = re.search(price_pattern, line)
                if m:
                    return m.group(1).replace(',', '')

    all_nums = re.findall(price_pattern, text)
    if all_nums:
        cleaned = [n.replace(',', '') for n in all_nums]
        try:
            return max(cleaned, key=lambda s: float(s))
        except Exception:
            return cleaned[0]

    return ""


def suggest_date(text: str) -> str:
    """Search for the first parseable date in text."""
    if not text:
        return ""
    try:
        from dateparser.search import search_dates
        found = search_dates(text, settings={'PREFER_DATES_FROM': 'past'})
        if found:
            return found[0][1].date().isoformat()
    except Exception:
        for line in text.splitlines():
            try:
                d = dateparser.parse(line, settings={'PREFER_DATES_FROM': 'past'})
                if d:
                    return d.date().isoformat()
            except Exception:
                continue
    return ""


def suggest_vendor(text: str) -> str:
    """Heuristic: examine the top few lines and prefer the most 'merchant-like' one."""
    if not text:
        return ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidates = []
    for i, line in enumerate(lines[:10]):
        if len(line) < 3:
            continue
        if re.search(r"\d", line) and len(line.split()) > 4:
            continue
        score = 0
        if line.isupper():
            score += 2
        if len(line) > 10:
            score += 1
        if re.search(r"[A-Za-z]", line):
            score += 1
        if not re.search(r"\b(RECEIPT|INVOICE|TAX|NO\.|DATE|AMOUNT|TOTAL)\b", line, re.I):
            candidates.append((score, i, line))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][2]
    for line in lines:
        if len(line) > 2:
            return line
    return ""


def parse_line_items(text: str) -> List[Dict[str,str]]:
    """Parse candidate line items consisting of a short description and a price at line end."""
    if not text:
        return []
    items = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    price_re = re.compile(r"([0-9]+[\.,][0-9]{2})\s*$")
    ignored_patterns = r"\b(total|subtotal|tax|change|amount|balance|gratuity|tip|service charge|cash|card)\b"
    for line in lines:
        if re.search(ignored_patterns, line, re.I):
            continue
        m = price_re.search(line)
        if m:
            price = m.group(1).replace(',', '')
            name = price_re.sub('', line).strip(' -:\t')
            name = re.sub(r"^[\W_]+|[\W_]+$", "", name)
            if len(re.sub(r"[^A-Za-z]", "", name)) < 2:
                continue
            if re.search(r"\b(gratuity|tip|service\s*charge|tax)\b", name, re.I):
                continue
            items.append({'name': name, 'price': price})
    return items
