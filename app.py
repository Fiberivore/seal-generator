import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import math
import io
import os
import requests
import re

# ==========================================
# 🌍 语言包配置 (Localization)
# ==========================================
LANG = {
    "CN": {
        "title": "🇺🇸 美国公司印章生成器",
        "header_input": "1. 输入信息",
        "header_preview": "2. 预览与下载",
        "lbl_name": "公司名称",
        "lbl_state": "注册州名 (自动添加 STATE OF)",
        "lbl_reg": "注册号 (无需输入 No.)",
        "lbl_color": "印章颜色",
        "btn_generate": "生成印章",
        "btn_download": "⬇️ 下载 PNG 印章",
        "loading": "正在排版绘制...",
        "info_start": "👈 请在左侧输入信息，并按回车键预览。",
        "warn_disclaimer": "仅供设计预览与内部存档使用。请勿用于非法用途。",
        "toggle_lang": "Switch to English",
        "ph_name": "EXAMPLE COMPANY LLC",
        "ph_state": "FLORIDA",
        "ph_reg": "12345678",
        "help_enter": "💡 修改内容后，请按键盘【回车键 (Enter)】刷新右侧预览图"
    },
    "EN": {
        "title": "🇺🇸 US Corporate Seal Generator",
        "header_input": "1. Input Details",
        "header_preview": "2. Preview & Download",
        "lbl_name": "Company Name",
        "lbl_state": "State Name (Auto adds 'STATE OF')",
        "lbl_reg": "Registration No. (No prefix needed)",
        "lbl_color": "Seal Color",
        "btn_generate": "Generate Seal",
        "btn_download": "⬇️ Download PNG",
        "loading": "Rendering seal...",
        "info_start": "👈 Please enter details on the left to start.",
        "warn_disclaimer": "For design preview and internal archiving only. Do not use for illegal purposes.",
        "toggle_lang": "切换到中文",
        "ph_name": "EXAMPLE COMPANY LLC",
        "ph_state": "FLORIDA",
        "ph_reg": "12345678",
        "help_enter": "Press Enter to apply changes"
    }
}

# ==========================================
# 🛠️ 核心绘图逻辑
# ==========================================

def load_font():
    """智能字体加载器"""
    system_paths = [
        "/System/Library/Fonts/Times.ttc",
        "/Library/Fonts/Times New Roman.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/georgia.ttf"
    ]
    for path in system_paths:
        if os.path.exists(path): return path
        
    local_paths = ["times.ttf", "Times New Roman.ttf", "Tinos-Bold.ttf"]
    for name in local_paths:
        if os.path.exists(name): return name

    font_url = "https://github.com/google/fonts/raw/main/ofl/tinos/Tinos-Bold.ttf"
    local_font_name = "Tinos-Bold.ttf"
    try:
        if not os.path.exists(local_font_name):
            r = requests.get(font_url, timeout=5)
            with open(local_font_name, 'wb') as f:
                f.write(r.content)
        return local_font_name
    except:
        return None

def get_font(path, size):
    try:
        return ImageFont.truetype(path, int(size)) if path else ImageFont.load_default()
    except:
        return ImageFont.load_default()

def draw_radial_dashes(draw, center, inner_r, outer_r, num_dashes, width, fill):
    for i in range(num_dashes):
        angle = math.radians(i * (360 / num_dashes))
        draw.line([
            (center[0] + inner_r * math.cos(angle), center[1] + inner_r * math.sin(angle)),
            (center[0] + outer_r * math.cos(angle), center[1] + outer_r * math.sin(angle))
        ], fill=fill, width=int(width))

def draw_dashed_ring(draw, center, radius, width, dash_len, gap_len, fill):
    circumference = 2 * math.pi * radius
    num_dashes = int(circumference / (dash_len + gap_len))
    angle_step = 360 / num_dashes
    for i in range(num_dashes):
        start = i * angle_step
        end = start + (dash_len / circumference) * 360
        draw.arc([center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius], 
                 start=start, end=end, fill=fill, width=int(width))

