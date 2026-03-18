#!/usr/bin/env python3
"""Удаляет старые блоки и создаёт оглавление со ссылками на подстраницы"""
import urllib.request
import json
import time

MATON_KEY = "qKSl5w70scaw9B7oIRYUk4_pVhSy0_2IdiWI0hm32v7_G1Kjw8L7iaBfINN1iWnxXhCM_T3fIj62yWRgK0jM24XrW28piN0XpdI"
PAGE_ID = "32783182-3725-81b5-b3a0-c27e6cb4b2c1"
BASE = "https://gateway.maton.ai/notion/v1"

# Подстраницы с ID
SUBPAGES = [
    ("📝", "Копирайтер — тексты для бизнеса", "3278318237258196a0f6e33ad0880d1b", "Посты, письма, рассылки, описания товаров, контент-планы"),
    ("📊", "Маркетолог — стратегия и анализ", "32783182372581fd9d5ac55c0e353d25", "Анализ конкурентов, портрет клиента, воронки продаж, УТП"),
    ("🎨", "Дизайнер — визуал и презентации", "3278318237258147bd77cda0b0a22316", "Карусели, презентации, обложки, картинки, инфографика"),
    ("💻", "Программист — сайты и автоматизации", "32783182372581328156c7d6063fadc5", "Лендинги, боты, автоматизации, интеграции, приложения"),
    ("📈", "Аналитик — цифры и финансы", "32783182372581669907d7809e078d51", "Финмодели, сметы, юнит-экономика, проверка цен"),
    ("👥", "HR и поиск клиентов", "32783182372581109f26d51362e90cf6", "Вакансии, собеседования, КП, холодные рассылки"),
    ("📄", "Секретарь — документы и рутина", "32783182372581a28a21dea5a6043deb", "Письма, договоры, протоколы, чек-листы, переводы"),
    ("🛒", "Продажник — скрипты и офферы", "327831823725814ab684d87a9d1dcca1", "Скрипты продаж, возражения, follow-up, офферы"),
    ("🎬", "Видеограф — AI-видео и Reels", "3278318237258136b8adc7e5e1f463bf", "Сценарии Reels, AI-видео, аватары, субтитры"),
    ("🧠", "Главное — Память ассистента", "327831823725814183e9fcfc956a0ad1", "Как ассистент учится, запоминает и становится умнее"),
]

def api(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {MATON_KEY}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        print(f"ERROR {e.code}: {err}")
        return None

# 1. Get all current blocks
print("Удаляю старые блоки...")
result = api("GET", f"/blocks/{PAGE_ID}/children?page_size=100")
if result:
    for block in result.get("results", []):
        bid = block["id"]
        # Skip child_page blocks (our subpages!)
        if block.get("type") == "child_page":
            continue
        api("DELETE", f"/blocks/{bid}")
        time.sleep(0.1)

# Check for more blocks
while result and result.get("has_more"):
    cursor = result.get("next_cursor")
    result = api("GET", f"/blocks/{PAGE_ID}/children?page_size=100&start_cursor={cursor}")
    if result:
        for block in result.get("results", []):
            if block.get("type") == "child_page":
                continue
            api("DELETE", f"/blocks/{block['id']}")
            time.sleep(0.1)

print("Старые блоки удалены!")
time.sleep(1)

# 2. Add new TOC with links
print("Создаю оглавление со ссылками...")

def format_page_id(raw_id):
    """Convert 32-char hex to UUID format"""
    if len(raw_id) == 32:
        return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
    return raw_id

children = [
    # Header
    {"object":"block","type":"heading_1","heading_1":{"rich_text":[{"text":{"content":"VA Academy — Методичка для учеников"}}]}},
    {"object":"block","type":"callout","callout":{
        "icon":{"type":"emoji","emoji":"🎯"},
        "rich_text":[{"text":{"content":"Один ассистент заменяет целую команду из 10 специалистов.\nНиже — все роли с примерами реальных запросов. Нажмите на любую → перейдёте в подробный раздел."}}]
    }},
    {"object":"block","type":"divider","divider":{}},
    {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"text":{"content":"📚 Содержание"}}]}},
]

# Add linked items for each subpage
for emoji, title, page_id, description in SUBPAGES:
    # Create a bookmark/link block using paragraph with mention
    uuid = format_page_id(page_id)
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "mention",
                    "mention": {
                        "type": "page",
                        "page": {"id": uuid}
                    }
                },
                {"type": "text", "text": {"content": f"\n{description}"},"annotations":{"color":"gray"}}
            ]
        }
    })

# Add summary section
children.extend([
    {"object":"block","type":"divider","divider":{}},
    {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"text":{"content":"💰 Итого: команда vs ассистент"}}]}},
    {"object":"block","type":"callout","callout":{
        "icon":{"type":"emoji","emoji":"📊"},
        "rich_text":[{"text":{"content":"Команда из 10 специалистов: 650К — 1.3 млн ₽/мес\nVA Academy ассистент: 30 000 ₽/мес\n\nИ он помнит ВСЁ. Навсегда."}}]
    }},
    {"object":"block","type":"divider","divider":{}},
    {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"© 2026 VA Academy — ИИ-ассистенты"},"annotations":{"color":"gray"}}]}},
])

result = api("PATCH", f"/blocks/{PAGE_ID}/children", {"children": children})
if result and "results" in result:
    print(f"✅ Оглавление создано!")
    print(f"📄 https://www.notion.so/{PAGE_ID.replace('-','')}")
else:
    print(f"❌ Ошибка: {result}")
