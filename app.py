import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import math
import io
import os
import re

# ==========================================
# 🌍 语言包配置
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
        "btn_download": "⬇️ 下载 PNG 印章",
        "loading": "正在排版绘制...",
        "info_start": "👈 请在左侧输入信息，并按回车键预览。",
        "toggle_lang": "Switch to English",
        "ph_name": "EXAMPLE COMPANY LLC",
        "ph_state": "FLORIDA",
        "ph_reg": "12345678",
        "help_enter": "💡 修改内容后，请按键盘【回车键 (Enter)】刷新右侧预览图",
        "font_error": "⚠️ 严重错误：未找到字体文件！请确保 'Tinos-Bold.ttf' 已上传到 GitHub 项目根目录。",
        
        "usage_title": "📖 使用说明",
        # 🔥 修改：使用 HTML 列表标签优化排版，实现自动换行和编号
        "usage_content": """
        <ol style="margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 10px;">美国没有所谓“公章”，所以公司印章没有固定模版，印章样式、颜色、尺寸，均可按照自己的喜欢设计。</li>
            <li style="margin-bottom: 10px;">如果是正式文书，一般以公司负责人的亲笔签字为准。</li>
            <li style="margin-bottom: 10px;">不同于国内，美国那边觉得公章可以造假，签字不容易伪造，而且不能确定责任，因为理论上任何人都可以拿公章来盖章，而签字只有本人才可以。</li>
            <li>所以相对于印章，美国更加注重签字。</li>
        </ol>
        """,
        "copyright": "© <a href='https://www.meisitongllc.com/' target='_blank' rel='nofollow' style='color: inherit; text-decoration: none; border-bottom: 1px dotted #aaa;'>美司通</a> www.meisitongllc.com 版权所有"
    },
    "EN": {
        "title": "🇺🇸 US Corporate Seal Generator",
        "header_input": "1. Input Details",
        "header_preview": "2. Preview & Download",
        "lbl_name": "Company Name",
        "lbl_state": "State Name (Auto adds 'STATE OF')",
        "lbl_reg": "Registration No. (No prefix needed)",
        "lbl_color": "Seal Color",
        "btn_download": "⬇️ Download PNG",
        "loading": "Rendering seal...",
        "info_start": "👈 Please enter details on the left to start.",
        "toggle_lang": "切换到中文",
        "ph_name": "EXAMPLE COMPANY LLC",
        "ph_state": "FLORIDA",
        "ph_reg": "12345678",
        "help_enter": "Press Enter to apply changes",
        "font_error": "⚠️ CRITICAL ERROR: Font file not found! Please ensure 'Tinos-Bold.ttf' is uploaded to the GitHub root directory.",
        
        "usage_title": "📖 Usage Guide",
        # 🔥 Change: Using HTML ordered lists for better formatting
        "usage_content": """
        <ol style="margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 10px;">In the US, there is no strict legal template for a "corporate seal." You can customize the design, color, and size freely.</li>
            <li style="margin-bottom: 10px;">For formal documents, the authorized officer's signature is the primary binding factor.</li>
            <li style="margin-bottom: 10px;">Unlike in some regions, seals are considered easier to forge than signatures. US law prioritizes personal accountability through signatures.</li>
            <li>Therefore, signatures carry more weight than seals in US business practices.</li>
        </ol>
        """,
        "copyright": "© <a href='https://www.meisitongllc.com/' target='_blank' rel='nofollow' style='color: inherit; text-decoration: none; border-bottom: 1px dotted #aaa;'>Meisitong</a> www.meisitongllc.com All Rights Reserved"
    }
}

# ==========================================
# 🛠️ 核心绘图逻辑 (保持不变)
# ==========================================

# 定义我们打包上传的字体文件名
BUNDLED_FONT_NAME = "Tinos-Bold.ttf"

@st.cache_resource
def get_font_path():
    """简单直接的字体检查"""
    if os.path.exists(BUNDLED_FONT_NAME):
        return BUNDLED_FONT_NAME
    else:
        return None

def get_font(path, size):
    try:
        if path:
            return ImageFont.truetype(path, int(size))
        else:
            return ImageFont.load_default()
    except Exception:
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
    
    font_path = get_font_path()

    # 参数
    size_seal = 75 * scale 
    size_inner_arc_text = 90 * scale 
    size_outer_text = 75 * scale 
    size_reg = 50 * scale 

    # 1. 边框
    draw_radial_dashes(draw, center, canvas_size*0.44, canvas_size*0.48, 120, 4*scale, fill)
    r_inner_ring = canvas_size*0.32
    draw_dashed_ring(draw, center, r_inner_ring, 3*scale, 15*scale, 12*scale, fill)
    
    # 2. 外部圆弧
    text_r = canvas_size * 0.39 
    clean_state = state_input.strip().upper()
    if clean_state and not clean_state.startswith("STATE OF"):
        final_state_text = f"STATE OF {clean_state}"
    else:
        final_state_text = clean_state

    draw_curved_text_precise(img, company.upper(), font_path, size_outer_text, center, text_r, True, fill, max_arc_angle=150)
    draw_curved_text_precise(img, final_state_text, font_path, size_outer_text, center, text_r, False, fill, max_arc_angle=150)

    # 3. 内部圆弧
    clean_name = company.strip().upper()
    if clean_name.endswith("LLC") or clean_name.endswith("L.L.C.") or clean_name.endswith("L.L.C"):
        inner_top_text = "LIMITED LIABILITY COMPANY"
    else:
        inner_top_text = "CORPORATE"
    
    inner_text_r = canvas_size * 0.25
    draw_curved_text_precise(img, inner_top_text, font_path, size_inner_arc_text, center, inner_text_r, True, fill, max_arc_angle=160)

    # 4. SEAL (绝对居中)
    f_seal = get_font(font_path, size_seal)
    bbox = draw.textbbox((0,0), "SEAL", font=f_seal)
    w_seal = bbox[2]-bbox[0]
    h_seal = bbox[3]-bbox[1]
    draw.text((center[0]-w_seal/2, center[1] - h_seal/2), "SEAL", font=f_seal, fill=fill)

    # 5. 注册号
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
# 🎨 UI
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

# 字体检查
font_path_check = get_font_path()
if not font_path_check:
    st.error(txt["font_error"])
    st.stop()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader(txt["header_input"])
    name = st.text_input(txt["lbl_name"], txt["ph_name"], help=txt["help_enter"])
    state = st.text_input(txt["lbl_state"], "FLORIDA", help=txt["help_enter"])
    reg_no = st.text_input(txt["lbl_reg"], "12345678", help=txt["help_enter"])
    color = st.color_picker(txt["lbl_color"], "#2C3E50")

with col2:
    st.subheader(txt["header_preview"])
    if name and state:
        with st.spinner(txt["loading"]):
            try:
                img = create_seal_image(name, state, reg_no, color)
                # 使用灰色网格背景展示透明度
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

# 📄 使用说明板块
with st.container():
    st.markdown(f"#### {txt['usage_title']}")
    # 使用灰色小字排版 + HTML 有序列表
    st.markdown(f"""
    <div style="color: #666; font-size: 0.9em; line-height: 1.6; background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
    {txt['usage_content']}
    </div>
    """, unsafe_allow_html=True)

# 🏢 版权信息 (包含 nofollow 链接)
st.markdown(f"""
<div style="text-align: center; margin-top: 40px; color: #aaa; font-size: 0.8em; border-top: 1px solid #eee; padding-top: 20px;">
{txt['copyright']}
</div>
""", unsafe_allow_html=True)
