import tkinter as tk
from tkinter import ttk, messagebox
from send1 import FileSender, FileSenderUI
from receive1 import FileReceiver, FileReceiverUI
import webbrowser
import json
import os

class RecAndSend:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg='#f0f0f0')
        
        # 创建菜单栏
        self.create_menu()
        
        # 设置样式
        style = ttk.Style()
        style.configure('TNotebook', background='#e0e0e0')
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TButton', padding=5)
        
        # 创建主notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 发送和接收框架
        self.send_frame = ttk.Frame(self.notebook)
        self.receive_frame = ttk.Frame(self.notebook)
        
        # 添加页面到notebook
        self.notebook.add(self.send_frame, text="📤 发送")
        self.notebook.add(self.receive_frame, text="📥 接收")

        # 初始化发送接收器
        self.file_sender = FileSender()
        self.sender_ui = FileSenderUI(self.send_frame, self.file_sender)

        self.file_receiver = FileReceiver()
        self.receiver_ui = FileReceiverUI(self.receive_frame, self.file_receiver)

        # 添加状态栏
        self.status_bar = tk.Label(root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 加载配置
        self.load_config()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存配置", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="传输速率图", command=self.show_speed_chart)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def save_config(self):
        config = {
            'last_host': self.sender_ui.entry_host.get(),
            'last_port': self.sender_ui.entry_port.get(),
            'threads': self.sender_ui.entry_threads.get()
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)
        self.status_bar.config(text="配置已保存")

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.sender_ui.entry_host.delete(0, tk.END)
                self.sender_ui.entry_host.insert(0, config.get('last_host', '127.0.0.1'))
                self.sender_ui.entry_port.delete(0, tk.END)
                self.sender_ui.entry_port.insert(0, config.get('last_port', '12345'))
                self.sender_ui.entry_threads.delete(0, tk.END)
                self.sender_ui.entry_threads.insert(0, config.get('threads', '3'))
        except:
            pass

    def show_speed_chart(self):
        import huitu
        huitu.plot_speed_vs_threads()

    def show_help(self):
        help_text = """
        文件收发器使用说明：
        1. 在发送页面输入接收方的IP地址和端口号。
        2. 选择要发送的文件并点击发送按钮。
        3. 在接收页面点击开始接收按钮。
        """
        messagebox.showinfo("使用说明", help_text)

    def show_about(self):
        about_text = """
        文件收发器 v1.0
        作者：陌水寒熙
        这是一个简单的文件发送和接收工具。
        """
        messagebox.showinfo("关于", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("文件收发器")
    root.geometry("800x900")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", tabposition='nw', background="LightSteelBlue")

    app = RecAndSend(root)
    root.mainloop()
