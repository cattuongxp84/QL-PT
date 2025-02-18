import tkinter as tk
from tkinter import messagebox, Canvas, Scrollbar, Frame
from PIL import Image, ImageTk  # Add this line
import pyodbc
import socket

# ⚙️ Cấu hình SQL Server
DB_CONFIG = {
    "server": "DESKTOP-MKN2F4D",  # Thay bằng tên server của bạn
    "database": "DPT",
    "username": "",  # Để trống nếu dùng Windows Authentication
    "password": "",
}

# 🔗 Kết nối SQL Server
def connect_db():
    try:
        if DB_CONFIG["username"]:  # Dùng SQL Authentication
            conn_str = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
        else:  # Dùng Windows Authentication
            conn_str = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;"
        
        return pyodbc.connect(conn_str)
    except Exception as e:
        messagebox.showerror("Lỗi Kết Nối", f"Không thể kết nối SQL Server!\n{e}")
        return None

# 📡 Lấy danh sách máy tính từ SQL Server
def get_computers():
    conn = connect_db()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, hostname, status FROM Computers")
    computers = cursor.fetchall()
    conn.close()
    return computers

# 🚀 Gửi lệnh đến client qua socket
def send_command(ip, command):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, 5000))
        client_socket.sendall(command.encode("utf-8"))
        client_socket.close()
        messagebox.showinfo("Thành công", f"Đã gửi lệnh {command} đến {ip}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể gửi lệnh đến {ip}\n{e}")

# 🔄 Cập nhật trạng thái máy trên giao diện
def update_status():
    computers = get_computers()
    for ip, hostname, status in computers:
        color = "green" if status == "Online" else "red"
        if ip in button_dict:
            button_dict[ip].config(bg=color, text=hostname)
    
    root.after(5000, update_status)  # Cập nhật mỗi 5 giây

# Load icons
shutdown_icon = ImageTk.PhotoImage(Image.open("icons/shutdown.png").resize((20, 20)))
restart_icon = ImageTk.PhotoImage(Image.open("icons/restart.png").resize((20, 20)))
logoff_icon = ImageTk.PhotoImage(Image.open("icons/logoff.png").resize((20, 20)))

# 🎛️ Menu gửi lệnh khi click vào button máy tính
def on_computer_click(ip):
    menu = tk.Toplevel(root)
    menu.title(f"Điều khiển {ip}")
    menu.geometry("250x150")

    tk.Label(menu, text=f"Chọn lệnh cho {ip}:", font=("Arial", 12)).pack(pady=10)

    tk.Button(menu, text=" Shutdown", fg="white", bg="red", width=15, image=shutdown_icon, compound="left", command=lambda: send_command(ip, "SHUTDOWN")).pack(pady=5)
    tk.Button(menu, text=" Restart", fg="black", bg="yellow", width=15, image=restart_icon, compound="left", command=lambda: send_command(ip, "RESTART")).pack(pady=5)
    tk.Button(menu, text=" Logoff", fg="white", bg="blue", width=15, image=logoff_icon, compound="left", command=lambda: send_command(ip, "LOGOFF")).pack(pady=5)

# 🎨 Tạo giao diện Tkinter
root = tk.Tk()
root.title("Quản lý máy tính")
root.geometry("900x600")

# 📌 Canvas + Scrollbar để hiển thị 65 máy tính
canvas = Canvas(root)
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

button_dict = {}

# 📌 Lấy danh sách máy tính và tạo button
computers = get_computers()
for index, (ip, hostname, status) in enumerate(computers):
    color = "green" if status == "Online" else "red"
    btn = tk.Button(scrollable_frame, text=hostname, width=12, height=2, bg=color, command=lambda ip=ip: on_computer_click(ip))
    btn.grid(row=index // 8, column=index % 8, padx=5, pady=5)  # Sắp xếp theo hàng 8 cột
    button_dict[ip] = btn

# Tạo các button cho các máy tính còn lại (nếu có ít hơn 64 máy trong cơ sở dữ liệu)
for index in range(len(computers), 64):
    btn = tk.Button(scrollable_frame, text="Unknown", width=12, height=2, bg="gray", state="disabled")
    btn.grid(row=index // 8, column=index % 8, padx=5, pady=5)

# 🔄 Cập nhật trạng thái mỗi 5 giây
root.after(5000, update_status)

root.mainloop()
