import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import socket
import json
import os
from pynput import keyboard
import threading
import time  # Add this import

SERVER_IP = "192.168.100.60"
SERVER_PORT = 12345
CLIENT_IP = "192.168.100.61"  # Bind to all available network interfaces

DISABLED_KEYS = {keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.cmd}

def on_press(key):
    if key in DISABLED_KEYS:
        return False  # Block the key press

listener = keyboard.Listener(on_press=on_press)
listener.start()

def send_to_server(action, username, password=None, khoavien=None):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    request = {"action": action, "username": username, "password": password, "client_ip": CLIENT_IP, "khoavien": khoavien}
    client_socket.send(json.dumps(request).encode('utf-8'))
    response_data = client_socket.recv(1024).decode('utf-8')
    client_socket.close()
    if not response_data:
        raise ValueError("Received empty response from server")
    return json.loads(response_data)

def handle_server_request():
    server_ip = '192.168.100.60'
    server_port = 12345

    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, server_port))

            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if data:
                    request = json.loads(data)
                    action = request.get("action")

                    if action == "shutdown":
                        client_socket.send(json.dumps({"status": "success", "message": "Shutdown command received"}).encode('utf-8'))
                        os.system("shutdown /s /t 1")  # Shutdown the client machine
        except ConnectionRefusedError:
            print(f"Connection to server {server_ip}:{server_port} refused. Retrying in 5 seconds...")
            time.sleep(5)  # Wait for 5 seconds before retrying
        except ConnectionResetError as e:
            print(f"Connection reset error: {e}. Retrying in 5 seconds...")
            time.sleep(5)  # Wait for 5 seconds before retrying
        except Exception as e:
            print(f"Error in handle_server_request: {e}")
        finally:
            client_socket.close()

def login():
    username = entry_username.get().strip()
    password = entry_password.get().strip()
    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password")
        return
    
    response = send_to_server("login", username, password)  # Gửi yêu cầu tới server
    if response["status"] == "success":
        messagebox.showinfo("Success", response["message"])  # Hiển thị thông báo
        login_window.destroy()
        open_main_window(username)
    else:
        messagebox.showerror("Error", response["message"])

def register():
    username = entry_username.get().strip()
    password = entry_password.get().strip()
    khoavien = entry_khoavien.get().strip()
    if not username or not password or not khoavien:
        messagebox.showerror("Error", "Please fill in all fields")
        return
    
    response = send_to_server("register", username, password, khoavien)  # Gửi yêu cầu tới server
    if response["status"] == "success":
        messagebox.showinfo("Success", response["message"])  # Hiển thị thông báo
        show_login_form()  # Switch back to login form
    else:
        messagebox.showerror("Error", response["message"])

def logout(username):
    response = send_to_server("logout", username)
    if response["status"] == "success":
        messagebox.showinfo("Success", response["message"])
        main_window.destroy()
        open_login_window()
    else:
        messagebox.showerror("Error", response["message"])

def log_error(error_message):
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{error_message}\n")

def disable_windows_keys():
    # Disable Windows key and Alt+Tab
    import ctypes
    user32 = ctypes.windll.user32
    user32.BlockInput(True)

def enable_windows_keys():
    # Enable Windows key and Alt+Tab
    import ctypes
    user32 = ctypes.windll.user32
    user32.BlockInput(False)

def open_login_window():
    global login_window, entry_username, entry_password, login_frame

    login_window = tk.Tk()
    login_window.title("Đăng nhập")

    # Làm cho cửa sổ chiếm toàn màn hình
    login_window.attributes("-fullscreen", True)
    login_window.attributes("-topmost", True)  # Đảm bảo cửa sổ luôn nằm trên các cửa sổ khác

    # Disable Windows key and Alt+Tab
    disable_windows_keys()

    # Đọc và hiển thị background hình ảnh
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        background_image_path = os.path.join(current_dir, "image.jpg")  # Đảm bảo đường dẫn đúng
        if not os.path.exists(background_image_path):
            raise Exception(f"Background image not found at {background_image_path}")
        
        background_image = Image.open(background_image_path)
        background_image = background_image.resize((login_window.winfo_screenwidth(), login_window.winfo_screenheight()), Image.Resampling.LANCZOS)
        background_photo = ImageTk.PhotoImage(background_image)
    except Exception as e:
        log_error(f"Error loading background image: {e}")
        messagebox.showerror("Error", f"Could not load background image: {e}")
        background_photo = None

    if background_photo:
        background_label = tk.Label(login_window, image=background_photo)
        background_label.place(relwidth=1, relheight=1)  # Đặt background hình ảnh

    # Tạo frame cho form login và đặt nó lệch phải
    login_frame = tk.Frame(login_window, bg="white", padx=30, pady=30, relief="solid", bd=4)
    login_frame.place(relx=0.8, rely=0.5, anchor="center")

    show_login_form()

    login_window.protocol("WM_DELETE_WINDOW", enable_windows_keys)  # Re-enable keys when window is closed
    login_window.mainloop()

