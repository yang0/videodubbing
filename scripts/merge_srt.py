"""
字幕配音优化：合句 + 数字转文字
用于 srt-translator 输出的后处理，生成供 audioclone 使用的配音优化版字幕
"""
import re, sys

def parse_srt(path):
    with open(path, encoding='utf-8-sig') as f:
        raw = f.read()
    blocks = re.split(r'\n(?=\d+\n)', raw.strip())
    entries = []
    for b in blocks:
        lines = b.strip().split('\n')
        if len(lines) < 3:
            continue
        num = lines[0].strip()
        ts = lines[1].strip()
        text = '\n'.join(lines[2:]).strip()
        m = re.match(
            r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', ts
        )
        if not m:
            continue
        g = lambda i: int(m.group(i))
        start_ms = g(1)*3600000 + g(2)*60000 + g(3)*1000 + g(4)
        end_ms   = g(5)*3600000 + g(6)*60000 + g(7)*1000 + g(8)
        entries.append({
            'num': int(num), 'start': start_ms, 'end': end_ms, 'text': text, 'ts': ts
        })
    return entries

# ---- 数字转中文 ----
DIGITS = '零一二三四五六七八九'
UNITS  = ['', '十', '百', '千', '万', '十万', '百万', '千万', '亿']

def _int_cn(s):
    s = s.replace(',', '')
    if len(s) > 4:
        wan = int(s) // 10000
        rest = int(s) % 10000
        result = _int_cn(str(wan)) + '万'
        if rest > 0:
            result += _int_cn(str(rest))
        return result
    n = int(s)
    result = ''
    for i, c in enumerate(reversed(s)):
        d = int(c)
        if d > 0:
            result = DIGITS[d] + UNITS[i] + result
        elif i == 0 and result == '':
            result = DIGITS[0]
    result = re.sub(r'^一十', '十', result)
    return result or '零'

def _dec_cn(s):
    a, b = s.split('.')
    return _int_cn(a) + '点' + ''.join(DIGITS[int(c)] for c in b)

def _year_cn(s):
    return ''.join(DIGITS[int(c)] for c in s)

def num_to_chinese(text):
    text = re.sub(r'(\d+\.?\d*)%', lambda m: '百分之' + (_dec_cn(m.group(1)) if '.' in m.group(1) else _int_cn(m.group(1))), text)
    text = re.sub(r'(\d{4})(年)', lambda m: _year_cn(m.group(1)) + '年', text)
    text = re.sub(r'(\d+)(?:st|nd|rd|th)', lambda m: '第' + _int_cn(m.group(1)), text)
    text = re.sub(r'(?<!\w)(\d{1,3}(?:,\d{3})*(?:\.\d+)?)(?!\w|年|\d)', lambda m: _dec_cn(m.group(1)) if '.' in m.group(1) else _int_cn(m.group(1)), text)
    return text

# ---- 主逻辑 ----
def merge_and_normalize(entries, gap_threshold=300):
    merged = []
    i = 0
    while i < len(entries):
        e = entries[i]
        text = e['text']
        start = e['start']
        end = e['end']
        is_end = text and text[-1] in '\u3002\uff01\uff1f\u2026'  # 。！？…

        while i + 1 < len(entries):
            nxt = entries[i + 1]
            gap = nxt['start'] - end
            if not is_end or gap < gap_threshold:
                i += 1
                text += nxt['text']
                end = nxt['end']
                is_end = text[-1] in '\u3002\uff01\uff1f\u2026'
            else:
                break

        text = num_to_chinese(text)
        merged.append({'text': text, 'start': start, 'end': end})
        i += 1
    return merged

def ms_to_ts(ms):
    h = ms // 3600000; ms %= 3600000
    m = ms // 60000; ms %= 60000
    s = ms // 1000; ms %= 1000
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def write_srt(entries, path):
    lines = []
    for idx, e in enumerate(entries, 1):
        lines.append(str(idx))
        lines.append(f'{ms_to_ts(e["start"])} --> {ms_to_ts(e["end"])}')
        lines.append(e['text'])
        lines.append('')
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python merge_srt.py <input.srt> <output.srt> [gap_ms=300]')
        sys.exit(1)
    inp, out = sys.argv[1], sys.argv[2]
    gap = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    entries = parse_srt(inp)
    merged = merge_and_normalize(entries, gap)
    write_srt(merged, out)
    print(f'{len(entries)} 条 -> {len(merged)} 条 (减少 {len(entries)-len(merged)}, {len(merged)/len(entries)*100:.0f}%)')
    print(f'输出: {out}')
