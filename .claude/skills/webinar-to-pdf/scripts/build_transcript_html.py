"""Parse raw transcript and generate styled HTML document.

Usage:
    python build_transcript_html.py --input transcript.txt --output transcript.html

Input format (Deepgram Nova 2 output):
    [MM:SS] Speaker N: text

Edit the `sections` list below to define topic boundaries by timestamp.
"""

import re
import argparse


def ts_to_sec(ts: str) -> int:
    p = ts.split(':')
    return int(p[0]) * 60 + int(p[1])


def build_transcript_html(input_path: str, output_path: str, title: str, subtitle: str,
                           meta: str, sections: list, footer_html: str):
    # Read and parse
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        line = line.strip()
        m = re.match(r'\[(\d+:\d+)\]\s*Speaker\s*\d+:\s*(.*)', line)
        if m:
            entries.append((m.group(1), m.group(2)))

    # Group into paragraphs
    paragraphs = []
    current_texts = []
    current_start = None
    prev_seconds = 0

    for ts, text in entries:
        seconds = ts_to_sec(ts)
        if current_start is None:
            current_start = ts
            current_texts = [text]
        elif seconds - prev_seconds < 25 and len(' '.join(current_texts)) < 600:
            current_texts.append(text)
        else:
            paragraphs.append((current_start, ' '.join(current_texts)))
            current_start = ts
            current_texts = [text]
        prev_seconds = seconds

    if current_texts:
        paragraphs.append((current_start, ' '.join(current_texts)))

    print(f'Parsed: {len(entries)} entries -> {len(paragraphs)} paragraphs')

    # Section boundaries
    section_boundaries = [(ts_to_sec(s[0]), s[1], s[2]) for s in sections]

    # Build HTML (uses template from references/html-components.md)
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', -apple-system, sans-serif;
            color: #1a1a2e; line-height: 1.8;
            background: #fff; padding: 50px 60px;
        }}
        .header {{
            background: linear-gradient(135deg, #0a0b2e, #151766, #2D2FE8);
            color: white; padding: 40px 50px;
            border-radius: 16px; margin-bottom: 40px;
        }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 1.1rem; opacity: 0.9; color: #7dd3fc; }}
        .header .meta {{ font-size: 0.9rem; opacity: 0.7; margin-top: 15px; }}
        .header .stats {{
            display: flex; gap: 30px; margin-top: 20px;
            padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.15);
        }}
        .header .stat {{ font-size: 0.9rem; }}
        .header .stat strong {{ color: #7dd3fc; }}
        .toc {{
            background: #f8fafc; border-radius: 12px;
            padding: 25px 30px; margin-bottom: 35px;
            border: 1px solid #e5e7eb;
        }}
        .toc h2 {{ font-size: 1.1rem; color: #151766; margin-bottom: 12px; }}
        .toc-item {{
            display: flex; justify-content: space-between;
            padding: 6px 0; font-size: 0.9rem;
            border-bottom: 1px dotted #d1d5db;
        }}
        .toc-item:last-child {{ border-bottom: none; }}
        .toc-time {{ color: #6b7280; font-family: monospace; font-size: 0.85rem; }}
        .section-header {{
            font-size: 1.3rem; color: #151766;
            margin: 35px 0 15px; padding: 12px 20px;
            border-radius: 8px; page-break-after: avoid;
        }}
        .paragraph {{
            margin: 8px 0; padding: 6px 0;
            font-size: 0.92rem; line-height: 1.8;
        }}
        .timestamp {{
            display: inline-block; font-family: monospace;
            font-size: 0.78rem; color: #9ca3af;
            background: #f3f4f6; padding: 1px 8px;
            border-radius: 4px; margin-right: 8px;
        }}
        .footer {{
            margin-top: 40px; padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            font-size: 0.85rem; color: #64748b;
        }}
        .footer a {{ color: #2D2FE8; text-decoration: none; }}
        @media print {{
            body {{ padding: 30px 40px; }}
            .section-header {{ page-break-after: avoid; }}
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
    <div class="meta">{meta}</div>
    <div class="stats">
        <div class="stat"><strong>{len(paragraphs)}</strong> paragraphs</div>
        <div class="stat"><strong>{len(entries)}</strong> phrases</div>
    </div>
</div>

<div class="toc">
    <h2>Contents</h2>
'''

    # TOC items
    for ts, sec_title, cls in sections:
        mins = int(ts.split(':')[0])
        secs = int(ts.split(':')[1])
        html += f'    <div class="toc-item"><span>{sec_title}</span><span class="toc-time">{mins:02d}:{secs:02d}</span></div>\n'

    html += '</div>\n'

    # Paragraphs with section headers
    emitted = set()
    current_idx = 0

    for ts, text in paragraphs:
        ts_sec = ts_to_sec(ts)

        for i in range(len(section_boundaries) - 1, -1, -1):
            if ts_sec >= section_boundaries[i][0]:
                current_idx = i
                break

        if current_idx not in emitted:
            emitted.add(current_idx)
            _, sec_title, sec_cls = section_boundaries[current_idx]
            html += f'\n<h2 class="section-header {sec_cls}">{sec_title}</h2>\n'

        mins = int(ts.split(':')[0])
        secs = int(ts.split(':')[1])
        html += f'<div class="paragraph"><span class="timestamp">{mins:02d}:{secs:02d}</span>{text}</div>\n'

    html += f'\n{footer_html}\n\n</body>\n</html>'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'HTML created: {len(html)} chars, {len(paragraphs)} paragraphs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build styled HTML from raw transcript')
    parser.add_argument('--input', required=True, help='Path to raw transcript .txt')
    parser.add_argument('--output', required=True, help='Output HTML path')
    args = parser.parse_args()

    # CUSTOMIZE: Edit these for each webinar
    sections = [
        ('00:42', 'Introduction', 'intro'),
        ('04:22', 'Program Overview', 'program'),
        ('08:20', 'Theory: Chatbots vs Assistants vs Agents', 'theory'),
        ('20:00', 'Practice: Platform Demo', 'practice'),
        ('55:00', 'Advanced Features', 'advanced'),
        ('95:00', 'Q&A and Closing', 'closing'),
    ]

    footer_html = '''<div class="footer">
    <p><strong>Speaker:</strong> Name | Contact info</p>
</div>'''

    build_transcript_html(
        args.input, args.output,
        title='Webinar Transcript',
        subtitle='Full transcript',
        meta='Date | Speaker',
        sections=sections,
        footer_html=footer_html
    )