def show_login_form():
    global entry_username, entry_password

    # Clear the existing widgets in the login_frame
    for widget in login_frame.winfo_children():
        widget.destroy()

    tk.Label(login_frame, text="Mã số SV", font=("Arial", 14), bg="white").pack(pady=5)
    entry_username = tk.Entry(login_frame, font=("Arial", 12), width=30)
    entry_username.pack(pady=5)
    entry_username.focus()  # Đặt con trỏ mặc định ở đây

    tk.Label(login_frame, text="Mật khẩu", font=("Arial", 14), bg="white").pack(pady=5)
    entry_password = tk.Entry(login_frame, show="*", font=("Arial", 12), width=30)
    entry_password.pack(pady=5)

    tk.Button(login_frame, text="Login", command=login, font=("Arial", 12), width=20, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(login_frame, text="Register", command=show_register_form, font=("Arial", 12), width=20, bg="#2196F3", fg="white").pack(pady=10)

    # Ràng buộc phím Enter với hành động login
    login_window.bind("<Return>", lambda event: login())

def show_register_form():
    global entry_username, entry_password, entry_khoavien

    # Clear the existing widgets in the login_frame
    for widget in login_frame.winfo_children():
        widget.destroy()

    tk.Label(login_frame, text="Mã số SV", font=("Arial", 14), bg="white").pack(pady=5)
    entry_username = tk.Entry(login_frame, font=("Arial", 12), width=30)
    entry_username.pack(pady=5)
    entry_username.focus()  # Đặt con trỏ mặc định ở đây

    tk.Label(login_frame, text="Mật khẩu", font=("Arial", 14), bg="white").pack(pady=5)
    entry_password = tk.Entry(login_frame, show="*", font=("Arial", 12), width=30)
    entry_password.pack(pady=5)

    tk.Label(login_frame, text="Khoa Viện", font=("Arial", 14), bg="white").pack(pady=5)
    khoa_vien_options = [
        "Khoa Công nghệ Cơ khí", "Khoa Công nghệ Thông tin", "Khoa Công nghệ Điện", "Khoa Công nghệ Điện tử",
        "Khoa Công nghệ Động lực", "Khoa Công nghệ Nhiệt - Lạnh", "Khoa Công nghệ May - Thời trang", "Khoa Công nghệ Hóa học",
        "Khoa Ngoại ngữ", "Khoa Quản trị Kinh doanh", "Khoa Thương mại - Du lịch", "Khoa Kỹ thuật Xây dựng",
        "Khoa Luật", "Viện Tài chính - Kế toán", "Viện Công nghệ Sinh học và Thực phẩm", "Viện Khoa học Công nghệ và Quản lý Môi trường"
    ]
    entry_khoavien = tk.StringVar(login_frame)
    entry_khoavien.set(khoa_vien_options[0])  # Set default value
    dropdown_khoavien = tk.OptionMenu(login_frame, entry_khoavien, *khoa_vien_options)
    dropdown_khoavien.config(font=("Arial", 12), width=28)
    dropdown_khoavien.pack(pady=5)

    tk.Button(login_frame, text="Register", command=register, font=("Arial", 12), width=20, bg="#4CAF50", fg="white").pack(pady=10)
    tk.Button(login_frame, text="Back to Login", command=show_login_form, font=("Arial", 12), width=20, bg="#2196F3", fg="white").pack(pady=10)

def open_main_window(username):
    global main_window
    main_window = tk.Tk()
    main_window.title("Main Window")

    # Làm cho cửa sổ không toàn màn hình và thay đổi kích thước
    main_window.geometry("300x150")  # Kích thước cửa sổ nhỏ

    # Đảm bảo cửa sổ luôn nằm trên các cửa sổ khác
    main_window.attributes("-topmost", True)

    # Di chuyển cửa sổ tới góc dưới bên phải
    screen_width = main_window.winfo_screenwidth()
    screen_height = main_window.winfo_screenheight()
    x = screen_width - 320  # Di chuyển tới góc phải màn hình
    y = screen_height - 200  # Di chuyển tới góc dưới

    main_window.geometry(f"300x150+{x}+{y}")  # Di chuyển cửa sổ

    tk.Label(main_window, text=f"Welcome, {username}!", font=("Arial", 14)).pack(pady=20)
    tk.Button(main_window, text="Logout", command=lambda: logout(username), font=("Arial", 12), bg="#f44336", fg="white").pack(pady=10)

    main_window.mainloop()

if __name__ == "__main__":
    threading.Thread(target=handle_server_request, daemon=True).start()
    open_login_window()