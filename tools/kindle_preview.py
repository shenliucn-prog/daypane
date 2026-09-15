# -*- coding: utf-8 -*-
"""模拟 Kindle PW3 实际渲染（从 E 盘 KOReader 源码反推的真实参数）。

关键事实（E 盘源码实测）：
- KOReader self.ui.dimen 在 PW3 上 = 物理像素 1072×1448
- framebuffer.lua scaleBySize(px) = ceil(px*(size_scale+dpi_scale)/2)，
  无 dpi_override 时 size_scale = dpi_scale = 1072/600 = 1.7867
- textboxwidget.lua:151 line_height_px = round(1.3 * face.size)
- 加粗：传 ffont face + bold=true（KOReader 合成粗体）
- 中线对齐：HorizontalGroup 无子 widget 水平对齐机制，回退到 col2full + padText 拼接
"""
import json, urllib.request, math, sys

SCREEN_W, SCREEN_H = 1072, 1448  # PW3 物理像素
PAD = 8                            # 屏外边距
SCALE = 1072 / 600                 # = 1.7867，Screen:scaleBySize 系数
SIZES = (26, 24, 22, 20, 18, 16)
MIN_LINES_PER_MODULE = 2           # 每模块至少占 2 行内容（不足补空行）

def num(v, d=None):
    if v is None: return "n/a"
    if d is not None: return ("%%.%df" % d) % v
    return str(v)

def wc_for(phys_sz, s):
    """按物理字号 phys_sz 估算像素宽：CJK=phys_sz，ASCII=phys_sz/2。"""
    w = 0
    half = phys_sz / 2.0
    for ch in s:
        w += half if ord(ch) < 128 else phys_sz
    return w

def price_text(v):
    if v is None: return "?"
    return num(v, 1 if v >= 1000 else 2)

def stock_cell(s):
    mkt = "美" if s.get("mkt") == "US" else ("A" if s.get("mkt") == "A" else " ")
    sign = "" if s.get("changePct") is None else ("+" if s.get("changePct") >= 0 else "-")
    p = "" if s.get("changePct") is None else ("%.1f%%" % abs(s.get("changePct")))
    return "%s %s %s %s%s" % (mkt, s.get("label", s.get("sym")), price_text(s.get("price")), sign, p)

def clock_cell(c):
    return "%s %s %s" % (c.get("city"), c.get("time"), c.get("date"))

def pad_text(s, width):
    """中英文混排宽度补空格（中文按 2 格）。"""
    n = sum(1 if ord(c) < 128 else 2 for c in s)
    return s + " " * max(0, width - n)

def build_modules(d, colw):
    """复刻 main.lua buildModules + col2full，返回结构化模块 [{title, lines}]。
    lines 里是最终拼好文本（含 padText 双列）。"""
    q = d.get("quotas", {}); w = d.get("weather", {})
    st = d.get("stocks", {}).get("items", [])
    fx = d.get("fx", {}); cl = d.get("clocks", {}).get("items", [])

    tok = []
    wb = q.get("workbuddy", {})
    if wb.get("ok"):
        t = wb.get("token", {})
        tok.append("WorkBuddy %s/%s (%d%%)" % (t.get("remaining", "?"), t.get("size", "?"), t.get("percent") or 0))
    else:
        tok.append("WorkBuddy 不可用")
    cc = q.get("claudecode", {}); cx = q.get("codex", {})
    tok.append(pad_text("ClaudeCode %s/%s" % (cc.get("used7d", "?"), cc.get("cap", "?")), colw)
              + "  " + "Codex %s/%s" % (cx.get("used7d", "?"), cx.get("cap", "?")))

    wea = []
    if w.get("ok"):
        wea.append("%s  %s %s°C  高%s 低%s 湿%s%%" % (
            w.get("city", ""), w.get("text", ""), w.get("temp", "?"),
            w.get("high", "?"), w.get("low", "?"), w.get("humidity", "?")))
    else:
        wea.append("天气 不可用")

    stk = []
    for i in range(0, len(st), 2):
        left = stock_cell(st[i])
        right = stock_cell(st[i + 1]) if i + 1 < len(st) else ""
        stk.append(pad_text(left, colw) + "  " + right)

    fxx = [pad_text("CNY " + num(fx.get("cny"), 3), colw) + "  INR " + num(fx.get("inr"), 3)]

    clk = []
    for i in range(0, len(cl), 2):
        left = clock_cell(cl[i])
        right = clock_cell(cl[i + 1]) if i + 1 < len(cl) else ""
        clk.append(pad_text(left, colw) + "  " + right)

    upd = ["更新 %s  顶部下滑返回" % "17:08:17"]

    return [
        {"title": "Token Usage", "lines": tok},
        {"title": "天气",        "lines": wea},
        {"title": "股市",        "lines": stk},
        {"title": "汇率",        "lines": fxx},
        {"title": "时钟",        "lines": clk},
        {"title": "更新",        "lines": upd},
    ]

