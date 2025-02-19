import pyodbc
import socket
import threading
import json
from datetime import datetime, timedelta  # Đảm bảo đã import datetime
from datetime import timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageFilter
import pandas as pd  # Add pandas for Excel import
from tkcalendar import DateEntry  # Add DateEntry import
from fpdf import FPDF  # Correct import statement
from tkinterdnd2 import TkinterDnD, DND_FILES  # Add this import for print dialog
import os  # Add import for os module
from tkinter import PhotoImage

# Lưu trạng thái online theo máy (IP)
online_machines = {}

# Database configuration
DB_CONFIG = {
    "server": "DESKTOP-MKN2F4D",  # Thay bằng tên server của bạn
    "database": "QLMTDPT",
    "username": "",  # Để trống nếu dùng Windows Authentication
    "password": "",
}

# Kết nối SQL Server
def connect_db():
    try:
        if (DB_CONFIG["username"]):  # Dùng SQL Authentication
            conn_str = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
        else:  # Dùng Windows Authentication
            conn_str = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;"
        
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        error_message = f"Không thể kết nối SQL Server!\n{e}"
        print(error_message)
        messagebox.showerror("Lỗi Kết Nối", error_message)
        return None

# Kiểm tra đăng nhập
def check_login(username, password, conn):
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM QLMTDPT.dbo.taikhoan WHERE username = ? AND password = ?", (username, password))
        return cursor.fetchone()
    except pyodbc.Error as e:
        print(f"Error checking login: {e}")
        return None

