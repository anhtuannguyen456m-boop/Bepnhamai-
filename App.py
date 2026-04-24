import streamlit as st
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import io

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def extract_text(img):
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return pytesseract.image_to_string(thresh)

def parse(text):
    data = {"items": []}

    m = re.search(r'\d{2}/\d{2}/\d{4}.*\d{2}:\d{2}', text)
    data["time"] = m.group() if m else ""

    m = re.search(r'Khách hàng[:\s]+(.+)', text)
    data["customer"] = m.group(1) if m else ""

    for line in text.split("\n"):
        if "x" in line:
            price = re.search(r'(\d{1,3}\.\d{3})', line)
            data["items"].append({
                "name": line.strip(),
                "price": price.group(1) if price else "0"
            })

    return data

def draw(data):
    img = Image.new("L", (420, 900), 255)
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", 22)
    except:
        font = ImageFont.load_default()

    y = 20
    d.text((100, y), "BẾP NHÀ MAI", font=font, fill=0)
    y += 40

    d.text((20, y), data["time"], font=font, fill=0)
    y += 30
    d.text((20, y), "KH: " + data["customer"], font=font, fill=0)
    y += 30

    total = 0

    for item in data["items"]:
        d.text((20, y), item["name"], font=font, fill=0)
        y += 25
        d.text((250, y), item["price"] + "đ", font=font, fill=0)
        y += 30

        try:
            total += int(item["price"].replace(".", ""))
        except:
            pass

    y += 20
    total_text = f"{total:,}".replace(",", ".") + "đ"
    d.text((20, y), "TỔNG:", font=font, fill=0)
    d.text((250, y), total_text, font=font, fill=0)

    return img

st.title("🧾 Receipt Generator")

uploaded = st.file_uploader("Upload ảnh", type=["jpg", "png"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img)

    if st.button("Đọc dữ liệu"):
        text = extract_text(img)
        data = parse(text)
        st.session_state["data"] = data

if "data" in st.session_state:
    data = st.session_state["data"]

    data["time"] = st.text_input("Thời gian", data.get("time", ""))
    data["customer"] = st.text_input("Khách hàng", data.get("customer", ""))

    new_items = []
    for i, item in enumerate(data["items"]):
        name = st.text_input(f"Tên món {i}", item["name"])
        price = st.text_input(f"Giá {i}", item["price"])
        new_items.append({"name": name, "price": price})

    data["items"] = new_items

    img = draw(data)
    st.image(img)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    st.download_button("Tải ảnh", buf.getvalue(), "receipt.png")
