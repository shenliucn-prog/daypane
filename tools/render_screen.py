# -*- coding: utf-8 -*-
"""DayPane 整屏渲染器（PC 端出图，Kindle 端只显示）。

把 /api/dashboard JSON 渲染成 1072x1448 印刷布告栏风整屏图，
16 级灰度（GRAY=128 / LIGHT_GRAY=200）最终 Floyd-Steinberg 抖动转 1-bit PNG。
静态数据（句子库）从 data/ 读；新闻/节日/时钟/额度均由服务端提供。
"""
import sys, os, json, math, re, urllib.request, argparse
from datetime import datetime
from zoneinfo import ZoneInfo
try:
    from layout import load_layout
except ModuleNotFoundError:
    from tools.layout import load_layout
LAYOUT = None

def display_now():
    return datetime.now(ZoneInfo(LAYOUT["timezone"])) if LAYOUT and LAYOUT.get("timezone") else datetime.now()
from PIL import Image, ImageDraw, ImageFont

# Language defaults to Chinese for backward-compatible personal deployments.
LANG = 'zh'
LABELS = {
    '今日新闻 · AI': 'AI News', '新闻源暂不可用': 'News unavailable',
    'AI 额度': 'AI Activity', 'AI 额度 · 电脑离线': 'AI Activity · PC offline',
    '未安装': 'Not installed', '不可用': 'Unavailable', '天气': 'Weather',
    '天气不可用': 'Weather unavailable', '市场': 'Markets', '世界时钟': 'World Clocks',
    '时钟不可用': 'Clocks unavailable', 'MLB · 道奇 / 教士': 'MLB · LAD / SD (UTC+8)',
    '赛程暂不可用': 'Schedule unavailable', '胜': 'W', '负': 'L',
    '无近期战报': 'No recent game', '今日一句': 'Daily Thought',
    '（编辑 data/quotes.txt）': '(Edit data/quotes.en.txt)',
}
CITY_EN = {'深圳':'Shenzhen', '伦敦':'London', '洛杉矶':'Los Angeles', '纽约':'New York', '德里':'Delhi'}
TEAM_EN = dict(zip(
    '响尾蛇 勇士 金莺 红袜 小熊 白袜 红人 守护者 洛基 老虎 太空人 皇家 天使 道奇 马林鱼 酿酒人 双城 大都会 洋基 运动家 费城人 海盗 教士 巨人 水手 红雀 光芒 游骑兵 蓝鸟 国民'.split(),
    'ARI ATL BAL BOS CHC CWS CIN CLE COL DET HOU KC LAA LAD MIA MIL MIN NYM NYY OAK PHI PIT SD SF SEA STL TB TEX TOR WSH'.split()))
WEATHER_EN = {0:'Clear',1:'Mostly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Rime fog',
    51:'Drizzle',53:'Drizzle',55:'Drizzle',56:'Freezing drizzle',57:'Freezing drizzle',
    61:'Rain',63:'Rain',65:'Heavy rain',66:'Freezing rain',67:'Freezing rain',
    71:'Snow',73:'Snow',75:'Heavy snow',77:'Snow grains',80:'Showers',81:'Showers',82:'Heavy showers',
    85:'Snow showers',86:'Snow showers',95:'Thunderstorm',96:'Hailstorm',99:'Hailstorm'}

def tr(text):
    return LABELS.get(text, text) if LANG == 'en' else text

