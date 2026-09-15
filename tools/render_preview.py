# -*- coding: utf-8 -*-
"""渲染 Kindle PW3 (1072x1448) 模拟图，复刻 main.lua showDashboard 布局（col2full 版）。
- 模块标题粗体（bold=True 用合成粗体，加 msyhbd.ttf）
- 中线对齐：col2full padText 拼接（左列补宽 + 2空格 + 右列），视觉上两列中线分
- 撑满屏：动态 padding/margin
"""
import sys, os, json, urllib.request, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kindle_preview import build_modules, choose_size, SCREEN_W, SCREEN_H, PAD, SCALE, MIN_LINES_PER_MODULE
from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = r"C:/Windows/Fonts/msyh.ttc"
FONT_BOLD    = r"C:/Windows/Fonts/msyhbd.ttc"

def load_font(path, size):
    if os.path.exists(path):
        try: return ImageFont.truetype(path, size)
        except Exception: pass
    return ImageFont.load_default()

def main():
    d = json.load(urllib.request.urlopen("http://127.0.0.1:8787/api/dashboard", timeout=20))
    availW = SCREEN_W - 2 * PAD
    availH = SCREEN_H - 2 * PAD
    sz, colw, tbw = choose_size(d, availW, availH)
    mods = build_modules(d, colw)

    physSz = math.ceil(sz * SCALE)
    titlePhysSz = math.ceil((sz + 2) * SCALE)
    mainTitlePhysSz = math.ceil((sz + 4) * SCALE)
    lineH = math.ceil(physSz * 1.3)  # 实际渲染行高
    titleH = math.ceil(titlePhysSz * 1.3)
    mainTitleH = math.ceil(mainTitlePhysSz * 1.3)
    # 固定 padding/margin（与 main.lua 一致，不再撑满屏）
    modMargin = 4
    modPadding = 6
    minLines = MIN_LINES_PER_MODULE

    img = Image.new("RGB", (SCREEN_W, SCREEN_H), "white")
    draw = ImageDraw.Draw(img)
    font_body = load_font(FONT_REGULAR, physSz)
    font_title = load_font(FONT_BOLD, titlePhysSz)
    font_main = load_font(FONT_BOLD, mainTitlePhysSz)

    y = PAD
    draw.text((PAD, y), "DayPane", fill="black", font=font_main)
    y += mainTitleH + 8

    for m in mods:
        eff_lines = max(len(m["lines"]), minLines)
        mod_lines_h = titleH + eff_lines * lineH
        frame_h = mod_lines_h + 2 * (modPadding + 1)
        x0 = PAD; x1 = SCREEN_W - PAD
        y += modMargin
        draw.rectangle([x0, y, x1, y + frame_h], outline="black", width=1)
        ty = y + modPadding + 1
        # 标题：粗体
        draw.text((x0 + modPadding + 1, ty), m["title"], fill="black", font=font_title)
        ty += titleH  # 标题占 1 行（用更大字号行高）
        # 内容行
        for line in m["lines"]:
            draw.text((x0 + modPadding + 1, ty), line, fill="black", font=font_body)
            ty += lineH
        # 预留空行（不足 minLines 补空行）
        for _ in range(max(0, minLines - len(m["lines"]))):
            ty += lineH  # 空行占位
        y += frame_h + modMargin

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kindle_preview.png")
    img.save(out)
    print(f"已生成: {out} ({SCREEN_W}x{SCREEN_H}, 字号 {sz}/物理{physSz}, colw={colw}, padding {modPadding}/margin {modMargin})")

if __name__ == "__main__":
    main()
