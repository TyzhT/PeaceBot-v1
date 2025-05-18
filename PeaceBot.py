
import os
import logging
import nest_asyncio
import asyncio
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables
wallet = 100000
btc = 0.0
trade_log = []

# Fetch BTC data and calculate RSI
def fetch_data():
    df = yf.download("BTC-USD", period="7d", interval="5m")
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df["RSI"] = rsi
    return df

# Strategy: Simple RSI-based buy signal
def strategy(df):
    rsi = df["RSI"].iloc[-1]
    return rsi < 30  # Buy if RSI is oversold

# Handle /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 PeaceBot Activated!")

# Handle /portfolio
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💼 Wallet: ₹{wallet:.2f}
🪙 BTC: {btc:.6f}")

# Handle /summary
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_value = wallet + (btc * fetch_data()["Close"].iloc[-1])
    await update.message.reply_text(
        f"📊 Portfolio Summary:
Wallet: ₹{wallet:.2f}
BTC: {btc:.6f}
Total Value: ₹{total_value:.2f}"
    )

# Handle /chart
async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = fetch_data()
    plt.figure(figsize=(10, 5))
    plt.plot(df["Close"], label="BTC Price")
    plt.title("BTC Price (7d, 5min)")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    await update.message.reply_photo(photo=InputFile(buf, filename="chart.png"))

# Handle /buy
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet, btc
    df = fetch_data()
    price = float(df["Close"].iloc[-1])
    if wallet >= 5000:
        wallet -= 5000
        btc_bought = 5000 / price
        btc += btc_bought
        trade_log.append(f"BUY ₹5000 @ ${price:.2f}")
        await update.message.reply_text(f"✅ Bought BTC @ ${price:.2f}")
    else:
        await update.message.reply_text("❌ Not enough funds.")

# Handle /sell
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet, btc
    df = fetch_data()
    price = float(df["Close"].iloc[-1])
    if btc >= 0.001:
        btc -= 0.001
        wallet += price * 0.001
        trade_log.append(f"SELL 0.001 BTC @ ${price:.2f}")
        await update.message.reply_text(f"✅ Sold 0.001 BTC @ ${price:.2f}")
    else:
        await update.message.reply_text("❌ Not enough BTC.")

# Handle /log
async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trade_log:
        await update.message.reply_text("📭 No trades yet.")
    else:
        await update.message.reply_text("
".join(trade_log))

# Run the bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("log", log))

    logger.info("✅ PeaceBot is running...")
    await app.run_polling()

nest_asyncio.apply()
asyncio.run(main())