def localized_data(data):
    """Translate built-in labels without mutating the Chinese payload."""
    import copy
    d = copy.deepcopy(data)
    if LANG != 'en':
        return d
    d['news'] = d.get('newsEn') or {'ok': False, 'items': []}
    w = d.get('weather') or {}
    w['city'] = w.get('cityEn') or CITY_EN.get(w.get('city'), w.get('city', ''))
    w['text'] = WEATHER_EN.get(w.get('code'), 'Unknown')
    for stock in (d.get('stocks') or {}).get('items', []):
        stock['label'] = stock.get('labelEn') or stock.get('sym', '')
    for clock in (d.get('clocks') or {}).get('items', []):
        clock['city'] = clock.get('cityEn') or CITY_EN.get(clock.get('city'), clock.get('tz', '').split('/')[-1].replace('_', ' '))
        date = clock.get('date', '')
        for zh, en in zip('一二三四五六日', ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']):
            date = date.replace('周' + zh, en)
        clock['date'] = date.replace('月','/').replace('日','')
    for team in (d.get('mlb') or {}).get('items', []):
        team['cn'] = team.get('abbr', '')
        for key in ('last', 'next'):
            game = team.get(key)
            if game:
                game['opp'] = TEAM_EN.get(game.get('opp'), game.get('opp', ''))
                if game.get('live'): game['time'] = 'Live'
    return d

# ---------- 屏幕与设计常量 ----------
SCREEN_W, SCREEN_H = 1072, 1448
PAD = 40
CONTENT_W = SCREEN_W - 2 * PAD
BLACK, GRAY, LIGHT_GRAY, WHITE = 0, 128, 200, 255

# 字体：本机用微软雅黑，Linux/CI 用开源 Noto Sans CJK。
# 优先级：环境变量 > 候选路径 > 默认值。找不到时 f() 会退回 load_default（不显示中文）。
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
LINUX_REG = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
    os.path.join(_ROOT, 'fonts', 'NotoSansSC-Regular.otf'),
    os.path.join(_ROOT, 'fonts', 'NotoSansCJKsc-Regular.otf'),
]
LINUX_BOLD = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf',
    os.path.join(_ROOT, 'fonts', 'NotoSansSC-Bold.otf'),
    os.path.join(_ROOT, 'fonts', 'NotoSansCJKsc-Bold.otf'),
]
WIN_REG = r"C:/Windows/Fonts/msyh.ttc"
WIN_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"


def _pick_font(env_key, candidates, fallback):
    p = os.environ.get(env_key)
    if p and os.path.exists(p):
        return p
    for c in candidates:
        if os.path.exists(c):
            return c
    return fallback


def _font_candidates():
    if os.name == 'nt':
        return LINUX_REG + [WIN_REG], LINUX_BOLD + [WIN_BOLD]
    return LINUX_REG + [WIN_REG], LINUX_BOLD + [WIN_BOLD]


_REG_CANDS, _BOLD_CANDS = _font_candidates()
FONT_REG = _pick_font('SHAWN_FONT_REG', _REG_CANDS, WIN_REG)
FONT_BOLD = _pick_font('SHAWN_FONT_BOLD', _BOLD_CANDS, WIN_BOLD)

F_DATE = 96
F_MONTH = 46
F_TIME = 72
F_TITLE = 40
F_BIG = 56
F_BODY = 34
F_SMALL = 27
F_FOOT = 24

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, '..', 'data')

# ---------- 字体缓存 ----------
# 注意：字体加载失败绝不能静默回退 —— load_default() 渲染不出中文，
# 整屏会变成空白/方块，而在 CI 上极难察觉。这里记录状态并允许 --check-fonts 直接报错。
_fc = {}
_font_errors = []


def f(size, bold=False):
    k = (size, bold)
    if k in _fc:
        return _fc[k]
    p = FONT_BOLD if bold else FONT_REG
    try:
        _fc[k] = ImageFont.truetype(p, size)
    except Exception as e:
        msg = '字体加载失败 %s: %s -> 退回 load_default（中文会渲染不出来）' % (p, e)
        if msg not in _font_errors:
            _font_errors.append(msg)
        print('[render] ERROR ' + msg, file=sys.stderr, flush=True)
        _fc[k] = ImageFont.load_default()
    return _fc[k]