def choose_size(d, availW, availH):
    """复刻 main.lua chooseSize。精确行高 1.3，模块开销 22，安全缓冲 40。"""
    tbw = availW - 4
    for sz in SIZES:
        phys_sz = math.ceil(sz * SCALE)
        title_phys_sz = math.ceil((sz + 2) * SCALE)
        main_title_phys_sz = math.ceil((sz + 4) * SCALE)
        phys_half = phys_sz / 2
        colw = int((tbw - phys_half) / (2 * phys_half))
        mods = build_modules(d, colw)
        ok = True
        if wc_for(main_title_phys_sz, "DayPane") > tbw:
            ok = False
        for m in mods:
            if not ok: break
            if wc_for(title_phys_sz, m["title"]) > tbw:
                ok = False; break
            for line in m["lines"]:
                if wc_for(phys_sz, line) > tbw:
                    ok = False; break
            if not ok: break
        if ok:
            lineH = math.ceil(phys_sz * 1.3)
            titleH = math.ceil(title_phys_sz * 1.3)
            mainTitleH = math.ceil(main_title_phys_sz * 1.3)
            totalH = mainTitleH
            for m in mods:
                totalH += titleH + max(len(m["lines"]), MIN_LINES_PER_MODULE) * lineH
            totalH += len(mods) * 22 + 40
            if totalH <= availH:
                return sz, colw, tbw
    return SIZES[-1], colw, tbw

def main():
    if len(sys.argv) > 1:
        d = json.load(open(sys.argv[1], encoding="utf-8"))
    else:
        d = json.load(urllib.request.urlopen("http://127.0.0.1:8787/api/dashboard", timeout=20))
    availW = SCREEN_W - 2 * PAD
    availH = SCREEN_H - 2 * PAD
    sz, colw, tbw = choose_size(d, availW, availH)
    mods = build_modules(d, colw)
    phys_sz = math.ceil(sz * SCALE)
    title_phys_sz = math.ceil((sz + 2) * SCALE)
    main_title_phys_sz = math.ceil((sz + 4) * SCALE)
    lineH = math.ceil(phys_sz * 1.3)
    titleH = math.ceil(title_phys_sz * 1.3)
    mainTitleH = math.ceil(main_title_phys_sz * 1.3)
    total_lines = 1
    for m in mods:
        total_lines += 1 + max(len(m["lines"]), MIN_LINES_PER_MODULE)
    totalH = mainTitleH
    for m in mods:
        totalH += titleH + max(len(m["lines"]), MIN_LINES_PER_MODULE) * lineH
    totalH += len(mods) * 22 + 40
    print("=== 排版检查 (屏 %dx%d, 字号 %d/物理%d, colw=%d单位, 可用 %dx%d) ===" % (
        SCREEN_W, SCREEN_H, sz, phys_sz, colw, availW, availH))
    warn = 0
    for m in mods:
        print("┌─ %s ─┐ (标题粗体)" % m["title"])
        if wc_for(title_phys_sz, m["title"]) > tbw:
            warn += 1; print("  !! 标题超宽")
        for line in m["lines"]:
            w = wc_for(phys_sz, line)
            status = "OK" if w <= tbw else "!! 超宽 %dpx" % (w - tbw)
            if w > tbw: warn += 1
            print("  %-50s %6.0f  %s" % (line[:50], w, status))
    print("---")
    print("总行数: %d, 总高: %dpx, 可用高: %dpx, %s" % (
        total_lines, totalH, availH,
        "余量 %dpx" % (availH - totalH) if totalH <= availH else "!! 溢出 %dpx" % (totalH - availH)))
    print("超宽行数: %d" % warn)

if __name__ == "__main__":
    main()
