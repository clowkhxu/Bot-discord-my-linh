import discord
from discord.ext import commands, tasks
import google.generativeai as genai
import os
import requests
import time
import asyncio
from flask import Flask
from threading import Thread
from io import BytesIO
from PIL import Image

# ======= Cấu hình API Key =======
GENAI_API_KEY = os.getenv('GENAI_API_KEY', '')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')

# ======= Cấu hình Gemini =======
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# ======= Cấu hình Discord Bot =======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Biến toàn cục để theo dõi trạng thái chat - mặc định là tắt (off)
chat_enabled = False


@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên {bot.user}')
    keep_alive.start()


@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn từ bot
    if message.author == bot.user:
        return

    # Xử lý lệnh
    await bot.process_commands(message)

    # Xử lý tin nhắn thông thường
    if not message.content.startswith(bot.command_prefix):
        await handle_message(message)


async def handle_message(message):
    global chat_enabled

    # Kiểm tra username của người gửi
    if message.author.name.lower() == "clow277":
        # Nếu chế độ chat đang tắt, không trả lời
        if not chat_enabled:
            return

        user_message = message.content.lower()
        print(f"User message from clow277: {user_message}")

        try:
            if "yêu" in user_message:
                reply = "Em yêu anh nhất, anh có yêu em không?"
            elif "nhớ em" in user_message:
                reply = "Nhớ anh hả? Em cũng nhớ anh nhiều."
            elif "giận" in user_message:
                reply = "Giận rồi đó. Anh dỗ em đi ~"
            else:
                try:
                    response = model.generate_content(f"""
                        Đóng vai bạn gái dễ thương nhưng quyền lực. Trả lời ngắn, xưng "em", gọi "anh yêu". 
                        Nhẹ nhàng, cưng chiều, quan tâm sức khỏe và tinh thần của anh.

                        User: {user_message}
                    """)
                    reply = response.text.strip()
                except Exception as e:
                    print(f"Lỗi khi xử lý tin nhắn: {e}")
                    reply = "Em bị lỗi rồi nè..."

            print(f"Reply: {reply}")
            await message.channel.send(reply)

        except Exception as e:
            print(f"Lỗi: {e}")
            await message.channel.send("Em bị lỗi rồi nè...")
    else:
        # Trả lời cho những người dùng khác
        await message.channel.send("Em chỉ nhắn tin với mỗi anh Clow thôi.")


@bot.command(name="ghe_dep")
async def toggle_chat(ctx, option=None):
    # Chỉ cho phép clow277 sử dụng lệnh này
    if ctx.author.name.lower() != "clow277":
        await ctx.send("Em chỉ nghe lệnh từ anh Clow thôi.")
        return

    global chat_enabled

    if option and option.lower() == "on":
        chat_enabled = True
        await ctx.send("Em sẽ trò chuyện với anh từ giờ.")
    elif option and option.lower() == "off":
        chat_enabled = False
        await ctx.send("Em sẽ im lặng từ giờ.")
    else:
        # Nếu không có tùy chọn, hiển thị trạng thái hiện tại
        status = "đang bật" if chat_enabled else "đang tắt"
        await ctx.send(
            f"Chế độ trò chuyện hiện {status}. Dùng '!ghe_dep on' để bật hoặc '!ghe_dep off' để tắt."
        )


@bot.command(name="clear")
async def clear_messages(ctx):
    # Chỉ cho phép clow277 sử dụng lệnh này
    if ctx.author.name.lower() != "clow277":
        await ctx.send("Em chỉ nghe lệnh từ anh Clow thôi.")
        return

    # Thông báo bắt đầu xóa tin nhắn
    status_message = await ctx.send("Em đang xóa tin nhắn của mình...")

    # Lấy 100 tin nhắn gần nhất trong kênh và xóa nếu là của bot
    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user:
            try:
                await message.delete()
                await asyncio.sleep(0.5)  # Tránh bị rate limit của Discord
            except discord.errors.NotFound:
                pass  # Bỏ qua nếu tin nhắn đã bị xóa trước đó

    # Xóa thông báo hoàn tất sau 5 giây
    complete_msg = await ctx.send("Em đã xóa xong tin nhắn của mình rồi!")
    await asyncio.sleep(5)
    await complete_msg.delete()


@bot.command(name="start")
async def start(ctx):
    if ctx.author.name.lower() == "clow277":
        await ctx.send("Em đây, anh yêu cần gì không?")
    else:
        await ctx.send("Em chỉ nhắn tin với mỗi anh Clow thôi.")


# ======= Flask để giữ ứng dụng hoạt động trên Render =======
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!"


# Chạy Flask trong luồng riêng để giữ ứng dụng hoạt động trên Render hoặc các dịch vụ tương tự
def run_flask():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)


# ======= Giữ Render luôn hoạt động bằng ping định kỳ =======
@tasks.loop(minutes=5)
async def keep_alive():
    url = "https://your-app-name.onrender.com"  # Thay đổi URL này thành URL thật của bạn trên Render hoặc dịch vụ khác.
    try:
        requests.get(url)
        print("Ping Flask để giữ ứng dụng luôn hoạt động.")
    except Exception as e:
        print(f"Lỗi khi ping Flask: {e}")


# ======= Chạy bot Discord =======
def main():
    Thread(target=run_flask).start()

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Lỗi khi chạy bot: {e}")


if __name__ == '__main__':
    main()
