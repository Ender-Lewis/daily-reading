#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日阅读网页生成脚本
读取内容索引，提取今日应推送的内容，生成一个美观的HTML网页
"""

import json
import os
import random
import sys
from datetime import datetime, timezone, timedelta

# 路径配置（GitHub Actions中通过环境变量覆盖）
INDEX_PATH = os.environ.get('INDEX_PATH', 'index.json')
OUTPUT_PATH = os.environ.get('OUTPUT_PATH', 'index.html')

CST = timezone(timedelta(hours=8))


def load_index():
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_index(index):
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def get_remaining_files(index):
    return [fk for fk, fd in index['files'].items() if not fd['is_completed']]


def pick_and_advance(file_data):
    if file_data['is_completed']:
        return None
    idx = file_data['current_index']
    if idx >= len(file_data['segments']):
        file_data['is_completed'] = True
        return None
    seg = file_data['segments'][idx]
    seg['sent'] = True
    file_data['current_index'] = idx + 1
    if file_data['current_index'] >= len(file_data['segments']):
        file_data['is_completed'] = True
    total = len(file_data['segments'])
    progress = f"第{idx+1}/{total}段"
    if file_data['is_completed']:
        progress += " (已完结)"
    return seg['text'], seg.get('heading', ''), file_data['filename'], progress


def escape_html(text):
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def build_html(results, progress_info, date_str):
    articles_html = ""
    for i, (filename, heading, text, progress) in enumerate(results):
        safe_filename = escape_html(filename)
        safe_heading = escape_html(heading) if heading else ''
        safe_text = escape_html(text).replace('\n', '<br>')
        heading_html = f'<h3 class="heading">{safe_heading}</h3>' if safe_heading else ''
        articles_html += f'''
        <article class="article">
            <div class="article-header">
                <span class="tag">{safe_filename}</span>
                <span class="progress">{progress}</span>
            </div>
            {heading_html}
            <div class="content">{safe_text}</div>
        </article>
'''

    remaining_html = ""
    if progress_info['remaining_files'] > 0:
        for name in progress_info['remaining_names']:
            remaining_html += f'<li>{escape_html(name)}</li>'
    else:
        remaining_html = '<li style="color:#4ade80;">全部完成！</li>'

    completed_pct = round(progress_info['completed_files'] / progress_info['total_files'] * 100) if progress_info['total_files'] > 0 else 0

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日阅读 · {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: #fafaf9;
            color: #292524;
            line-height: 1.8;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #292524 0%, #44403c 100%);
            color: #fafaf9;
            padding: 2rem 1.5rem;
            text-align: center;
        }}
        .header h1 {{ font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; }}
        .header .date {{ font-size: 0.875rem; opacity: 0.7; }}
        .container {{ max-width: 42rem; margin: 0 auto; padding: 1.5rem 1rem 3rem; }}
        .article {{
            background: #ffffff; border-radius: 12px; padding: 1.5rem;
            margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}
        .article-header {{
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;
        }}
        .tag {{
            background: #fef3c7; color: #92400e; padding: 0.2rem 0.6rem;
            border-radius: 6px; font-size: 0.75rem; font-weight: 500;
        }}
        .progress {{ color: #78716c; font-size: 0.75rem; }}
        .heading {{ font-size: 1rem; font-weight: 600; color: #1c1917; margin-bottom: 0.75rem; }}
        .content {{ font-size: 0.9375rem; color: #44403c; text-align: justify; }}
        .stats {{
            background: #ffffff; border-radius: 12px; padding: 1.25rem 1.5rem;
            margin-top: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}
        .stats-title {{ font-size: 0.8rem; color: #78716c; margin-bottom: 0.75rem; }}
        .progress-bar {{
            background: #e7e5e4; border-radius: 100px; height: 6px;
            margin-bottom: 0.75rem; overflow: hidden;
        }}
        .progress-fill {{
            background: #f59e0b; height: 100%; border-radius: 100px; transition: width 0.3s ease;
        }}
        .progress-text {{ font-size: 0.8rem; color: #78716c; margin-bottom: 0.5rem; }}
        .stats ul {{ list-style: none; padding: 0; }}
        .stats li {{ font-size: 0.8rem; color: #78716c; padding: 0.2rem 0; }}
        .footer {{
            text-align: center; color: #a8a29e; font-size: 0.75rem; margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>每日阅读</h1>
        <div class="date">{date_str}</div>
    </div>
    <div class="container">
        {articles_html}
        <div class="stats">
            <div class="stats-title">阅读进度</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {completed_pct}%"></div>
            </div>
            <div class="progress-text">已完成 {progress_info['completed_files']}/{progress_info['total_files']} 份文件</div>
            <ul>{remaining_html}</ul>
        </div>
        <div class="footer">每日自动更新 · 刷新页面获取最新内容</div>
    </div>
</body>
</html>'''
    return html


def main():
    index = load_index()
    remaining = get_remaining_files(index)
    today = datetime.now(CST)
    date_str = today.strftime('%Y年%m月%d日')

    if not remaining:
        html = build_html([], {
            'completed_files': index['stats']['total_files'],
            'total_files': index['stats']['total_files'],
            'remaining_files': 0,
            'remaining_names': []
        }, date_str)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(html)
        print("ALL_COMPLETED")
        return

    selected = random.sample(remaining, min(2, len(remaining)))
    results = []
    for fk in selected:
        r = pick_and_advance(index['files'][fk])
        if r:
            results.append(r)

    if not results:
        print("NO_CONTENT")
        return

    remaining_after = get_remaining_files(index)
    progress_info = {
        'completed_files': index['stats']['total_files'] - len(remaining_after),
        'total_files': index['stats']['total_files'],
        'remaining_files': len(remaining_after),
        'remaining_names': [index['files'][k]['filename'] for k in remaining_after]
    }

    html = build_html(results, progress_info, date_str)
    save_index(index)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"SUCCESS - {date_str}")
    print(f"Files: {[r[2] for r in results]}")
    print(f"Progress: {progress_info['completed_files']}/{progress_info['total_files']}")


if __name__ == '__main__':
    main()