def draw_curved_text_precise(img, text, font_path, initial_size, center, radius, is_top, fill, max_arc_angle=150):
    """弧形文字绘制（带自动缩放）"""
    if not text: return
    draw = ImageDraw.Draw(img)
    circumference = 2 * math.pi * radius
    
    current_size = initial_size
    min_size = initial_size * 0.3
    font = None
    char_widths = []
    spacing = 0
    total_angle = 0

    while current_size >= min_size:
        font = get_font(font_path, current_size)
        char_widths = []
        for char in text:
            bbox = draw.textbbox((0, 0), char, font=font)
            char_widths.append(bbox[2] - bbox[0])
            
        spacing = current_size * 0.15
        total_arc_length = sum(char_widths) + spacing * (len(text) - 1)
        total_angle = (total_arc_length / circumference) * 360

        if total_angle <= max_arc_angle:
            break 
        current_size -= 2

    if font is None: font = get_font(font_path, current_size)

    if is_top:
        current_angle = -90 - (total_angle / 2)
    else:
        current_angle = 90 + (total_angle / 2)

    for i, char in enumerate(text):
        char_width = char_widths[i]
        char_angle_span = (char_width / circumference) * 360
        
        if is_top:
            angle = current_angle + char_angle_span / 2
            rotation = angle + 90
        else:
            angle = current_angle - char_angle_span / 2
            rotation = angle - 90

        rad_angle = math.radians(angle)
        x = center[0] + radius * math.cos(rad_angle)
        y = center[1] + radius * math.sin(rad_angle)

        s = int(font.size * 3)
        char_img = Image.new('RGBA', (s, s), (0,0,0,0))
        cd = ImageDraw.Draw(char_img)
        bbox = cd.textbbox((0,0), char, font=font)
        w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        
        cd.text(((s-w)/2 - bbox[0], (s-h)/2 - bbox[1]), char, font=font, fill=fill)
        rotated = char_img.rotate(-rotation, resample=Image.BICUBIC, expand=True)
        img.paste(rotated, (int(x - rotated.width/2), int(y - rotated.height/2)), rotated)
        
        angle_step = ((char_width + spacing) / circumference) * 360
        if is_top:
            current_angle += angle_step
        else:
            current_angle -= angle_step

