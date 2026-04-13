"""Daily Digest · Week 4 · N16 · B 路 /execute-plan 产出
对应 specs: week4/specs/digest.md · week4/specs/deploy.md

学员参考版 · 生产使用前请:
- 对接真实 SMTP 账号
- 对接 knowledge/articles/{date}.md 的真实解析
- 对接 subscribers.yaml 真实列表
"""
from __future__ import annotations
import argparse
import logging
import os
import smtplib
import sys
from email.mime.text import MIMEText
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import yaml

log = logging.getLogger(__name__)

# ─── 常量 · 从 env 读 ─────────────────────────────────────
SMTP_HOST    = os.getenv("SMTP_HOST")
SMTP_PORT    = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER    = os.getenv("SMTP_USER")
SMTP_PASS    = os.getenv("SMTP_PASS")
FROM_EMAIL   = os.getenv("FROM_EMAIL")
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "https://example.com")


def load_articles(date: str) -> List[dict]:
    """读 knowledge/articles/{date}.md · 解析 top 5（按 innovation_level 排）"""
    p = Path(f"knowledge/articles/{date}.md")
    if not p.exists():
        log.error(f"articles file missing: {p}")
        return []
    # TODO: 真实实现 · 解析 markdown · 按 spec § § 排序
    # 占位返回 mock 数据
    return [
        {"title": f"Example AI project {i}",
         "url": f"https://github.com/example/proj-{i}",
         "tech_category": "llm",
         "difficulty": "intermediate",
         "description": "这是一个示例描述 · 50 字内"}
        for i in range(1, 6)
    ]


def load_subscribers(path: str = "subscribers.yaml") -> List[str]:
    p = Path(path)
    if not p.exists():
        log.warning(f"no subscribers file · {p}")
        return []
    data = yaml.safe_load(p.read_text())
    return data.get("subscribers", [])


def render_email(articles: List[dict], date: str) -> tuple[str, str]:
    """返回 (subject, body)"""
    if not articles:
        subject = f"今日无更新 · {date}"
        body = "今日采集无内容 · 明天见。"
        return subject, body

    top1 = articles[0]
    subject = f"今日 5 条 AI 热点 · {top1['title'][:40]}"

    lines = [f"{date} · 共 {len(articles)} 条精选", ""]
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. {a['title']}")
        lines.append(f"   {a['url']}")
        lines.append(f"   标签: {a['tech_category']} · {a['difficulty']}")
        lines.append(f"   {a['description']}")
        lines.append("")

    lines.append("─" * 27)
    lines.append(f"完整内容 · {WEB_BASE_URL}/digest/{date}")
    lines.append(f"取消订阅 · {WEB_BASE_URL}/unsubscribe?token=<user_token>")

    return subject, "\n".join(lines)


def send_email(to: str, subject: str, body: str, dry_run: bool = False):
    if dry_run:
        log.info(f"[DRY-RUN] to={to} · subject={subject!r}")
        log.info(f"[DRY-RUN] body preview:\n{body[:300]}...")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    log.info(f"Loading articles for {args.date}")
    articles = load_articles(args.date)
    subject, body = render_email(articles, args.date)

    log.info(f"Loading subscribers")
    subs = load_subscribers()
    log.info(f"  {len(subs)} subscribers")

    sent = 0
    for sub in subs:
        try:
            send_email(sub, subject, body, dry_run=args.dry_run)
            sent += 1
        except Exception as e:
            log.exception(f"send to {sub} failed: {e}")

    log.info(f"Pipeline completed · sent {sent}/{len(subs)}")


if __name__ == "__main__":
    main()