# Cập nhật trạng thái online trong DB
def update_online_status(username, client_ip, status, conn):
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            MERGE QLMTDPT.dbo.online_status AS target
            USING (SELECT ? AS username, ? AS client_ip, ? AS status, ? AS login_time) AS source
            ON (target.username = source.username AND target.client_ip = source.client_ip)
            WHEN MATCHED THEN 
                UPDATE SET status = source.status, login_time = source.login_time
            WHEN NOT MATCHED THEN
                INSERT (username, client_ip, status, login_time)
                VALUES (source.username, source.client_ip, source.status, source.login_time);
        """, (username, client_ip, status, datetime.now()))
        conn.commit()
    except pyodbc.IntegrityError as e:
        print(f"Integrity error updating online status: {e}")
    except pyodbc.Error as e:
        print(f"Error updating online status: {e}")

# Giao diện quản lý Server
class ServerGUI:
    def __init__(self, QLMTDPT, db_conn):
        self.QLMTDPT = QLMTDPT
        self.db_conn = db_conn
        self.QLMTDPT.title("Phần mềm - Quản lý Máy Tính Phòng Đa Phương Tiện")
        self.QLMTDPT.iconbitmap(self.get_image_path("leaf.ico"))  # Use dynamic path for icon
        self.create_menu()  # Add menu creation

        # Load and set background image
        self.bg_image = Image.open(self.get_image_path("background.jpg"))
        self.bg_image = self.bg_image.filter(ImageFilter.GaussianBlur(5))  # Apply blur effect
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self.QLMTDPT, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self.QLMTDPT, bg="white", width=800, height=600)
        self.canvas.pack(fill="both", expand=True)
        self.bg_label.lower(self.canvas)  # Ensure the background label is behind the canvas

        self.canvas.bind("<Button-1>", self.on_canvas_click)  # Bind click event to canvas

        self.clients = {}
        self.create_client_grid()
        self.QLMTDPT.state("zoomed")  # Mở cửa sổ fullscreen

    def get_image_path(self, filename):
        return os.path.join(os.path.dirname(__file__), filename)

    def create_menu(self):
        menu_bar = tk.Menu(self.QLMTDPT)
        self.QLMTDPT.config(menu=menu_bar)

        menu_bar.add_command(label="Thống kê", command=self.show_statistics)
        
        account_menu = tk.Menu(menu_bar, tearoff=0)
        account_menu.add_command(label="Import Excel", command=self.import_excel)
        account_menu.add_command(label="Thêm tài khoản", command=self.add_account)
        menu_bar.add_cascade(label="Quản lý tài khoản", menu=account_menu)

        #menu_bar.add_command(label="Xem màn hình Client", command=self.view_client_screen)  # Add menu option

        shutdown_menu = tk.Menu(menu_bar, tearoff=0)
        shutdown_menu.add_command(label="Tắt từng máy ", command=self.shutdown_client)
        shutdown_menu.add_command(label="Tắt tất cả", command=self.shutdown_all_clients)
        menu_bar.add_cascade(label="Tắt máy", menu=shutdown_menu)

        # Remove the reload online status menu option
        # menu_bar.add_command(label="Reload Online Status", command=self.reload_online_status)

        menu_bar.add_command(label="Thông tin", command=self.show_info)

        # Set icon for each menu
        for menu in [menu_bar, account_menu, shutdown_menu]:
            self.QLMTDPT.iconbitmap(self.get_image_path("leaf.ico"))

    # Remove the reload_online_status method
    # def reload_online_status(self):
    #     reload_online_status(self, self.db_conn)  # Call the reload function

    def add_account(self):
        add_account_window = tk.Toplevel(self.QLMTDPT)
        add_account_window.title("Thêm tài khoản")
        add_account_window.geometry("400x300")  # Set the window size to 400x300
        add_account_window.iconbitmap(self.get_image_path("leaf.ico"))  # Add icon to the window

        # Center the window on the screen
        window_width, window_height = 400, 300
        screen_width = self.QLMTDPT.winfo_screenwidth()
        screen_height = self.QLMTDPT.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        add_account_window.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        tk.Label(add_account_window, text="Username:").grid(row=0, column=0, padx=10, pady=10)
        username_entry = tk.Entry(add_account_window)
        username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_account_window, text="Password:").grid(row=1, column=0, padx=10, pady=10)
        password_entry = tk.Entry(add_account_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(add_account_window, text="Khoa Viện:").grid(row=2, column=0, padx=10, pady=10)
        khoavien_list = [
            "Khoa Công nghệ Cơ khí", "Khoa Công nghệ Thông tin", "Khoa Công nghệ Điện", "Khoa Công nghệ Điện tử",
            "Khoa Công nghệ Động lực", "Khoa Công nghệ Nhiệt - Lạnh", "Khoa Công nghệ May - Thời trang", "Khoa Công nghệ Hóa học",
            "Khoa Ngoại ngữ", "Khoa Quản trị Kinh doanh", "Khoa Thương mại - Du lịch", "Khoa Kỹ thuật Xây dựng",
            "Khoa Luật", "Viện Tài chính - Kế toán", "Viện Công nghệ Sinh học và Thực phẩm", "Viện Khoa học Công nghệ và Quản lý Môi trường"
        ]
        max_width = max(len(khoavien) for khoavien in khoavien_list)
        khoavien_combobox = ttk.Combobox(add_account_window, values=khoavien_list, width=max_width)
        khoavien_combobox.grid(row=2, column=1, padx=10, pady=10)

        def on_submit():
            username = username_entry.get()
            password = password_entry.get()
            khoavien = khoavien_combobox.get()

            if username and password and khoavien:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                        MERGE QLMTDPT.dbo.taikhoan AS target
                        USING (SELECT ? AS username, ? AS password, ? AS khoavien) AS source
                        ON (target.username = source.username)
                        WHEN MATCHED THEN 
                            UPDATE SET password = source.password, khoavien = source.khoavien
                        WHEN NOT MATCHED THEN
                            INSERT (username, password, khoavien)
                            VALUES (source.username, source.password, source.khoavien);
                    """, (username, password, khoavien))
                    self.db_conn.commit()
                    messagebox.showinfo("Thêm tài khoản", "Thêm tài khoản thành công!")
                    add_account_window.destroy()
                except pyodbc.Error as e:
                    messagebox.showerror("Thêm tài khoản", f"Lỗi khi thêm tài khoản: {e}")
            else:
                messagebox.showwarning("Thêm tài khoản", "Vui lòng điền đầy đủ thông tin.")

        tk.Button(add_account_window, text="Thêm", command=on_submit).grid(row=3, column=0, columnspan=2, pady=20)

    def show_info(self):
        info_message = (
            "Author: Nguyễn Quang Thịnh\n"
            "Version: 1.0\n"
            "Address: 12 Nguyễn Văn Bảo, Phường 4, Gò Vấp, Hồ Chí Minh\n"
            "Phone: 0984458061"
        )
        messagebox.showinfo("Thông tin", info_message)

    def show_statistics(self):
        if not self.db_conn:
            messagebox.showerror("Thống kê", "Không thể kết nối đến cơ sở dữ liệu.")
            return

        date_picker_window = tk.Toplevel(self.QLMTDPT)
        date_picker_window.title("Chọn khoảng thời gian")
        date_picker_window.iconbitmap(self.get_image_path("leaf.ico"))  # Add icon to the form

        # Center the window on the screen
        window_width, window_height = 500, 350
        screen_width = self.QLMTDPT.winfo_screenwidth()
        screen_height = self.QLMTDPT.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        date_picker_window.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        frame = tk.Frame(date_picker_window)
        frame.pack(pady=20)

        tk.Label(frame, text="Ngày bắt đầu:").grid(row=0, column=0, padx=10)
        start_date_entry = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        start_date_entry.grid(row=0, column=1, padx=10)

        tk.Label(frame, text="Ngày kết thúc:").grid(row=0, column=2, padx=10)
        end_date_entry = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        end_date_entry.grid(row=0, column=3, padx=10)

        def on_submit():
            start_date = start_date_entry.get_date()
            end_date = end_date_entry.get_date()
            if (end_date - start_date).days < 1:
                messagebox.showerror("Thống kê", "Khoảng thời gian phải ít nhất là 1 ngày.")
                return
            self.generate_statistics((start_date + timedelta(days=1)).strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), date_picker_window)

        tk.Button(date_picker_window, text="Tạo báo cáo", command=on_submit).pack(pady=20)

    def generate_statistics(self, start_date, end_date, parent_window):
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Convert to datetime and include the end date
        start_date = datetime.strptime(start_date, '%Y-%m-%d')  # Convert to datetime
        khoavien_list = [
            "Khoa Công nghệ Cơ khí", "Khoa Công nghệ Thông tin", "Khoa Công nghệ Điện", "Khoa Công nghệ Điện tử",
            "Khoa Công nghệ Động lực", "Khoa Công nghệ Nhiệt - Lạnh", "Khoa Công nghệ May - Thời trang", "Khoa Công nghệ Hóa học",
            "Khoa Ngoại ngữ", "Khoa Quản trị Kinh doanh", "Khoa Thương mại - Du lịch", "Khoa Kỹ thuật Xây dựng",
            "Khoa Luật", "Viện Tài chính - Kế toán", "Viện Công nghệ Sinh học và Thực phẩm", "Viện Khoa học Công nghệ và Quản lý Môi trường"
        ]

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT QLMTDPT.dbo.taikhoan.khoavien, COUNT(*) as total_accesses
                FROM QLMTDPT.dbo.online_status
                JOIN QLMTDPT.dbo.taikhoan ON QLMTDPT.dbo.online_status.username = QLMTDPT.dbo.taikhoan.username
                WHERE login_time BETWEEN ? AND ?
                GROUP BY QLMTDPT.dbo.taikhoan.khoavien
            """, (start_date, end_date))  # Use ? for parameter markers
            records = cursor.fetchall()

            stats = {khoavien: 0 for khoavien in khoavien_list}
            for record in records:
                stats[record[0]] = record[1]

            stats_frame = tk.Frame(parent_window)
            stats_frame.pack(fill="both", expand=True)

            tree = ttk.Treeview(stats_frame, columns=("khoavien", "total_accesses"), show="headings")
            tree.heading("khoavien", text="Khoa Viện")
            tree.heading("total_accesses", text="Tổng Truy Cập")

            total_accesses_sum = 0
            for khoavien, total_accesses in stats.items():
                tree.insert("", "end", values=(khoavien, total_accesses))
                total_accesses_sum += total_accesses

            tree.pack(fill="both", expand=True)

            total_label = tk.Label(stats_frame, text=f"Tổng lượt truy cập: {total_accesses_sum}", font=("Arial", 12))
            total_label.pack(pady=10)

            # Fix the window size
            parent_window.geometry('600x650')

        except pyodbc.Error as e:
            messagebox.showerror("Thống kê", f"Lỗi khi truy vấn dữ liệu: {e}")

    def import_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            try:
                df = pd.read_excel(file_path)
                cursor = self.db_conn.cursor()
                for index, row in df.iterrows():
                    cursor.execute("""
                        MERGE QLMTDPT.dbo.taikhoan AS target
                        USING (SELECT ? AS username, ? AS password, ? AS khoavien) AS source
                        ON (target.username = source.username)
                        WHEN MATCHED THEN 
                            UPDATE SET password = source.password, khoavien = source.khoavien
                        WHEN NOT MATCHED THEN
                            INSERT (username, password, khoavien)
                            VALUES (source.username, source.password, source.khoavien);
                    """, (row['username'], row['password'], row['khoavien']))
                self.db_conn.commit()
                messagebox.showinfo("Import Excel", "Import dữ liệu thành công!")
            except Exception as e:
                messagebox.showerror("Import Excel", f"Lỗi khi import dữ liệu: {e}")

    def create_client_grid(self):
        total_pcs = 66
        icon_size = (80, 60)
        spacing_x, spacing_y = 160, 90  # Adjusted spacing_y to reduce the top margin

        self.icon_online = ImageTk.PhotoImage(Image.open(self.get_image_path("online.png")).resize(icon_size))
        self.icon_offline = ImageTk.PhotoImage(Image.open(self.get_image_path("offline.png")).resize(icon_size))

        pc_count = 0
        for pc_number in range(1, total_pcs + 1):
            if pc_number == 2:  # Skip PC 02
                continue
            row = pc_count // 9
            col = pc_count % 9
            x, y = spacing_x * (col + 1), spacing_y * (row + 1)
            pc_name = f"PC {pc_number:02}"  # Add leading zero if number is less than 10
            img_id = self.canvas.create_image(x, y, image=self.icon_offline)
            label_id = self.canvas.create_text(x, y + 45, text=pc_name, font=("Arial", 12))
            self.clients[pc_name] = {"ip": f"192.168.200.{100 + pc_number}", "image_id": img_id, "label": label_id, "x": x, "y": y}
            pc_count += 1

    def on_canvas_click(self, event):
        for pc_name, data in self.clients.items():
            x, y = data["x"], data["y"]
            if x - 30 < event.x < x + 30 and y - 30 < y + 30:
                self.view_client_screen(pc_name)
                break

    def view_client_screen(self, pc_name=None):
        if (pc_name is None):
            pc_name = simpledialog.askstring("Xem màn hình Client", "Nhập tên PC (ví dụ: PC 01):")
        if pc_name and pc_name in self.clients:
            client_ip = self.clients[pc_name]["ip"]
            # Send a request to the client to capture its screen
            request = json.dumps({"action": "capture_screen"}).encode('utf-8')
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((client_ip, 12345))
                client_socket.send(request)
                # Receive the screen data from the client
                screen_data = client_socket.recv(1024 * 1024)  # Adjust buffer size as needed
                self.display_client_screen(client_ip, screen_data)
            except ConnectionRefusedError:
                messagebox.showerror("Connection Error", f"Could not connect to {pc_name} at {client_ip}. The target machine actively refused the connection.")
            finally:
                client_socket.close()

    def update_client_status(self, client_ip, status):
        for pc_name, data in self.clients.items():
            if data["ip"] == client_ip:
                icon = self.icon_online if status == "online" else self.icon_offline
                self.canvas.itemconfig(data["image_id"], image=icon)

    def display_client_screen(self, client_ip, screen_data):
        screen_window = tk.Toplevel(self.QLMTDPT)
        screen_window.title(f"Màn hình của {client_ip}")
        screen_image = ImageTk.PhotoImage(data=screen_data)
        screen_label = tk.Label(screen_window, image=screen_image)
        screen_label.image = screen_image  # Keep a reference to avoid garbage collection
        screen_label.pack()

    def shutdown_client(self):
        pc_name = simpledialog.askstring("Shutdown Client", "Nhập tên PC (ví dụ: PC 01):")
        if pc_name and pc_name in self.clients:
            client_ip = self.clients[pc_name]["ip"]
            if not ping_client(client_ip):
                messagebox.showerror("Shutdown Client", f"Could not connect to {pc_name} at {client_ip}. The target machine actively refused the connection.")
                return
            request = json.dumps({"action": "shutdown"}).encode('utf-8')
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((client_ip, 12345))
                client_socket.send(request)
                response = json.loads(client_socket.recv(1024).decode('utf-8'))
                client_socket.close()
                messagebox.showinfo("Shutdown Client", response["message"])
            except Exception as e:
                print(f"Error shutting down client {pc_name} at {client_ip}: {e}")
                messagebox.showerror("Shutdown Client", f"Error shutting down client {pc_name}: {e}")

    def shutdown_all_clients(self):
        for pc_name, data in self.clients.items():
            client_ip = data["ip"]
            if not ping_client(client_ip):
                messagebox.showerror("Shutdown All Clients", f"Could not connect to {pc_name} at {client_ip}. The target machine actively refused the connection.")
                continue
            request = json.dumps({"action": "shutdown"}).encode('utf-8')
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((client_ip, 12345))
                client_socket.send(request)
                response = json.loads(client_socket.recv(1024).decode('utf-8'))
                client_socket.close()
                messagebox.showinfo("Shutdown All Clients", f"{pc_name}: {response['message']}")
            except Exception as e:
                print(f"Error shutting down client {pc_name} at {client_ip}: {e}")
                messagebox.showerror("Shutdown All Clients", f"Error shutting down client {pc_name}: {e}")

def handle_client(client_socket, client_address, gui, db_conn):
    try:
        data = client_socket.recv(1024).decode('utf-8')
        if data:
            request = json.loads(data)
            action = request.get("action")
            username = request.get("username")
            password = request.get("password")
            client_ip = request.get("client_ip")  # IP máy khách
            khoavien = request.get("khoavien")  # Add khoavien to handle registration

            if action == "login":
                if check_login(username, password, db_conn):
                    online_machines[client_ip] = username
                    update_online_status(username, client_ip, "online", db_conn)
                    gui.update_client_status(client_ip, "online")
                    client_socket.send(json.dumps({"status": "success", "message": "Đăng nhập thành công!"}).encode('utf-8'))
                else:
                    client_socket.send(json.dumps({"status": "error", "message": "Invalid credentials"}).encode('utf-8'))

            elif action == "register":
                try:
                    cursor = db_conn.cursor()
                    cursor.execute("""
                        MERGE QLMTDPT.dbo.taikhoan AS target
                        USING (SELECT ? AS username, ? AS password, ? AS khoavien) AS source
                        ON (target.username = source.username)
                        WHEN MATCHED THEN 
                            UPDATE SET password = source.password, khoavien = source.khoavien
                        WHEN NOT MATCHED THEN
                            INSERT (username, password, khoavien)
                            VALUES (source.username, source.password, source.khoavien);
                    """, (username, password, khoavien))
                    db_conn.commit()
                    client_socket.send(json.dumps({"status": "success", "message": "Đăng ký thành công!"}).encode('utf-8'))
                except pyodbc.Error as e:
                    client_socket.send(json.dumps({"status": "error", "message": f"Lỗi trong quá trình đăng ký: {e}"}).encode('utf-8'))

            elif action == "logout":
                if client_ip in online_machines:
                    username = online_machines[client_ip]
                    del online_machines[client_ip]
                    gui.update_client_status(client_ip, "offline")
                    client_socket.send(json.dumps({"status": "success", "message": "Đăng xuất thành công!"}).encode('utf-8'))

            elif action == "capture_screen":
                screen_data = request.get("screen_data")
                gui.display_client_screen(client_ip, screen_data)

            elif action == "shutdown":
                client_socket.send(json.dumps({"status": "success", "message": "Đã nhận được lệnh tắt máy"}).encode('utf-8'))
                os.system("shutdown /s /t 1")  # Shutdown the client machine
    except ConnectionResetError as e:
        print(f"Connection reset error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def ping_client(client_ip):
    try:
        print(f"Pinging client {client_ip}...")  # Debug print
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(2)  # Set timeout to 2 seconds
        client_socket.connect((client_ip, 12345))
        client_socket.close()
        print(f"Client {client_ip} is reachable.")  # Debug print
        return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Client {client_ip} is not reachable: {e}")  # Debug print
        return False

def start_server(gui, db_conn):
    # Remove the call to reload_online_status
    # reload_online_status(gui, db_conn)  # Reload online status from the database

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('192.168.200.102', 12345))
    server_socket.listen(5)
    print("Server started on port 12345")

    while True:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, client_address, gui, db_conn), daemon=True).start()

if __name__ == "__main__":
    try:
        db_conn = connect_db()
        if db_conn is None:
            raise Exception("Unable to connect to the database.")
    except Exception as e:
        messagebox.showerror("Database Connection Error", f"Unable to connect to the database: {e}")
        db_conn = None  # Set db_conn to None if connection fails

    root = tk.Tk()
    gui = ServerGUI(root, db_conn)
    if db_conn:
        # Remove the call to reload_online_status
        # reload_online_status(gui, db_conn)  # Reload online status from the database on startup
        threading.Thread(target=start_server, args=(gui, db_conn), daemon=True).start()
        # threading.Thread(target=check_heartbeats, args=(gui, db_conn), daemon=True).start()
    root.mainloop()