def check_fonts():
    """真正加载一次并测量中日韩字符，确认能渲染中文。返回 (ok, 详情列表)。"""
    info = []
    ok = True
    for tag, path in (('regular', FONT_REG), ('bold', FONT_BOLD)):
        if not os.path.exists(path):
            info.append('%s: 文件不存在 %s' % (tag, path))
            ok = False
            continue
        try:
            ft = ImageFont.truetype(path, 34)
        except Exception as e:
            info.append('%s: 加载失败 %s (%s)' % (tag, path, e))
            ok = False
            continue
        # 用中文实测：宽度异常小说明字形缺失（豆腐/空白）
        img = Image.new('L', (1200, 80), 255)
        d = ImageDraw.Draw(img)
        # fill 必须显式给 0：默认是白色，画在白底上会量到 0 墨迹
        d.text((0, 10), '中文测试道奇教士', font=ft, fill=0)
        bb = d.textbbox((0, 10), '中文测试道奇教士', font=ft)
        wpx = bb[2] - bb[0]
        ink = sum(1 for y in range(80) for x in range(1200) if img.load()[x, y] < 128)
        good = wpx >= 200 and ink > 200
        info.append('%s: %s  中文8字宽=%dpx 墨迹=%d  %s'
                    % (tag, os.path.basename(path), wpx, ink, 'OK' if good else '字形缺失!'))
        if not good:
            ok = False
    return ok, info

# ---------- 工具 ----------
def tw(draw, s, font):
    b = draw.textbbox((0, 0), s, font=font)
    return b[2] - b[0]

def clip(draw, s, font, max_w):
    if tw(draw, s, font) <= max_w:
        return s
    ell = '…'
    while s and tw(draw, s + ell, font) > max_w:
        s = s[:-1]
    return s + ell

# 自然断句：在标点/空格后切分（零宽 lookbehind，标点保留在前一段末尾）
_SENT_SPLIT = re.compile(r'(?<=[，,。；;！？!?、：:\s])')

def clip_sentence(draw, s, font, max_w):
    """一句话新闻截断：优先在自然标点处收尾，保证整句可读且不超页宽。

    1) 整句能放下 -> 原样返回
    2) 否则按标点分段累加，取能放下的最长前缀（结尾是标点，不再加省略号）
    3) 首段就超宽 / 断出来太短没信息量 -> 退化为硬截断加省略号
    """
    s = ' '.join((s or '').split())
    if not s:
        return s
    if tw(draw, s, font) <= max_w:
        return s
    parts = [p for p in _SENT_SPLIT.split(s) if p]
    out = ''
    idx = 0
    for i, p in enumerate(parts):
        cand = out + p
        if tw(draw, cand, font) <= max_w:
            out = cand
            idx = i + 1
        else:
            break
    # 断句结果要有足够信息量，否则宁可硬截断
    if not out or len(out.strip()) < 6:
        return clip(draw, s, font, max_w)
    # 截在逗号/顿号上、后面还有内容时，用剩余宽度把下一截填满（避免"…放榜，"这种半句）
    if idx < len(parts) and out.rstrip()[-1] not in '。！？!?':
        budget = max_w - tw(draw, out, font)
        # 至少放得下 3 个字 + 省略号，否则补进去只会得到 "To…" 这种碎片
        if budget >= 140:
            frag = clip(draw, ''.join(parts[idx:]), font, budget)
            if frag:
                out = out + frag
    return out.rstrip()

def hline(draw, y, color=GRAY, width=1):
    draw.line([(PAD, y), (SCREEN_W - PAD, y)], fill=color, width=width)

def thickline(draw, y, color=BLACK, width=4):
    draw.line([(PAD, y), (SCREEN_W - PAD, y)], fill=color, width=width)

def fnum(v):
    if v is None: return '?'
    if isinstance(v, float):
        return '%.0f' % v if abs(v) >= 1000 else '%.1f' % v
    return str(v)

def fmt_pct(v):
    if v is None: return '?'
    return '%.1f' % abs(v)