def draw_straight_text_autosize(draw, text, font_path, max_width, initial_size, y_center, center_x, fill):
    """
    直线文字绘制，带自动缩放功能。
    """
    if not text: return
    current_size = initial_size
    min_size = 10 
    font = None
    
    while current_size >= min_size:
        font = get_font(font_path, current_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            break
        current_size -= 2
        
    if font is None: font = get_font(font_path, min_size)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text((center_x - text_width / 2, y_center - text_height / 2), text, font=font, fill=fill)


def create_seal_image(company, state_input, reg_no, color_hex):
    base_size = 500
    scale = 2 
    canvas_size = base_size * scale
    center = (canvas_size / 2, canvas_size / 2)
    
    img = Image.new('RGBA', (canvas_size, canvas_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    fill = ImageColor.getrgb(color_hex)
    font_path = load_font()

    # --- 📐 参数调整区 ---
    size_seal = 75 * scale 
    size_inner_arc_text = 90 * scale 
    size_outer_text = 75 * scale 
    size_reg = 50 * scale 

    # --- 1. 绘制边框 ---
    draw_radial_dashes(draw, center, canvas_size*0.44, canvas_size*0.48, 120, 4*scale, fill)
    r_inner_ring = canvas_size*0.32
    draw_dashed_ring(draw, center, r_inner_ring, 3*scale, 15*scale, 12*scale, fill)
    
    # --- 2. 外部圆弧文字 ---
    text_r = canvas_size * 0.39 
    
    clean_state = state_input.strip().upper()
    if clean_state and not clean_state.startswith("STATE OF"):
        final_state_text = f"STATE OF {clean_state}"
    else:
        final_state_text = clean_state

    draw_curved_text_precise(img, company.upper(), font_path, size_outer_text, center, text_r, True, fill, max_arc_angle=150)
    draw_curved_text_precise(img, final_state_text, font_path, size_outer_text, center, text_r, False, fill, max_arc_angle=150)

    # --- 3. 内部圆弧文字 (LLC放大版) ---
    clean_name = company.strip().upper()
    if clean_name.endswith("LLC") or clean_name.endswith("L.L.C.") or clean_name.endswith("L.L.C"):
        inner_top_text = "LIMITED LIABILITY COMPANY"
    else:
        inner_top_text = "CORPORATE"
    
    inner_text_r = canvas_size * 0.25
    draw_curved_text_precise(img, inner_top_text, font_path, size_inner_arc_text, center, inner_text_r, True, fill, max_arc_angle=160)

    # --- 4. 中间 SEAL 文字 (绝对居中) ---
    f_seal = get_font(font_path, size_seal)
    bbox = draw.textbbox((0,0), "SEAL", font=f_seal)
    w_seal = bbox[2]-bbox[0]
    h_seal = bbox[3]-bbox[1]
    
    # 🔥🔥🔥 修正：绝对垂直居中，移除偏移量 🔥🔥🔥
    # 原来是 center[1] - h/2 + 25，现在直接 center[1] - h/2
    draw.text((center[0]-w_seal/2, center[1] - h_seal/2), "SEAL", font=f_seal, fill=fill)

    # --- 5. 注册号 ---
    if reg_no:
        reg_str = str(reg_no).strip()
        if not re.match(r'^no[\.\s]', reg_str, re.IGNORECASE):
            final_reg = f"No. {reg_str}"
        else:
            final_reg = reg_str
            
        max_reg_width = (r_inner_ring * 2) * 0.70
        y_pos = center[1] + (95 * scale)
        draw_straight_text_autosize(draw, final_reg, font_path, max_reg_width, size_reg, y_pos, center[0], fill)

    return img.resize((base_size, base_size), resample=Image.LANCZOS)

# ==========================================
# 🎨 网页界面 (UI)
# ==========================================

st.set_page_config(page_title="Seal Generator", page_icon="🔏", layout="centered")

if 'lang' not in st.session_state:
    st.session_state.lang = 'CN'

def toggle_language():
    st.session_state.lang = 'EN' if st.session_state.lang == 'CN' else 'CN'

txt = LANG[st.session_state.lang]

t_col1, t_col2 = st.columns([3, 1])
with t_col1:
    st.title(txt["title"])
with t_col2:
    st.button(txt["toggle_lang"], on_click=toggle_language, use_container_width=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader(txt["header_input"])
    name = st.text_input(txt["lbl_name"], txt["ph_name"], help=txt["help_enter"])
    state = st.text_input(txt["lbl_state"], txt["ph_state"], help=txt["help_enter"])
    reg_no = st.text_input(txt["lbl_reg"], txt["ph_reg"], help=txt["help_enter"])
    color = st.color_picker(txt["lbl_color"], "#2C3E50")

with col2:
    st.subheader(txt["header_preview"])
    if name and state:
        with st.spinner(txt["loading"]):
            try:
                img = create_seal_image(name, state, reg_no, color)
                st.markdown("""<style>[data-testid="stImage"]{background:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PGcmaWxsPSIjZjBmMGYwIj48cmVjdCB3aWR0aD0iMTAiIGhlaWdodD0iMTAiLz48cmVjdCB4PSIxMCIgeT0iMTAiIHdpZHRoPSIxMCIgaGVpZ2h0PSIxMCIvPjwvZz48L3N2Zz4=");border-radius:8px;}</style>""", unsafe_allow_html=True)
                st.image(img, use_container_width=True)
                
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                filename = f"Seal_{name.split()[0]}.png"
                
                st.download_button(
                    label=txt["btn_download"],
                    data=buf.getvalue(),
                    file_name=filename,
                    mime="image/png",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info(txt["info_start"])

st.markdown("---")
st.caption(txt["warn_disclaimer"])