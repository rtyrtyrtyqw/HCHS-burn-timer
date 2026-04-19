#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新竹高中炎上侦测器 – Dcard 版
功能：搜寻 Dcard 上关于竹中的最新文章，若发现炎上关键词且热度超过阈值，
      则将当前时间与事件标题写入 data.json。
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

# 优先使用 cloudscraper 绕过 Cloudflare，若未安装则回退到 requests
try:
    import cloudscraper
    scraper = cloudscraper.create_scraper()
    USING_CLOUDSCRAPER = True
except ImportError:
    import requests
    scraper = requests
    USING_CLOUDSCRAPER = False
    print("警告：未安装 cloudscraper，可能无法绕过 Dcard 防护。建议执行: pip install cloudscraper")

# ================= 参数配置 =================
SEARCH_QUERY = "新竹高中"   # 可同时搜到“竹中”
BURN_KEYWORDS = ["炎上", "爭議", "道歉", "抗議", "歧視", "校方", "黑箱", "教官", "霸凌", "性平"]
HEAT_THRESHOLD = 50        # 爱心数 + 留言数 >= 50 即视为有热度
DATA_FILE = "data.json"    # 输出文件
# ============================================

def fetch_dcard_posts():
    """从 Dcard 搜索 API 获取最新文章列表"""
    url = f"https://www.dcard.tw/service/api/v2/search/posts?query={SEARCH_QUERY}&sort=createdAt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        if USING_CLOUDSCRAPER:
            resp = scraper.get(url, headers=headers, timeout=15)
        else:
            resp = scraper.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"❌ API 请求失败，HTTP {resp.status_code}")
            return []
        posts = resp.json()
        # 确保返回的是列表
        if isinstance(posts, list):
            return posts
        else:
            print("❌ API 返回格式异常")
            return []
    except Exception as e:
        print(f"❌ 网络或解析错误: {e}")
        return []

def check_burn(posts):
    """遍历文章，判断是否存在炎上事件"""
    for post in posts:
        title = post.get('title', '')
        excerpt = post.get('excerpt', '')
        comment_count = post.get('commentCount', 0)
        like_count = post.get('likeCount', 0)
        content = title + excerpt

        # 检查关键词
        has_keyword = any(kw in content for kw in BURN_KEYWORDS)
        # 检查热度
        is_hot = (comment_count + like_count) >= HEAT_THRESHOLD

        if has_keyword and is_hot:
            print(f"🚨 侦测到炎上事件！标题：{title}")
            print(f"   热度: 爱心 {like_count} | 留言 {comment_count}")
            return True, title
    return False, None

def update_json(event_title):
    """将炎上时间写入 data.json，供前端读取"""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).isoformat(timespec='seconds')  # 例: 2025-04-19T14:35:00+08:00

    data = {
        "school": "新竹高中",
        "last_burn": now,
        "latest_event": event_title
    }

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新 {DATA_FILE}，归零时间：{now}")

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始扫描 Dcard...")
    posts = fetch_dcard_posts()
    if not posts:
        print("⚠️ 未获取到任何文章，可能 API 限制或网络问题，保持原有 data.json 不变。")
        return

    is_burning, title = check_burn(posts)
    if is_burning:
        update_json(title)
    else:
        print("✅ 目前校园一片祥和，无事发生。")

if __name__ == "__main__":
    main()
