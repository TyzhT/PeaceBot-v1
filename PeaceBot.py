
import os
import nest_asyncio
import asyncio
import logging
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# --- Setup ---
nest_asyncio.apply()
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

wallet = 100000.00  # ₹
btc = 0.0
trade_log = []
strategy = "RSI"

logging.basicConfig(level=logging.INFO)

# --- RSI Function ---
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- Price Fetch ---
def get_price_data():
    data = yf.download("BTC-USD", period="7d", interval="1h")
    data["RSI"] = calculate_rsi(data["Close"])
    return data

# --- Chart Generator ---
def generate_chart(data):
    plt.figure(figsize=(10, 5))
    plt.plot(data["Close"], label="BTC Price")
    plt.plot(data["RSI"], label="RSI")
    plt.axhline(30, color='green', linestyle='--', linewidth=1)
    plt.axhline(70, color='red', linestyle='--', linewidth=1)
    plt.legend()
    plt.title("BTC Price & RSI Chart")
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        await update.message.reply_text("⛔ Access Denied.")
        return
    await update.message.reply_text("👋 PeaceBot Activated!
Use /strategy, /buy, /sell, /chart, /summary")

async def set_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global strategy
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /strategy rsi")
        return
    strategy = context.args[0].upper()
    await update.message.reply_text(f"✅ Strategy set to {strategy}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet, btc
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /buy amount")
        return
    amount = float(context.args[0])
    price = float(get_price_data()["Close"].iloc[-1])
    if wallet >= amount:
        btc += amount / price
        wallet -= amount
        trade_log.append(f"BUY ₹{amount:.2f} @ ${price:.2f}")
        await update.message.reply_text(f"✅ Bought ₹{amount:.2f} worth BTC @ ${price:.2f}")
    else:
        await update.message.reply_text("❌ Insufficient funds")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet, btc
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /sell amount")
        return
    amount = float(context.args[0])
    price = float(get_price_data()["Close"].iloc[-1])
    sell_btc = amount / price
    if btc >= sell_btc:
        btc -= sell_btc
        wallet += amount
        trade_log.append(f"SELL ₹{amount:.2f} @ ${price:.2f}")
        await update.message.reply_text(f"✅ Sold ₹{amount:.2f} worth BTC @ ${price:.2f}")
    else:
        await update.message.reply_text("❌ Not enough BTC to sell")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_price_data()
    chart = generate_chart(data)
    await update.message.reply_photo(photo=InputFile(chart, filename="chart.png"))

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = float(get_price_data()["Close"].iloc[-1])
    value = btc * price
    total = wallet + value
    await update.message.reply_text(
        f"💼 Wallet: ₹{wallet:.2f}
"
        f"🪙 BTC: {btc:.6f}
"
        f"📈 BTC Value: ₹{value:.2f}
"
        f"🧾 Net Worth: ₹{total:.2f}"
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trade_log:
        await update.message.reply_text("🧾 No trades yet.")
    else:
        await update.message.reply_text("===== TRADE LOG =====
" + "
".join(trade_log))

# --- Main Bot Runner ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("strategy", set_strategy))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("history", history))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
