import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import math
import time
import json
import os
from datetime import datetime


class TicketClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NCHU连点器")
        self.root.geometry("500x950")

        # 运行状态
        self.is_clicking = False
        self.click_thread = None

        # 加载配置
        self.config_file = "clicker_config.json"
        self.config = self.load_config()

        self.setup_ui()

    def setup_ui(self):
        """创建界面"""
        # 标题
        title_label = tk.Label(self.root, text="这是一个连点器", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== 坐标设置 ==========
        coord_frame = ttk.LabelFrame(main_frame, text="点击位置设置", padding="10")
        coord_frame.pack(fill=tk.X, pady=5)

        # 坐标输入
        ttk.Label(coord_frame, text="X坐标:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.x_var = tk.StringVar(value=str(self.config.get("x", 500)))
        x_entry = ttk.Entry(coord_frame, textvariable=self.x_var, width=10)
        x_entry.grid(row=0, column=1, padx=5)

        ttk.Label(coord_frame, text="Y坐标:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.y_var = tk.StringVar(value=str(self.config.get("y", 600)))
        y_entry = ttk.Entry(coord_frame, textvariable=self.y_var, width=10)
        y_entry.grid(row=0, column=3, padx=5)

        # 获取坐标按钮
        def get_mouse_pos():
            self.get_coord_label.config(text="将鼠标移到按钮上，3秒后获取...")
            self.root.after(3000, self.capture_mouse_position)

        ttk.Button(coord_frame, text="获取鼠标位置", command=get_mouse_pos).grid(row=1, column=0, columnspan=2, pady=5,
                                                                                 sticky=tk.W)
        self.get_coord_label = ttk.Label(coord_frame, text="")
        self.get_coord_label.grid(row=1, column=2, columnspan=2, padx=5)

        # ========== 点击参数 ==========
        click_frame = ttk.LabelFrame(main_frame, text="点击参数设置", padding="10")
        click_frame.pack(fill=tk.X, pady=5)

        # 点击间隔
        ttk.Label(click_frame, text="点击间隔(秒):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.interval_var = tk.StringVar(value=str(self.config.get("interval", 0.01)))
        interval_spin = ttk.Spinbox(click_frame, from_=0.001, to=1, increment=0.001,
                                    textvariable=self.interval_var, width=10)
        interval_spin.grid(row=0, column=1, padx=5)
        ttk.Label(click_frame, text="(越小越快，建议0.01-0.05)").grid(row=0, column=2, padx=5)

        # 点击次数
        ttk.Label(click_frame, text="点击次数:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.max_clicks_var = tk.StringVar(value=str(self.config.get("max_clicks", 0)))
        max_clicks_entry = ttk.Entry(click_frame, textvariable=self.max_clicks_var, width=10)
        max_clicks_entry.grid(row=1, column=1, padx=5)
        ttk.Label(click_frame, text="(0表示无限点击)").grid(row=1, column=2, padx=5)

        # 持续时间
        ttk.Label(click_frame, text="持续时间(秒):").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.duration_var = tk.StringVar(value=str(self.config.get("duration", 30)))
        duration_entry = ttk.Entry(click_frame, textvariable=self.duration_var, width=10)
        duration_entry.grid(row=2, column=1, padx=5)
        ttk.Label(click_frame, text="(0表示无限制)").grid(row=2, column=2, padx=5)

        # ========== 高级设置 ==========
        advanced_frame = ttk.LabelFrame(main_frame, text="高级设置", padding="10")
        advanced_frame.pack(fill=tk.X, pady=5)

        # 随机延迟
        self.random_delay_var = tk.BooleanVar(value=self.config.get("random_delay", False))
        random_delay_cb = ttk.Checkbutton(advanced_frame, text="启用随机延迟",
                                          variable=self.random_delay_var,
                                          command=self.toggle_random_delay)
        random_delay_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.random_max_var = tk.StringVar(value=str(self.config.get("random_max", 0.02)))
        self.random_max_entry = ttk.Entry(advanced_frame, textvariable=self.random_max_var, width=10, state='disabled')
        self.random_max_entry.grid(row=1, column=1, padx=5)
        ttk.Label(advanced_frame, text="最大随机延迟(秒):").grid(row=1, column=0, sticky=tk.W, padx=5)

        # 多位置点击
        self.multi_pos_var = tk.BooleanVar(value=self.config.get("multi_pos", False))
        multi_pos_cb = ttk.Checkbutton(advanced_frame, text="启用多位置点击",
                                       variable=self.multi_pos_var,
                                       command=self.toggle_multi_pos)
        multi_pos_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.positions_text = tk.Text(advanced_frame, height=3, width=30, state='disabled')
        self.positions_text.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Label(advanced_frame, text="坐标列表(每行一个，格式:x,y):").grid(row=3, column=0, columnspan=2, sticky=tk.W)
        if self.config.get("positions"):
            self.positions_text.config(state='normal')
            self.positions_text.insert('1.0', "\n".join([f"{p[0]},{p[1]}" for p in self.config["positions"]]))
            self.positions_text.config(state='disabled')

        # ========== 快捷键设置 ==========
        hotkey_frame = ttk.LabelFrame(main_frame, text="快捷键设置", padding="10")
        hotkey_frame.pack(fill=tk.X, pady=5)

        ttk.Label(hotkey_frame, text="启动快捷键:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.start_hotkey_var = tk.StringVar(value=self.config.get("start_hotkey", "f9"))
        start_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.start_hotkey_var, width=10)
        start_hotkey_entry.grid(row=0, column=1, padx=5)

        ttk.Label(hotkey_frame, text="停止快捷键:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.stop_hotkey_var = tk.StringVar(value=self.config.get("stop_hotkey", "f10"))
        stop_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey_var, width=10)
        stop_hotkey_entry.grid(row=1, column=1, padx=5)

        # ========== 控制按钮 ==========
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(control_frame, text="开始抢票", command=self.start_clicking)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.stop_btn = ttk.Button(control_frame, text="停止", command=self.stop_clicking, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.save_btn = ttk.Button(control_frame, text="保存配置", command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # ========== 状态显示 ==========
        status_frame = ttk.LabelFrame(main_frame, text="运行状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.status_text = tk.Text(status_frame, height=8, width=50)
        self.status_text.pack(fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(self.status_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)

        # 计数器
        self.count_label = ttk.Label(status_frame, text="点击次数: 0")
        self.count_label.pack(pady=5)

    def capture_mouse_position(self):
        """获取鼠标位置"""
        try:
            pos = pyautogui.position()
            self.x_var.set(str(pos.x))
            self.y_var.set(str(pos.y))
            self.get_coord_label.config(text=f"已获取坐标: ({pos.x}, {pos.y})")
            self.add_log(f"获取坐标: X={pos.x}, Y={pos.y}")
        except Exception as e:
            self.get_coord_label.config(text="获取失败")
            self.add_log(f"获取坐标失败: {e}")

    def toggle_random_delay(self):
        """切换随机延迟"""
        if self.random_delay_var.get():
            self.random_max_entry.config(state='normal')
        else:
            self.random_max_entry.config(state='disabled')

    def toggle_multi_pos(self):
        """切换多位置点击"""
        if self.multi_pos_var.get():
            self.positions_text.config(state='normal')
        else:
            self.positions_text.config(state='disabled')

    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self):
        """保存配置"""
        config = {
            "x": int(self.x_var.get()),
            "y": int(self.y_var.get()),
            "interval": float(self.interval_var.get()),
            "max_clicks": int(self.max_clicks_var.get()),
            "duration": int(self.duration_var.get()),
            "random_delay": self.random_delay_var.get(),
            "random_max": float(self.random_max_var.get()),
            "multi_pos": self.multi_pos_var.get(),
            "start_hotkey": self.start_hotkey_var.get(),
            "stop_hotkey": self.stop_hotkey_var.get()
        }

        if self.multi_pos_var.get():
            positions = []
            text = self.positions_text.get('1.0', tk.END).strip()
            for line in text.split('\n'):
                if ',' in line:
                    x, y = line.split(',')
                    positions.append((int(x.strip()), int(y.strip())))
            config["positions"] = positions

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        self.add_log("配置已保存")
        messagebox.showinfo("成功", "配置已保存！")

    def start_clicking(self):
        """开始点击"""
        if self.is_clicking:
            return

        # 获取参数
        try:
            self.x = int(self.x_var.get())
            self.y = int(self.y_var.get())
            self.interval = float(self.interval_var.get())
            self.max_clicks = int(self.max_clicks_var.get())
            self.duration = int(self.duration_var.get())
            self.random_delay = self.random_delay_var.get()
            self.random_max = float(self.random_max_var.get()) if self.random_delay else 0
            self.multi_pos = self.multi_pos_var.get()

            if self.multi_pos:
                positions_text = self.positions_text.get('1.0', tk.END).strip()
                self.positions = []
                for line in positions_text.split('\n'):
                    if ',' in line:
                        x, y = line.split(',')
                        self.positions.append((int(x.strip()), int(y.strip())))
                if not self.positions:
                    messagebox.showwarning("警告", "请添加点击位置！")
                    return
        except ValueError as e:
            messagebox.showerror("错误", f"参数格式错误: {e}")
            return

        self.is_clicking = True
        self.click_count = 0
        self.start_time = time.time()

        # 启动点击线程
        self.click_thread = threading.Thread(target=self.click_loop)
        self.click_thread.daemon = True
        self.click_thread.start()

        # 更新UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.add_log(f"开始抢票 - 目标位置: ({self.x}, {self.y})")
        self.add_log(f"点击间隔: {self.interval}秒, 随机延迟: {self.random_delay}")
        if self.max_clicks > 0:
            self.add_log(f"目标次数: {self.max_clicks}")
        if self.duration > 0:
            self.add_log(f"持续时间: {self.duration}秒")

    def click_loop(self):
        """点击循环"""
        while self.is_clicking:
            # 检查时间限制
            if self.duration > 0 and time.time() - self.start_time > self.duration:
                self.add_log("时间到达，停止点击")
                self.stop_clicking()
                break

            # 检查次数限制
            if self.max_clicks > 0 and self.click_count >= self.max_clicks:
                self.add_log(f"已达到目标次数({self.max_clicks})，停止点击")
                self.stop_clicking()
                break

            # 执行点击
            try:
                if self.multi_pos:
                    # 多位置点击
                    for pos in self.positions:
                        if not self.is_clicking:
                            break
                        pyautogui.click(pos[0], pos[1])
                        self.click_count += 1
                        self.update_count_display()
                        if self.random_delay and self.random_max > 0:
                            time.sleep(random.uniform(0, self.random_max))
                else:
                    # 单位置点击
                    pyautogui.click(self.x, self.y)
                    self.click_count += 1
                    self.update_count_display()

                # 等待间隔
                if self.random_delay and self.random_max > 0:
                    time.sleep(max(0, self.interval + random.uniform(-self.random_max, self.random_max)))
                else:
                    time.sleep(self.interval)

            except Exception as e:
                self.add_log(f"点击错误: {e}")
                time.sleep(0.1)

        # 线程结束
        if not self.is_clicking:
            self.add_log("抢票已停止")

    def update_count_display(self):
        """更新计数显示"""

        def update():
            self.count_label.config(text=f"点击次数: {self.click_count}")
            if self.click_count % 100 == 0:
                self.add_log(f"已点击 {self.click_count} 次")

        self.root.after(0, update)

    def stop_clicking(self):
        """停止点击"""
        self.is_clicking = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

        # 显示统计
        elapsed = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        if elapsed > 0:
            rate = self.click_count / elapsed
            self.add_log(f"统计: 共点击{self.click_count}次, 耗时{elapsed:.1f}秒, 平均{rate:.1f}次/秒")


if __name__ == "__main__":
    # 检查依赖
    try:
        import pyautogui
        import random
    except ImportError:
        print("请先安装依赖: pip install pyautogui")
        exit(1)

    root = tk.Tk()
    app = TicketClickerGUI(root)
    root.mainloop()