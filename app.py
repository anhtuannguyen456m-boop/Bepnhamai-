import streamlit as st
import pytesseract
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import re
import io
import random

# ===== CONFIG =====
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# ===== OCR =====
def extract_text(img):
    return pytesseract.image_to_string(img)

# ===== PARSE =====
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


# ===== DRAW REALISTIC RECEIPT =====
def draw_realistic(data):
    width, height = 500, 900
    paper = Image.new("RGB", (width, height), (250, 250, 245))
    draw = ImageDraw.Draw(paper)

    # fonts
    try:
        font_main = ImageFont.truetype("DejaVuSansMono.ttf", 22)
        font_small = ImageFont.truetype("DejaVuSansMono.ttf", 18)
        font_big = ImageFont.truetype("DejaVuSansMono.ttf", 26)
    except:
        font_main = font_small = font_big = ImageFont.load_default()

    y = 30

    # header
    draw.text((120, y), "BẾP NHÀ MAI", fill=(0,0,0), font=font_big)
    y += 50

    draw.text((20, y), data.get("time",""), fill=(0,0,0), font=font_main)
    y += 30

    draw.text((20, y), "KH: " + data.get("customer",""), fill=(0,0,0), font=font_main)
    y += 40

    total = 0

    # items
    for item in data["items"]:
        name = item["name"]
        price = item["price"]

        # tách note
        if '"' in name:
            parts = name.split('"')
            main = parts[0]
            note = '"' + parts[1] + '"'
        else:
            main = name
            note = ""

        # tên món
        draw.text((20, y), main.strip(), fill=(0,0,0), font=font_main)
        y += 25

        # note nhỏ hơn
        if note:
            draw.text((30, y), note.strip(), fill=(80,80,80), font=font_small)
            y += 25

        # giá
        draw.text((320, y-25), price + "đ", fill=(0,0,0), font=font_main)

        y += 20

        try:
            total += int(price.replace(".", ""))
        except:
            pass

    # total
    y += 20
    total_text = f"{total:,}".replace(",", ".") + "đ"

    draw.text((20, y), "TỔNG:", fill=(0,0,0), font=font_big)
    draw.text((300, y), total_text, fill=(0,0,0), font=font_big)

    # ===== EFFECT NHẸ (KHÔNG MỜ CHỮ) =====
    paper = paper.filter(ImageFilter.GaussianBlur(0.3))

    # rotate nhẹ
    angle = random.uniform(-1.5, 1.5)
    paper = paper.rotate(angle, expand=True, fillcolor=(200,200,200))

    # nền gỗ
    bg = Image.new("RGB", (900, 1200), (130, 90, 60))

    # shadow
    shadow = Image.new("RGBA", paper.size, (0,0,0,60))
    bg.paste(shadow, (180+8, 200+8), shadow)

    # dán giấy
    bg.paste(paper, (180, 200))

    return bg


# ===== UI =====
st.title("🧾 Receipt Generator PRO")

uploaded = st.file_uploader("Upload ảnh đơn hàng", type=["jpg", "png"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Ảnh gốc")

    if st.button("Đọc dữ liệu"):
        text = extract_text(img)
        data = parse(text)
        st.session_state["data"] = data


# ===== EDIT =====
if "data" in st.session_state:
    data = st.session_state["data"]

    data["time"] = st.text_input("Thời gian", data.get("time",""))
    data["customer"] = st.text_input("Khách hàng", data.get("customer",""))

    st.subheader("Danh sách món")

    new_items = []
    for i, item in enumerate(data["items"]):
        col1, col2 = st.columns([3,1])
        name = col1.text_input(f"Món {i}", item["name"])
        price = col2.text_input(f"Giá {i}", item["price"])
        new_items.append({"name": name, "price": price})

    if st.button("➕ Thêm món"):
        new_items.append({"name": "", "price": "0"})

    data["items"] = new_items

    # ===== PREVIEW =====
    st.subheader("Xem trước")

    img = draw_realistic(data)
    st.image(img, width=300)

    # ===== DOWNLOAD =====
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    st.download_button(
        "📥 Tải hoá đơn",
        data=buf.getvalue(),
        file_name="receipt.png",
        mime="image/png"
  )
