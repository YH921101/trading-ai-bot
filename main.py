import os
import json
from typing import Any, Dict

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "TradingView webhook server is running"
    }


@app.post("/webhook/tradingview")
async def tradingview_webhook(request: Request):
    """
    TradingViewのPine alert(json, ...) から送られるJSONを受信する。
    まずはDB保存せず、Renderログ出力 + Discord簡易通知だけ行う。
    """
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raw_body = await request.body()
        payload = {
            "raw_body": raw_body.decode("utf-8", errors="replace")
        }

    print("=== TradingView Webhook Received ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    discord_message = format_discord_message(payload)

    if DISCORD_WEBHOOK_URL:
        await send_discord_message(discord_message)
    else:
        print("DISCORD_WEBHOOK_URL is not set. Skipped Discord notification.")

    return JSONResponse(
        {
            "ok": True,
            "received": payload
        }
    )


async def send_discord_message(message: str):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message}
        )
        response.raise_for_status()


def format_discord_message(payload: Dict[str, Any]) -> str:
    """
    Discordに送るテスト用メッセージ。
    後で9:30まとめ、AI通知、日次ログ用に分ける。
    """
    symbol = payload.get("symbol", "-")
    name = payload.get("name", "-")
    bar_time = payload.get("bar_time", "-")
    bucket = payload.get("notification_bucket", "-")

    signals = payload.get("signals", "-")
    send_signal_set = payload.get("send_signal_set", "-")
    main_signal = payload.get("main_signal_hint", "-")

    price = payload.get("price", "-")
    change_pct = payload.get("change_pct", "-")
    volume = payload.get("volume", "-")
    vol_vs_20d = payload.get("volume_vs_20d", "-")

    daily_ma5 = payload.get("daily_ma5", "-")
    daily_ma20 = payload.get("daily_ma20", "-")
    ma5_kairi = payload.get("daily_ma5_kairi_pct", "-")

    return (
        "【TradingView Signal Test】\n"
        f"銘柄：{symbol} {name}\n"
        f"時刻：{bar_time}\n"
        f"Bucket：{bucket}\n"
        f"Signals：{signals}\n"
        f"SendSet：{send_signal_set}\n"
        f"Main：{main_signal}\n"
        f"価格：{price}\n"
        f"前日比：{change_pct}%\n"
        f"出来高：{volume}\n"
        f"20日平均比：{vol_vs_20d}倍\n"
        f"5MA：{daily_ma5}\n"
        f"20MA：{daily_ma20}\n"
        f"5MA乖離：{ma5_kairi}%"
    )