# ---------- 数据 ----------
def fetch_dashboard(url='http://127.0.0.1:8787/api/dashboard'):
    req = urllib.request.Request(url, headers={'User-Agent': 'kindle-dash/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

def load_quotes():
    p = os.path.join(DATA_DIR, 'quotes.en.txt' if LANG == 'en' else 'quotes.txt')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as source:
            return [x.strip() for x in source.read().splitlines() if x.strip()]
    return []

# ---------- 模块 ----------
def draw_header(draw, d, y):
    now = display_now()
    day = now.strftime('%d')
    wd = '一二三四五六日'[now.weekday()]
    mw = (['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][now.month-1] + ' ' + ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][now.weekday()]) if LANG == 'en' else '%d月 周%s' % (now.month, wd)
    ts = now.strftime('%H:%M')
    city = (d.get('weather') or {}).get('city') or ''
    fd = f(F_DATE, bold=True)
    draw.text((PAD, y), day, fill=BLACK, font=fd)
    dw = tw(draw, day, fd)
    draw.text((PAD + dw + 24, y + 16), mw, fill=BLACK, font=f(F_MONTH, bold=True))
    ft = f(F_TIME, bold=True)
    tw_s = tw(draw, ts, ft)
    draw.text((SCREEN_W - PAD - tw_s, y - 6), ts, fill=BLACK, font=ft)
    if city:
        fs = f(F_SMALL)
        draw.text((SCREEN_W - PAD - tw(draw, city, fs), y + F_TIME + 6), city, fill=GRAY, font=fs)
    return y + round(112 * (LAYOUT["fontScale"] if LAYOUT else 1))

def stamp_label(src):
    """把模块数据里的 fetchedAt 变成右上角的时间标注。

    stale（本次拉取失败、用的是上次成功数据）时标成「缓存 HH:MM」。
    拿不到时间就返回 None，标题栏保持原样。
    """
    if not isinstance(src, dict):
        return None
    ts = src.get('fetchedAt')
    if not ts:
        return None
    try:
        t = datetime.fromtimestamp(float(ts) / 1000.0, ZoneInfo(LAYOUT['timezone']) if LAYOUT and LAYOUT.get('timezone') else None)
    except (TypeError, ValueError, OSError, OverflowError):
        return None
    hhmm = t.strftime('%H:%M')
    return (('Cached %s' if LANG == 'en' else '缓存 %s') % hhmm) if src.get('stale') else hhmm


def draw_title(draw, y, text, src=None):
    """模块标题。传 src（该模块的数据）时，右上角显示数据的获取时间。"""
    draw.text((PAD, y), text, fill=BLACK, font=f(F_TITLE, bold=True))
    label = stamp_label(src)
    if label:
        fs = f(F_SMALL)
        # 右对齐到内容区右边界；小字按标题基线附近排，视觉上跟标题齐平
        draw.text((SCREEN_W - PAD - tw(draw, label, fs), y + (F_TITLE - F_SMALL)),
                  label, fill=GRAY, font=fs)
    return y + F_TITLE + 8

def draw_news(draw, d, y):
    """今日新闻 · AI：中文一句话，按自然标点断句，绝不超页宽"""
    y = draw_title(draw, y, tr('今日新闻 · AI'), d.get('news'))
    items = (d.get('news') or {}).get('items', [])
    ff = f(F_BODY)
    fs = f(F_SMALL)
    if not items:
        draw.text((PAD, y), tr('新闻源暂不可用'), fill=GRAY, font=fs)
        return y + F_SMALL
    n = min(len(items), 3)
    for i in range(n):
        line = '· ' + (items[i].get('title') or '')
        draw.text((PAD, y + i * (F_BODY + 8)), (clip(draw, line, ff, CONTENT_W) if LANG == 'en' else clip_sentence(draw, line, ff, CONTENT_W)),
                  fill=BLACK, font=ff)
    return y + n * (F_BODY + 8)

def draw_ai(draw, d, y):
    """AI 额度：WorkBuddy / Claude Code / Codex 三行统一度量衡"""
    # cloud 模式下若本机久未上报，标题直接点明"电脑离线"，不拿旧值假装新鲜
    title = ('AI Activity' if LANG == 'en' else 'AI 活动估算') if d.get('pcOnline', True) else ('AI Activity · PC offline' if LANG == 'en' else 'AI 活动 · 电脑离线')
    y = draw_title(draw, y, title, d.get('quotas'))
    q = d.get('quotas', {})
    rows = [
        ('WorkBuddy', q.get('workbuddy', {})),
        ('Claude Code', q.get('claudecode', {})),
        ('Codex', q.get('codex', {}))
    ]
    ff = f(F_BODY)
    fs = f(F_SMALL)
    bar_h, bar_w, gap = 10, 300, 6
    for i, (name, v) in enumerate(rows):
        ry = y + i * (F_BODY + bar_h + gap)
        draw.text((PAD, ry), name, fill=BLACK, font=ff)
        used = v.get('used') if v.get('used') is not None else v.get('used7d')
        cap = v.get('cap')
        rem = v.get('remaining')
        pct = v.get('percent')
        unit = v.get('unit') or ''
        if v.get('ok') and rem is not None and cap is not None:
            val = '%s / %s' % (fnum(rem), fnum(cap))
        elif v.get('ok'):
            val = '%s / %s' % (fnum(used), fnum(cap))
        else:
            val = tr('未安装') if v.get('error') == 'not-installed' else tr('不可用')
        # 右侧数值（剩余/总额）
        vx = SCREEN_W - PAD - bar_w - 20 - tw(draw, val, fs)
        draw.text((vx, ry + 4), val, fill=GRAY, font=fs)
        # 进度条（右侧固定宽度，不内嵌文字，e-ink 可读性更好）
        bx = SCREEN_W - PAD - bar_w
        by = ry + 6
        r = bar_h // 2
        draw.rounded_rectangle([bx, by, bx + bar_w, by + bar_h], radius=r, fill=LIGHT_GRAY, outline=BLACK, width=1)
        if v.get('ok') and pct is not None:
            fw = max(bar_h, int(bar_w * (pct or 0) / 100))
            if fw > 2:
                draw.rounded_rectangle([bx, by, bx + fw, by + bar_h], radius=r, fill=BLACK)
        elif not v.get('ok'):
            draw.text((bx + 8, by - 2), '—', fill=GRAY, font=fs)
    return y + len(rows) * (F_BODY + bar_h + gap)

def draw_weather(draw, d, y):
    w = d.get('weather', {})
    y = draw_title(draw, y, tr('天气'), w)
    if w.get('ok'):
        t1 = '%s°%s' % (fnum(w.get('temp')), LAYOUT['temperatureUnit'] if LAYOUT else 'C')
        ft = f(F_BIG, bold=True)
        draw.text((PAD, y), t1, fill=BLACK, font=ft)
        tw1 = tw(draw, t1, ft)
        det = ('%s  H%s L%s  RH%s%%' if LANG == 'en' else '%s  高%s 低%s  湿%s%%') % (w.get('text', ''), fnum(w.get('high')), fnum(w.get('low')), w.get('humidity', '?'))
        draw.text((PAD + tw1 + 24, y + 14), det, fill=GRAY, font=f(F_SMALL))
        # 温度大字用 56px 字体，实际字形高度超过 F_BIG，固定 y+F_BIG 会让字形底部压过分隔线
        return draw.textbbox((PAD, y), t1, font=ft)[3] + 8
    else:
        draw.text((PAD, y), tr('天气不可用'), fill=GRAY, font=f(F_SMALL))
        return y + F_SMALL + 8

def draw_market(draw, d, y):
    st = (d.get('stocks') or {}).get('items', [])
    y = draw_title(draw, y, tr('市场'), d.get('stocks'))
    ff = f(F_BODY)
    colw = CONTENT_W // 2
    rows = math.ceil(len(st) / 2)
    for i in range(0, len(st), 2):
        ry = y + (i // 2) * (F_BODY + 6)
        for j, s in enumerate(st[i:i+2]):
            x = PAD + j * colw
            if s.get('ok'):
                sign = '+' if (s.get('changePct') or 0) >= 0 else '-'
                cell = '%s %s %s%s%%' % (s.get('label') or s.get('sym'), fnum(s.get('price')), sign, fmt_pct(s.get('changePct')))
            else:
                cell = '%s --' % (s.get('label') or s.get('sym'))
            draw.text((x, ry), clip(draw, cell, ff, colw - 8), fill=BLACK, font=ff)
    return y + rows * (F_BODY + 6)

def draw_clocks(draw, d, y):
    """世界时钟（两列）"""
    y = draw_title(draw, y, tr('世界时钟'))
    cl = (d.get('clocks') or {}).get('items', [])
    ff = f(F_BODY)
    fs = f(F_SMALL)
    colw = CONTENT_W // 2
    if not cl:
        draw.text((PAD, y), tr('时钟不可用'), fill=GRAY, font=fs)
        return y + F_SMALL
    for i in range(0, len(cl), 2):
        ry = y + (i // 2) * (F_BODY + 8)
        for j, c in enumerate(cl[i:i+2]):
            x = PAD + j * colw
            city = c.get('city', '')
            if LANG == 'en':
                city = clip(draw, city, ff, colw - 150)
            tme = c.get('time', '')[:5]
            draw.text((x, ry), city, fill=BLACK, font=ff)
            cw = tw(draw, city, ff)
            draw.text((x + cw + 12, ry + 2), tme, fill=BLACK, font=ff)
            dw2 = tw(draw, tme, ff)
            date_s = '' if LANG == 'en' else (c.get('date') or '').replace('周', ' 周')
            draw.text((x + cw + dw2 + 24, ry + 6), date_s, fill=GRAY, font=fs)
    return y + math.ceil(len(cl) / 2) * (F_BODY + 8)

def draw_mlb(draw, d, y):
    """MLB · 道奇 / 教士：上一场比分 + 下一场时间（均为北京时间）"""
    y = draw_title(draw, y, tr('MLB · 道奇 / 教士'), d.get('mlb'))
    items = (d.get('mlb') or {}).get('items', [])
    ff = f(F_BODY)
    fs = f(F_SMALL)
    if not items:
        draw.text((PAD, y), tr('赛程暂不可用'), fill=GRAY, font=fs)
        return y + F_SMALL
    name_w = 88 if LANG == 'en' else 80
    col_a = PAD + name_w
    col_b = PAD + name_w + 410

    def mark_of(g):
        # "@勇士" 紧凑；"vs 海盗" 加空格更好读
        return 'vs ' if g.get('home') else '@'

    for i, it in enumerate(items[:2]):
        ry = y + i * (F_BODY + 8)
        draw.text((PAD, ry), it.get('cn', ''), fill=BLACK, font=f(F_BODY, bold=True))
        last = it.get('last') or {}
        nxt = it.get('next') or {}
        if last:
            s = '%s %s%s %s-%s' % (last.get('date', ''), mark_of(last), last.get('opp', ''),
                                   last.get('us', 0), last.get('them', 0))
            draw.text((col_a, ry), s, fill=GRAY, font=ff)
            res = tr('胜') if last.get('win') else tr('负')
            # 胜=黑，负=灰：e-ink 上靠明度区分，不用颜色
            draw.text((col_a + tw(draw, s, ff) + 12, ry), res,
                      fill=BLACK if last.get('win') else GRAY, font=f(F_BODY, bold=True))
        else:
            draw.text((col_a, ry), tr('无近期战报'), fill=GRAY, font=fs)
        if nxt:
            s2 = '→ %s %s %s%s' % (nxt.get('date', ''), nxt.get('time', ''),
                                   mark_of(nxt), nxt.get('opp', ''))
            draw.text((col_b, ry), clip(draw, s2, ff, SCREEN_W - PAD - col_b), fill=BLACK, font=ff)
    return y + min(len(items), 2) * (F_BODY + 8)

def draw_quote(draw, d, y, quotes):
    y = draw_title(draw, y, tr('今日一句'))
    if not quotes:
        draw.text((PAD, y), tr('（编辑 data/quotes.txt）'), fill=GRAY, font=f(F_SMALL))
        return y + F_SMALL
    ff = f(F_BODY)
    q = quotes[display_now().timetuple().tm_yday % len(quotes)]
    if ' —— ' in q:
        text, src = q.split(' —— ', 1)
    elif '—' in q:
        text, src = q.split('—', 1)
    else:
        text, src = q, ''
    line = clip(draw, text, ff, CONTENT_W - 80)
    if src:
        line = clip(draw, line + '  — ' + src, ff, CONTENT_W)
    draw.text((PAD, y), line, fill=BLACK, font=ff)
    return y + F_BODY + 6

def draw_footer(draw, d, y, offline=False, last_ok=None):
    hline(draw, y, GRAY, 1)
    y += 12
    now = display_now().strftime('%H:%M')
    txt = ('DayPane · 离线 · 最后 %s · 顶部下滑返回' % (last_ok or '?')) if offline \
        else ('DayPane · 更新 %s · 顶部下滑返回' % now)
    if LANG == 'en':
        txt = ('DayPane · Offline · Last %s' % (last_ok or '?')) if offline else 'DayPane · Updated %s · Swipe from top to exit' % now
    draw.text((PAD, y), txt, fill=GRAY, font=f(F_FOOT))
    return y + F_FOOT

# ---------- 主流程 ----------
def render(d, out_path=None, language="zh"):
    global LANG
    LANG = language
    global LAYOUT, SCREEN_W, SCREEN_H, CONTENT_W
    LAYOUT = load_layout(os.environ.get('SHAWN_CONFIG', 'config.json'))
    # Compose at a readable portrait ratio, then scale to the selected screen.
    SCREEN_W = 1072
    SCREEN_H = round(1072 * LAYOUT['height'] / LAYOUT['width'])
    CONTENT_W = SCREEN_W - 2 * PAD
    for key, base in {'F_DATE':96,'F_MONTH':46,'F_TIME':72,'F_TITLE':40,'F_BIG':56,'F_BODY':34,'F_SMALL':27,'F_FOOT':24}.items():
        globals()[key] = round(base * LAYOUT['fontScale'])
    d = localized_data(d)
    if LAYOUT['temperatureUnit'] == 'F':
        for key in ('temp','high','low'):
            value = (d.get('weather') or {}).get(key)
            if isinstance(value, (int,float)): d['weather'][key] = value*9/5+32
    img = Image.new('L', (SCREEN_W, SCREEN_H), WHITE)
    draw = ImageDraw.Draw(img)
    quotes = load_quotes()

    y = PAD
    y = draw_header(draw, d, y)
    y += 10
    thickline(draw, y, BLACK, 4)
    y += 16

    registry = {
        'news': lambda y: draw_news(draw, d, y),
        'ai': lambda y: draw_ai(draw, d, y),
        'weather': lambda y: draw_weather(draw, d, y),
        'market': lambda y: draw_market(draw, d, y),
        'clocks': lambda y: draw_clocks(draw, d, y),
        'mlb': lambda y: draw_mlb(draw, d, y),
        'quote': lambda y: draw_quote(draw, d, y, quotes),
    }
    mods = [registry[name] for name in LAYOUT['modules']]
    for fn in mods:
        y = fn(y)
        hline(draw, y + 4, GRAY, 1)
        y += 14
    y = draw_footer(draw, d, y)

    print('[render] final_y=%d screen_h=%d margin=%d' % (y, SCREEN_H, SCREEN_H - y), file=sys.stderr, flush=True)
    if y > SCREEN_H - 12:
        raise ValueError('Layout exceeds screen height; reduce modules or font scale')
    img = img.resize((LAYOUT['width'], LAYOUT['height']), Image.Resampling.LANCZOS)
    out = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    if out_path:
        out.save(out_path)
        print('saved', out_path, file=sys.stderr, flush=True)
    else:
        out.save(sys.stdout.buffer, 'PNG')
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', choices=['en', 'zh'], default='zh')
    ap.add_argument('--out')
    ap.add_argument('--data')
    ap.add_argument('--url', default='http://127.0.0.1:8787/api/dashboard')
    ap.add_argument('--check-fonts', action='store_true',
                    help='只校验字体能否渲染中文，失败则以非零码退出（CI 用）')
    a = ap.parse_args()
    # CI 上字体找错会渲染成方块，打出来便于排查
    print('[render] font_reg=%s%s' % (FONT_REG, '' if os.path.exists(FONT_REG) else '  <-- 缺失!'),
          file=sys.stderr, flush=True)
    print('[render] font_bold=%s%s' % (FONT_BOLD, '' if os.path.exists(FONT_BOLD) else '  <-- 缺失!'),
          file=sys.stderr, flush=True)

    if a.check_fonts:
        ok, info = check_fonts()
        for line in info:
            print('[font] ' + line, file=sys.stderr, flush=True)
        if not ok:
            print('[font] FAILED', file=sys.stderr, flush=True)
            sys.exit(2)
        print('[font] OK', file=sys.stderr, flush=True)
        return
    d = json.load(open(a.data, encoding='utf-8')) if a.data else fetch_dashboard(a.url)
    render(d, a.out, a.lang)

if __name__ == '__main__':
    main()
