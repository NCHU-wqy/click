import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time
import json
import os
from datetime import datetime


class TicketClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("这是一个连点器")
        self.root.geometry("700x900")

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
        title_label = tk.Label(self.root, text="抢票自动点击器 - 轮换点击模式",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # 创建主框架和滚动条
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        main_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # ========== 点击模式选择 ==========
        mode_frame = ttk.LabelFrame(main_frame, text="点击模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)

        self.click_mode = tk.StringVar(value=self.config.get("click_mode", "rotation"))
        ttk.Radiobutton(mode_frame, text="轮换点击模式（推荐）",
                        variable=self.click_mode, value="rotation").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="随机点击模式",
                        variable=self.click_mode, value="random").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="顺序点击模式",
                        variable=self.click_mode, value="sequence").pack(anchor=tk.W)

        # ========== 坐标列表设置 ==========
        coord_frame = ttk.LabelFrame(main_frame, text="坐标列表（每个坐标可单独设置点击次数）", padding="10")
        coord_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 创建表格
        columns = ('X坐标', 'Y坐标', '点击次数', '描述')
        self.tree = ttk.Treeview(coord_frame, columns=columns, show='headings', height=6)

        for col in columns:
            self.tree.heading(col, text=col)
            if col == '点击次数':
                self.tree.column(col, width=100)
            elif col == '描述':
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=100)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # 坐标操作按钮
        coord_btn_frame = ttk.Frame(coord_frame)
        coord_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(coord_btn_frame, text="添加当前鼠标位置",
                   command=self.add_current_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(coord_btn_frame, text="手动添加",
                   command=self.manual_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(coord_btn_frame, text="删除选中",
                   command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(coord_btn_frame, text="清空所有",
                   command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # 导入导出
        ttk.Button(coord_btn_frame, text="导入配置",
                   command=self.import_positions).pack(side=tk.RIGHT, padx=5)
        ttk.Button(coord_btn_frame, text="导出配置",
                   command=self.export_positions).pack(side=tk.RIGHT, padx=5)

        # 加载保存的坐标
        self.load_positions_to_tree()

        # ========== 全局参数设置 ==========
        param_frame = ttk.LabelFrame(main_frame, text="全局参数设置", padding="10")
        param_frame.pack(fill=tk.X, pady=5)

        # 第一行
        row1 = ttk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="点击间隔(秒):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value=str(self.config.get("interval", 0.01)))
        interval_spin = ttk.Spinbox(row1, from_=0.001, to=1, increment=0.001,
                                    textvariable=self.interval_var, width=10)
        interval_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="轮换间隔(秒):").pack(side=tk.LEFT, padx=5)
        self.switch_delay_var = tk.StringVar(value=str(self.config.get("switch_delay", 0)))
        switch_spin = ttk.Spinbox(row1, from_=0, to=5, increment=0.1,
                                  textvariable=self.switch_delay_var, width=10)
        switch_spin.pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="(切换坐标后等待时间)").pack(side=tk.LEFT, padx=5)

        # 第二行
        row2 = ttk.Frame(param_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text="总点击次数:").pack(side=tk.LEFT, padx=5)
        self.max_clicks_var = tk.StringVar(value=str(self.config.get("max_clicks", 0)))
        max_clicks_entry = ttk.Entry(row2, textvariable=self.max_clicks_var, width=10)
        max_clicks_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="(0表示无限)").pack(side=tk.LEFT, padx=5)

        ttk.Label(row2, text="持续时间(秒):").pack(side=tk.LEFT, padx=5)
        self.duration_var = tk.StringVar(value=str(self.config.get("duration", 30)))
        duration_entry = ttk.Entry(row2, textvariable=self.duration_var, width=10)
        duration_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="(0表示无限制)").pack(side=tk.LEFT, padx=5)

        # 第三行
        row3 = ttk.Frame(param_frame)
        row3.pack(fill=tk.X, pady=2)

        self.random_delay_var = tk.BooleanVar(value=self.config.get("random_delay", False))
        ttk.Checkbutton(row3, text="启用随机延迟",
                        variable=self.random_delay_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(row3, text="最大随机延迟(秒):").pack(side=tk.LEFT, padx=5)
        self.random_max_var = tk.StringVar(value=str(self.config.get("random_max", 0.02)))
        random_entry = ttk.Entry(row3, textvariable=self.random_max_var, width=10)
        random_entry.pack(side=tk.LEFT, padx=5)

        # 第四行
        row4 = ttk.Frame(param_frame)
        row4.pack(fill=tk.X, pady=2)

        self.loop_mode_var = tk.BooleanVar(value=self.config.get("loop_mode", True))
        ttk.Checkbutton(row4, text="循环轮换（完成后重新从第一个开始）",
                        variable=self.loop_mode_var).pack(side=tk.LEFT, padx=5)

        # ========== 控制按钮 ==========
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(control_frame, text="开始抢票",
                                    command=self.start_clicking, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.stop_btn = ttk.Button(control_frame, text="停止",
                                   command=self.stop_clicking, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.save_btn = ttk.Button(control_frame, text="保存配置",
                                   command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # ========== 状态显示 ==========
        status_frame = ttk.LabelFrame(main_frame, text="运行状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.status_text = tk.Text(status_frame, height=10, width=60)
        self.status_text.pack(fill=tk.BOTH, expand=True)

        status_scrollbar = ttk.Scrollbar(self.status_text)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=status_scrollbar.set)
        status_scrollbar.config(command=self.status_text.yview)

        # 统计信息
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill=tk.X, pady=5)

        self.count_label = ttk.Label(stats_frame, text="总点击次数: 0")
        self.count_label.pack(side=tk.LEFT, padx=10)

        self.current_pos_label = ttk.Label(stats_frame, text="当前坐标: 无")
        self.current_pos_label.pack(side=tk.LEFT, padx=10)

        self.rotation_info_label = ttk.Label(stats_frame, text="轮换进度: 0/0")
        self.rotation_info_label.pack(side=tk.LEFT, padx=10)

        # 更新滚动区域
        main_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def add_current_position(self):
        """添加当前鼠标位置"""
        self.status_text.insert(tk.END, "3秒后获取鼠标位置，请将鼠标移到目标位置...\n")
        self.root.after(3000, self.capture_and_add_position)

    def capture_and_add_position(self):
        """捕获鼠标位置并添加到列表"""
        pos = pyautogui.position()
        # 弹出对话框设置点击次数
        self.add_position_dialog(pos.x, pos.y)

    def add_position_dialog(self, x, y):
        """添加位置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加坐标")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"坐标: ({x}, {y})").pack(pady=10)

        ttk.Label(dialog, text="点击次数:").pack()
        clicks_var = tk.StringVar(value="1")
        clicks_spin = ttk.Spinbox(dialog, from_=1, to=9999, textvariable=clicks_var, width=10)
        clicks_spin.pack(pady=5)

        ttk.Label(dialog, text="描述(可选):").pack()
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=30)
        desc_entry.pack(pady=5)

        def confirm():
            self.tree.insert('', 'end', values=(x, y, clicks_var.get(), desc_var.get()))
            dialog.destroy()
            self.status_text.insert(tk.END, f"已添加坐标: ({x}, {y}) 点击{clicks_var.get()}次\n")

        ttk.Button(dialog, text="确认", command=confirm).pack(pady=10)

    def manual_add(self):
        """手动添加坐标"""
        dialog = tk.Toplevel(self.root)
        dialog.title("手动添加坐标")
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="X坐标:").pack(pady=5)
        x_var = tk.StringVar()
        x_entry = ttk.Entry(dialog, textvariable=x_var)
        x_entry.pack()

        ttk.Label(dialog, text="Y坐标:").pack(pady=5)
        y_var = tk.StringVar()
        y_entry = ttk.Entry(dialog, textvariable=y_var)
        y_entry.pack()

        ttk.Label(dialog, text="点击次数:").pack(pady=5)
        clicks_var = tk.StringVar(value="1")
        clicks_spin = ttk.Spinbox(dialog, from_=1, to=9999, textvariable=clicks_var, width=10)
        clicks_spin.pack()

        ttk.Label(dialog, text="描述:").pack(pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dialog, textvariable=desc_var, width=30)
        desc_entry.pack()

        def confirm():
            try:
                x = int(x_var.get())
                y = int(y_var.get())
                self.tree.insert('', 'end', values=(x, y, clicks_var.get(), desc_var.get()))
                dialog.destroy()
                self.status_text.insert(tk.END, f"已添加坐标: ({x}, {y}) 点击{clicks_var.get()}次\n")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的坐标")

        ttk.Button(dialog, text="确认", command=confirm).pack(pady=10)

    def delete_selected(self):
        """删除选中的坐标"""
        selected = self.tree.selection()
        if selected:
            for item in selected:
                self.tree.delete(item)
            self.status_text.insert(tk.END, "已删除选中坐标\n")

    def clear_all(self):
        """清空所有坐标"""
        if messagebox.askyesno("确认", "确定要清空所有坐标吗？"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.status_text.insert(tk.END, "已清空所有坐标\n")

    def get_positions_list(self):
        """获取坐标列表"""
        positions = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if len(values) >= 3:
                positions.append({
                    'x': int(values[0]),
                    'y': int(values[1]),
                    'clicks': int(values[2]),
                    'desc': values[3] if len(values) > 3 else ''
                })
        return positions

    def load_positions_to_tree(self):
        """加载保存的坐标到表格"""
        positions = self.config.get("positions", [])
        for pos in positions:
            self.tree.insert('', 'end', values=(pos['x'], pos['y'], pos.get('clicks', 1), pos.get('desc', '')))

    def import_positions(self):
        """导入坐标配置"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    positions = json.load(f)
                self.clear_all()
                for pos in positions:
                    self.tree.insert('', 'end', values=(pos['x'], pos['y'], pos.get('clicks', 1), pos.get('desc', '')))
                self.status_text.insert(tk.END, f"已从 {filename} 导入配置\n")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def export_positions(self):
        """导出坐标配置"""
        from tkinter import filedialog
        positions = self.get_positions_list()
        if not positions:
            messagebox.showwarning("警告", "没有坐标可导出")
            return

        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(positions, f, indent=2, ensure_ascii=False)
                self.status_text.insert(tk.END, f"已导出到 {filename}\n")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

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
        return {
            "interval": 0.01,
            "switch_delay": 0,
            "max_clicks": 0,
            "duration": 30,
            "random_delay": False,
            "random_max": 0.02,
            "click_mode": "rotation",
            "loop_mode": True,
            "positions": []
        }

    def save_config(self):
        """保存配置"""
        config = {
            "interval": float(self.interval_var.get()),
            "switch_delay": float(self.switch_delay_var.get()),
            "max_clicks": int(self.max_clicks_var.get()),
            "duration": int(self.duration_var.get()),
            "random_delay": self.random_delay_var.get(),
            "random_max": float(self.random_max_var.get()),
            "click_mode": self.click_mode.get(),
            "loop_mode": self.loop_mode_var.get(),
            "positions": self.get_positions_list()
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        self.add_log("配置已保存")
        messagebox.showinfo("成功", "配置已保存！")

    def start_clicking(self):
        """开始点击"""
        if self.is_clicking:
            return

        # 获取坐标列表
        self.positions = self.get_positions_list()
        if not self.positions:
            messagebox.showwarning("警告", "请先添加点击坐标！")
            return

        # 获取参数
        try:
            self.interval = float(self.interval_var.get())
            self.switch_delay = float(self.switch_delay_var.get())
            self.max_clicks = int(self.max_clicks_var.get())
            self.duration = int(self.duration_var.get())
            self.random_delay = self.random_delay_var.get()
            self.random_max = float(self.random_max_var.get())
            self.click_mode = self.click_mode.get()
            self.loop_mode = self.loop_mode_var.get()
        except ValueError as e:
            messagebox.showerror("错误", f"参数格式错误: {e}")
            return

        self.is_clicking = True
        self.total_clicks = 0
        self.start_time = time.time()

        # 启动点击线程
        self.click_thread = threading.Thread(target=self.click_loop_with_rotation)
        self.click_thread.daemon = True
        self.click_thread.start()

        # 更新UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        mode_names = {"rotation": "轮换", "random": "随机", "sequence": "顺序"}
        self.add_log(f"开始抢票 - 模式: {mode_names[self.click_mode]}")
        self.add_log(f"共 {len(self.positions)} 个坐标点")
        for i, pos in enumerate(self.positions):
            self.add_log(f"  点{i + 1}: ({pos['x']}, {pos['y']}) - 点击{pos['clicks']}次 - {pos.get('desc', '')}")
        self.add_log(f"点击间隔: {self.interval}秒")
        if self.switch_delay > 0:
            self.add_log(f"轮换延迟: {self.switch_delay}秒")

    def click_loop_with_rotation(self):
        """带轮换的点击循环"""
        import random

        # 构建点击队列
        click_queue = []
        if self.click_mode == "rotation":
            # 轮换模式：按顺序每个坐标点击指定次数
            for pos in self.positions:
                for _ in range(pos['clicks']):
                    click_queue.append(pos)
        elif self.click_mode == "random":
            # 随机模式：随机选择坐标
            pass  # 动态生成
        else:  # sequence
            # 顺序模式：依次点击每个坐标一次，循环
            pass

        current_index = 0
        last_pos = None

        while self.is_clicking:
            # 检查时间限制
            if self.duration > 0 and time.time() - self.start_time > self.duration:
                self.add_log("时间到达，停止点击")
                break

            # 检查次数限制
            if self.max_clicks > 0 and self.total_clicks >= self.max_clicks:
                self.add_log(f"已达到目标次数({self.max_clicks})，停止点击")
                break

            # 根据模式选择下一个点击位置
            if self.click_mode == "rotation":
                if current_index >= len(click_queue):
                    if self.loop_mode:
                        current_index = 0
                        self.add_log("========== 开始新一轮轮换 ==========")
                    else:
                        self.add_log("所有轮换完成，停止点击")
                        break

                current_pos = click_queue[current_index]
                current_index += 1

            elif self.click_mode == "random":
                current_pos = random.choice(self.positions)
                # 随机模式也支持指定次数，但这里简化处理，每次都随机选

            else:  # sequence
                if current_index >= len(self.positions):
                    if self.loop_mode:
                        current_index = 0
                        self.add_log("========== 开始新一轮顺序 ==========")
                    else:
                        self.add_log("所有顺序完成，停止点击")
                        break
                current_pos = self.positions[current_index]
                current_index += 1

            # 切换坐标延迟
            if last_pos != current_pos and self.switch_delay > 0 and self.total_clicks > 0:
                self.add_log(f"切换到坐标 ({current_pos['x']}, {current_pos['y']})，等待{self.switch_delay}秒...")
                time.sleep(self.switch_delay)

            # 执行点击
            try:
                pyautogui.click(current_pos['x'], current_pos['y'])
                self.total_clicks += 1

                # 更新显示
                self.update_display(current_pos, current_index,
                                    len(click_queue) if self.click_mode == "rotation" else len(self.positions))

                # 随机延迟
                delay = self.interval
                if self.random_delay and self.random_max > 0:
                    delay = max(0.001, delay + random.uniform(-self.random_max, self.random_max))
                time.sleep(delay)

                last_pos = current_pos

            except Exception as e:
                self.add_log(f"点击错误: {e}")
                time.sleep(0.1)

        self.stop_clicking()

    def update_display(self, current_pos, current_index, total_items):
        """更新显示"""

        def update():
            self.count_label.config(text=f"总点击次数: {self.total_clicks}")
            self.current_pos_label.config(text=f"当前坐标: ({current_pos['x']}, {current_pos['y']})")
            if self.click_mode == "rotation":
                self.rotation_info_label.config(text=f"轮换进度: {current_index}/{total_items}")
            else:
                self.rotation_info_label.config(text=f"进度: {current_index}/{total_items}")

            if self.total_clicks % 50 == 0:
                elapsed = time.time() - self.start_time
                rate = self.total_clicks / elapsed if elapsed > 0 else 0
                self.add_log(f"进度: 已点击{self.total_clicks}次, 速率:{rate:.1f}次/秒")

        self.root.after(0, update)

    def stop_clicking(self):
        """停止点击"""
        if not self.is_clicking:
            return

        self.is_clicking = False

        # 显示统计
        elapsed = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        if elapsed > 0:
            rate = self.total_clicks / elapsed
            self.add_log(f"========== 抢票结束 ==========")
            self.add_log(f"总点击次数: {self.total_clicks}")
            self.add_log(f"总耗时: {elapsed:.1f}秒")
            self.add_log(f"平均速率: {rate:.1f}次/秒")

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')


if __name__ == "__main__":
    try:
        import pyautogui
        import random
    except ImportError:
        print("请先安装依赖: pip install pyautogui")
        exit(1)

    root = tk.Tk()
    app = TicketClickerGUI(root)
    root.mainloop()