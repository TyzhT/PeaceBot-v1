
import os
import nest_asyncio
import asyncio
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
nest_asyncio.apply()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

wallet = 100000
portfolio = {}

def get_price(symbol):
    data = yf.download(symbol, period="1d", interval="1m")
    return float(data['Close'].iloc[-1])

def plot_portfolio():
    fig, ax = plt.subplots()
    symbols = list(portfolio.keys())
    values = [portfolio[s] * get_price(s) for s in symbols]
    ax.pie(values, labels=symbols, autopct='%1.1f%%')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 PeaceBot Activated!")

async def strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Strategy: RSI 14-day with basic thresholds. Buy < 30, Sell > 70")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet
    value = wallet + sum([portfolio[symbol] * get_price(symbol) for symbol in portfolio])
    await update.message.reply_text(f"💼 Wallet: ₹{wallet:.2f}\n📈 Total Value: ₹{value:.2f}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet, portfolio
    try:
        symbol = context.args[0].upper()
        quantity = int(context.args[1])
        price = get_price(symbol)
        cost = price * quantity
        if wallet >= cost:
            wallet -= cost
            portfolio[symbol] = portfolio.get(symbol, 0) + quantity
            await update.message.reply_text(f"✅ Bought {quantity} of {symbol} at ₹{price:.2f}")
        else:
            await update.message.reply_text("❌ Not enough funds.")
    except:
        await update.message.reply_text("❗ Usage: /buy SYMBOL QUANTITY")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wallet, portfolio
    try:
        symbol = context.args[0].upper()
        quantity = int(context.args[1])
        if portfolio.get(symbol, 0) >= quantity:
            price = get_price(symbol)
            wallet += price * quantity
            portfolio[symbol] -= quantity
            if portfolio[symbol] == 0:
                del portfolio[symbol]
            await update.message.reply_text(f"✅ Sold {quantity} of {symbol} at ₹{price:.2f}")
        else:
            await update.message.reply_text("❌ Not enough holdings.")
    except:
        await update.message.reply_text("❗ Usage: /sell SYMBOL QUANTITY")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not portfolio:
        await update.message.reply_text("📉 Portfolio is empty.")
        return
    chart = plot_portfolio()
    await update.message.reply_photo(photo=chart)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("strategy", strategy))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("sell", sell))
app.add_handler(CommandHandler("chart", chart))

print("✅ PeaceBot v1.0 Running")
app.run_polling()
