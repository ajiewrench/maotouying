import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from flask import Flask, send_file, abort
import socket
import os
import time
import uuid
import qrcode
from PIL import Image, ImageTk
import webbrowser

# ---------------- 配置 ----------------
APP_NAME = "猫头鹰 · 局域网文件互传助手"
VERSION = "v1.0.0"
AUTHOR = "阿杰"
GITHUB_URL = "https://github.com/ajiewrench"

PORT = 8080
EXPIRE_SECONDS = 600
current_file = None
is_published = False
token = None
token_expire = 0

FEATHER_PNG = "feather.png"
FEATHER_ICO = "feather.ico"

# ---------------- 自动生成 ICO ----------------
if os.path.exists(FEATHER_PNG):
    img = Image.open(FEATHER_PNG)
    img.save(FEATHER_ICO, format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32)])

# ---------------- 获取局域网IP ----------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# ---------------- Flask服务器 ----------------
app = Flask(__name__)

@app.route("/download")
def download():
    global current_file, is_published, token_expire
    try:
        if not is_published or not current_file or not os.path.exists(current_file):
            abort(404)
        if time.time() > token_expire:
            abort(403, "链接已过期")
        return send_file(current_file, as_attachment=True)
    except Exception as e:
        abort(500, str(e))

def run_flask():
    app.run(host="0.0.0.0", port=PORT, threaded=True)

# ---------------- Tkinter GUI ----------------
def select_file():
    global current_file, is_published
    path = filedialog.askopenfilename()
    if path:
        current_file = path
        is_published = False
        qr_label.config(image="")
        countdown_label.config(text="")
        url_entry.configure(state="normal")
        url_entry.delete(0, tk.END)
        url_entry.configure(state="readonly")
        update_status()

def upload():
    global is_published, token, token_expire
    if not current_file:
        return
    token = uuid.uuid4().hex
    token_expire = time.time() + EXPIRE_SECONDS
    is_published = True
    generate_qr()
    show_url()
    update_status()
    update_countdown()
    messagebox.showinfo("上传完毕", "中！！！！！！")

def reset():
    global current_file, is_published
    current_file = None
    is_published = False
    qr_label.config(image="")
    countdown_label.config(text="")
    url_entry.configure(state="normal")
    url_entry.delete(0, tk.END)
    url_entry.configure(state="readonly")
    update_status()

def update_status():
    if not current_file:
        status_label.config(text="未选择文件")
    elif is_published:
        status_label.config(text=f"已上传：{os.path.basename(current_file)}")
    else:
        status_label.config(text=f"已选择文件：{os.path.basename(current_file)}")

def generate_qr():
    ip = get_local_ip()
    url = f"http://{ip}:{PORT}/download"
    img = qrcode.make(url).resize((200, 200))
    photo = ImageTk.PhotoImage(img)
    qr_label.image = photo
    qr_label.config(image=photo)

def show_url():
    ip = get_local_ip()
    url = f"http://{ip}:{PORT}/download"
    url_entry.configure(state="normal")
    url_entry.delete(0, tk.END)
    url_entry.insert(0, url)
    url_entry.configure(state="readonly")

def open_file_url(event=None):
    url = url_entry.get()
    if url:
        webbrowser.open(url)

def open_github(event=None):
    webbrowser.open(GITHUB_URL)

def update_countdown():
    if not is_published:
        return
    remain = int(token_expire - time.time())
    if remain <= 0:
        countdown_label.config(text="剩余时间：00:00（已失效）")
        return
    m, s = divmod(remain, 60)
    countdown_label.config(text=f"剩余时间：{m:02d}:{s:02d}")
    root.after(1000, update_countdown)

# ---------------- GUI布局 ----------------
root = tk.Tk()
root.title(f"{APP_NAME}  |  by {AUTHOR}")
root.geometry("480x720")
root.resizable(False, False)

# 设置窗口图标（EXE图标）
if os.path.exists(FEATHER_ICO):
    root.iconbitmap(FEATHER_ICO)

DEFAULT_FONT = ("Segoe UI", 10)

# 顶部 Logo + 标题
top_frame = tk.Frame(root)
top_frame.pack(pady=15)

try:
    feather_img = Image.open(FEATHER_PNG).resize((32, 32))
    feather_photo = ImageTk.PhotoImage(feather_img)
    tk.Label(top_frame, image=feather_photo).pack(side="left", padx=5)
except:
    feather_photo = None

tk.Label(top_frame, text=APP_NAME, font=("Segoe UI", 14, "bold")).pack(side="left")

# 状态显示
status_label = tk.Label(root, text="请选择文件", font=("Segoe UI", 12))
status_label.pack(pady=(20, 10))

# 按钮
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="选择文件", width=15, font=DEFAULT_FONT, command=select_file).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="上传", width=12, font=DEFAULT_FONT, command=upload).grid(row=0, column=1, padx=10)
tk.Button(btn_frame, text="重置", width=12, font=DEFAULT_FONT, command=reset).grid(row=0, column=2, padx=10)

# 二维码提示
tk.Label(root, text="扫码下载文件", font=DEFAULT_FONT).pack(pady=5)
qr_label = tk.Label(root)
qr_label.pack(pady=5)
countdown_label = tk.Label(root, font=DEFAULT_FONT, fg="gray")
countdown_label.pack()

# URL显示（单行）
url_frame = tk.Frame(root)
url_frame.pack(pady=10, fill="x", padx=20)
tk.Label(url_frame, text="文件地址：", font=DEFAULT_FONT).pack(side="left")
url_entry = tk.Entry(url_frame, font=DEFAULT_FONT, width=50, state="readonly", fg="blue", cursor="hand2")
url_entry.pack(side="left", fill="x", expand=True)
url_entry.bind("<Button-1>", open_file_url)

# ---------------- 工具信息模块 ----------------
info_frame = tk.LabelFrame(root, text="工具信息", font=("Segoe UI", 10, "bold"), padx=12, pady=8)
info_frame.pack(padx=20, pady=18, fill="x")

tk.Label(info_frame, text=f"Version : {VERSION}", font=DEFAULT_FONT, anchor="w").pack(fill="x")
tk.Label(info_frame, text=f"Author  : {AUTHOR}", font=DEFAULT_FONT, anchor="w").pack(fill="x", pady=2)

# GitHub 可点击蓝色，但文字本身不蓝
github_frame = tk.Frame(info_frame)
github_frame.pack(fill="x")
tk.Label(github_frame, text="GitHub  : ", font=DEFAULT_FONT, anchor="w").pack(side="left")
github_url_label = tk.Label(github_frame, text=GITHUB_URL, font=DEFAULT_FONT, fg="blue", cursor="hand2")
github_url_label.pack(side="left")
github_url_label.bind("<Button-1>", open_github)

# ---------------- 启动 Flask 线程 ----------------
threading.Thread(target=run_flask, daemon=True).start()
root.mainloop()
