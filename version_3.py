import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time
import json
import os
from datetime import datetime
import random


class ScrollableFrame(ttk.Frame):
    """可滚动的框架"""

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 存储canvas引用
        self.canvas = canvas


class TicketClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("抢票自动点击器 v3.2")
        self.root.geometry("800x800")

        # 设置窗口最小尺寸
        self.root.minsize(800, 600)

        # 配置根窗口的网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 运行状态
        self.is_clicking = False
        self.click_thread = None

        # 加载配置
        self.config_file = "clicker_config.json"
        self.config = self.load_config()

        self.setup_ui()

    def setup_ui(self):
        """创建界面"""
        # 创建主框架（使用Frame而不是直接使用ScrollableFrame，以便更好地控制布局）
        main_container = ttk.Frame(self.root)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # 创建可滚动框架
        self.scrollable_frame = ScrollableFrame(main_container)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

        # 获取实际的滚动内容框架
        content_frame = self.scrollable_frame.scrollable_frame

        # 配置内容框架的列权重
        content_frame.grid_columnconfigure(0, weight=1)

        # ========== 标题 ==========
        title_frame = ttk.Frame(content_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)

        title_label = tk.Label(title_frame, text="抢票自动点击器",
                               font=("Arial", 18, "bold"), fg="#333")
        title_label.grid(row=0, column=0)

        # ========== 使用说明 ==========
        info_frame = ttk.LabelFrame(content_frame, text="使用说明", padding="10")
        info_frame.grid(row=1, column=0, sticky="ew", pady=5, padx=10)
        info_frame.grid_columnconfigure(0, weight=1)

        info_text = """
        ★ 循环组：这些坐标会无限循环点击
        ★ 单次组：这些坐标只执行一次（执行完后自动停止）
        ★ 双击表格任意行可以编辑参数
        ★ 点击"删除"按钮删除选中的行
        ★ 支持鼠标滚轮滚动页面
        ★ 窗口可自由调整大小
        """
        info_label = ttk.Label(info_frame, text=info_text, foreground="blue")
        info_label.grid(row=0, column=0, sticky="w")

        # ========== 循环组设置 ==========
        loop_frame = ttk.LabelFrame(content_frame, text="【循环组】会无限循环点击的坐标", padding="10")
        loop_frame.grid(row=2, column=0, sticky="ew", pady=10, padx=10)
        loop_frame.grid_columnconfigure(0, weight=1)

        # 循环组表格和滚动条
        table_frame = ttk.Frame(loop_frame)
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # 创建表格滚动条
        tree_scroll = ttk.Scrollbar(table_frame)
        tree_scroll.grid(row=0, column=1, sticky="ns")

        loop_columns = ('X坐标', 'Y坐标', '点击次数', '描述')
        self.loop_tree = ttk.Treeview(table_frame, columns=loop_columns, show='headings',
                                      height=6, yscrollcommand=tree_scroll.set)

        for col in loop_columns:
            self.loop_tree.heading(col, text=col)
            if col == '点击次数':
                self.loop_tree.column(col, width=100, minwidth=80)
            elif col == '描述':
                self.loop_tree.column(col, width=300, minwidth=150)
            else:
                self.loop_tree.column(col, width=100, minwidth=80)

        self.loop_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.config(command=self.loop_tree.yview)

        # 绑定双击事件
        self.loop_tree.bind('<Double-Button-1>', lambda e: self.edit_item(self.loop_tree))

        # 循环组按钮
        loop_btn_frame = ttk.Frame(loop_frame)
        loop_btn_frame.grid(row=1, column=0, sticky="ew", pady=10)

        # 使用grid布局按钮，使其自动换行
        buttons = [
            ("添加当前鼠标位置", lambda: self.add_to_group("loop")),
            ("手动添加", lambda: self.manual_add_to_group("loop")),
            ("编辑选中", lambda: self.edit_item(self.loop_tree)),
            ("删除选中", lambda: self.delete_selected(self.loop_tree)),
            ("清空循环组", lambda: self.clear_group(self.loop_tree))
        ]

        for i, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(loop_btn_frame, text=text, command=cmd)
            btn.grid(row=0, column=i, padx=5, sticky="ew")
            loop_btn_frame.grid_columnconfigure(i, weight=1)

        # ========== 单次组设置 ==========
        once_frame = ttk.LabelFrame(content_frame, text="【单次组】只执行一次的坐标（执行完后自动停止）", padding="10")
        once_frame.grid(row=3, column=0, sticky="ew", pady=10, padx=10)
        once_frame.grid_columnconfigure(0, weight=1)

        # 单次组表格
        once_table_frame = ttk.Frame(once_frame)
        once_table_frame.grid(row=0, column=0, sticky="nsew")
        once_table_frame.grid_columnconfigure(0, weight=1)
        once_table_frame.grid_rowconfigure(0, weight=1)

        once_tree_scroll = ttk.Scrollbar(once_table_frame)
        once_tree_scroll.grid(row=0, column=1, sticky="ns")

        once_columns = ('X坐标', 'Y坐标', '点击次数', '描述')
        self.once_tree = ttk.Treeview(once_table_frame, columns=once_columns, show='headings',
                                      height=6, yscrollcommand=once_tree_scroll.set)

        for col in once_columns:
            self.once_tree.heading(col, text=col)
            if col == '点击次数':
                self.once_tree.column(col, width=100, minwidth=80)
            elif col == '描述':
                self.once_tree.column(col, width=300, minwidth=150)
            else:
                self.once_tree.column(col, width=100, minwidth=80)

        self.once_tree.grid(row=0, column=0, sticky="nsew")
        once_tree_scroll.config(command=self.once_tree.yview)

        # 绑定双击事件
        self.once_tree.bind('<Double-Button-1>', lambda e: self.edit_item(self.once_tree))

        # 单次组按钮
        once_btn_frame = ttk.Frame(once_frame)
        once_btn_frame.grid(row=1, column=0, sticky="ew", pady=10)

        once_buttons = [
            ("添加当前鼠标位置", lambda: self.add_to_group("once")),
            ("手动添加", lambda: self.manual_add_to_group("once")),
            ("编辑选中", lambda: self.edit_item(self.once_tree)),
            ("删除选中", lambda: self.delete_selected(self.once_tree)),
            ("清空单次组", lambda: self.clear_group(self.once_tree))
        ]

        for i, (text, cmd) in enumerate(once_buttons):
            btn = ttk.Button(once_btn_frame, text=text, command=cmd)
            btn.grid(row=0, column=i, padx=5, sticky="ew")
            once_btn_frame.grid_columnconfigure(i, weight=1)

        # ========== 移动按钮 ==========
        move_frame = ttk.Frame(content_frame)
        move_frame.grid(row=4, column=0, sticky="ew", pady=10, padx=10)
        move_frame.grid_columnconfigure(0, weight=1)
        move_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(move_frame, text="↓↓ 移到循环组 ↓↓",
                   command=self.move_to_loop).grid(row=0, column=0, padx=10, sticky="ew")
        ttk.Button(move_frame, text="↑↑ 移到单次组 ↑↑",
                   command=self.move_to_once).grid(row=0, column=1, padx=10, sticky="ew")

        # ========== 全局参数设置 ==========
        param_frame = ttk.LabelFrame(content_frame, text="全局参数设置", padding="10")
        param_frame.grid(row=5, column=0, sticky="ew", pady=10, padx=10)
        param_frame.grid_columnconfigure(0, weight=1)

        # 第一行
        row1 = ttk.Frame(param_frame)
        row1.grid(row=0, column=0, sticky="ew", pady=5)
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)
        row1.grid_columnconfigure(2, weight=1)
        row1.grid_columnconfigure(3, weight=1)

        ttk.Label(row1, text="点击间隔(秒):").grid(row=0, column=0, sticky="e", padx=5)
        self.interval_var = tk.StringVar(value=str(self.config.get("interval", 0.01)))
        interval_spin = ttk.Spinbox(row1, from_=0.001, to=1, increment=0.001,
                                    textvariable=self.interval_var, width=10)
        interval_spin.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(row1, text="轮换延迟(秒):").grid(row=0, column=2, sticky="e", padx=5)
        self.switch_delay_var = tk.StringVar(value=str(self.config.get("switch_delay", 0)))
        switch_spin = ttk.Spinbox(row1, from_=0, to=5, increment=0.1,
                                  textvariable=self.switch_delay_var, width=10)
        switch_spin.grid(row=0, column=3, sticky="w", padx=5)

        # 第二行
        row2 = ttk.Frame(param_frame)
        row2.grid(row=1, column=0, sticky="ew", pady=5)

        ttk.Label(row2, text="循环组轮换模式:").pack(side=tk.LEFT, padx=5)
        self.loop_mode_var = tk.StringVar(value=self.config.get("loop_mode", "rotation"))
        ttk.Radiobutton(row2, text="轮换（按次数）", variable=self.loop_mode_var, value="rotation").pack(side=tk.LEFT,
                                                                                                       padx=5)
        ttk.Radiobutton(row2, text="顺序（各1次）", variable=self.loop_mode_var, value="sequence").pack(side=tk.LEFT,
                                                                                                      padx=5)
        ttk.Radiobutton(row2, text="随机", variable=self.loop_mode_var, value="random").pack(side=tk.LEFT, padx=5)

        # 第三行
        row3 = ttk.Frame(param_frame)
        row3.grid(row=2, column=0, sticky="ew", pady=5)

        self.random_delay_var = tk.BooleanVar(value=self.config.get("random_delay", False))
        ttk.Checkbutton(row3, text="启用随机延迟",
                        variable=self.random_delay_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(row3, text="最大随机延迟(秒):").pack(side=tk.LEFT, padx=5)
        self.random_max_var = tk.StringVar(value=str(self.config.get("random_max", 0.02)))
        random_entry = ttk.Entry(row3, textvariable=self.random_max_var, width=10)
        random_entry.pack(side=tk.LEFT, padx=5)

        # 第四行
        row4 = ttk.Frame(param_frame)
        row4.grid(row=3, column=0, sticky="ew", pady=5)

        self.enable_once_group_var = tk.BooleanVar(value=self.config.get("enable_once_group", True))
        ttk.Checkbutton(row4, text="启用单次组（先执行单次组，再执行循环组）",
                        variable=self.enable_once_group_var).pack(side=tk.LEFT, padx=5)

        # ========== 控制按钮 ==========
        control_frame = ttk.Frame(content_frame)
        control_frame.grid(row=6, column=0, sticky="ew", pady=10, padx=10)
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)

        self.start_btn = ttk.Button(control_frame, text="开始抢票",
                                    command=self.start_clicking)
        self.start_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.stop_btn = ttk.Button(control_frame, text="停止",
                                   command=self.stop_clicking, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self.save_btn = ttk.Button(control_frame, text="保存配置",
                                   command=self.save_config)
        self.save_btn.grid(row=0, column=2, padx=5, sticky="ew")

        # ========== 状态显示 ==========
        status_frame = ttk.LabelFrame(content_frame, text="运行状态", padding="10")
        status_frame.grid(row=7, column=0, sticky="ew", pady=10, padx=10)
        status_frame.grid_columnconfigure(0, weight=1)

        # 统计信息
        stats_frame = ttk.Frame(status_frame)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=5)
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)

        self.count_label = ttk.Label(stats_frame, text="总点击次数: 0", font=("Arial", 10, "bold"))
        self.count_label.grid(row=0, column=0, padx=10, sticky="w")

        self.stage_label = ttk.Label(stats_frame, text="阶段: 等待开始", font=("Arial", 10, "bold"))
        self.stage_label.grid(row=0, column=1, padx=10, sticky="w")

        self.current_pos_label = ttk.Label(stats_frame, text="当前坐标: 无", font=("Arial", 10, "bold"))
        self.current_pos_label.grid(row=0, column=2, padx=10, sticky="w")

        # 日志文本框
        log_frame = ttk.Frame(status_frame)
        log_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.grid(row=0, column=1, sticky="ns")

        self.status_text = tk.Text(log_frame, height=12, width=70, yscrollcommand=log_scroll.set)
        self.status_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.config(command=self.status_text.yview)

        # 加载保存的配置
        self.load_groups()

    def add_to_group(self, group):
        """添加当前鼠标位置到指定组"""
        self.status_text.insert(tk.END, "3秒后获取鼠标位置，请将鼠标移到目标位置...\n")
        self.root.after(3000, lambda: self.capture_and_add(group))

    def capture_and_add(self, group):
        """捕获鼠标位置并添加到指定组"""
        pos = pyautogui.position()
        self.add_position_dialog(pos.x, pos.y, group)

    def manual_add_to_group(self, group):
        """手动添加坐标到指定组"""
        self.manual_add_dialog(group)

    def manual_add_dialog(self, group):
        """手动添加对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"手动添加坐标到{'循环组' if group == 'loop' else '单次组'}")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # 对话框布局
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="X坐标:").pack(pady=5)
        x_var = tk.StringVar()
        x_entry = ttk.Entry(main_frame, textvariable=x_var)
        x_entry.pack(fill=tk.X)

        ttk.Label(main_frame, text="Y坐标:").pack(pady=5)
        y_var = tk.StringVar()
        y_entry = ttk.Entry(main_frame, textvariable=y_var)
        y_entry.pack(fill=tk.X)

        ttk.Label(main_frame, text="点击次数:").pack(pady=5)
        clicks_var = tk.StringVar(value="1")
        clicks_spin = ttk.Spinbox(main_frame, from_=1, to=9999, textvariable=clicks_var, width=10)
        clicks_spin.pack(pady=5)

        ttk.Label(main_frame, text="描述(可选):").pack(pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(main_frame, textvariable=desc_var, width=30)
        desc_entry.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        def confirm():
            try:
                x = int(x_var.get())
                y = int(y_var.get())
                tree = self.loop_tree if group == "loop" else self.once_tree
                tree.insert('', 'end', values=(x, y, clicks_var.get(), desc_var.get()))
                dialog.destroy()
                self.status_text.insert(tk.END,
                                        f"已添加到{'循环组' if group == 'loop' else '单次组'}: ({x}, {y}) 点击{clicks_var.get()}次\n")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的坐标")

        ttk.Button(btn_frame, text="确认", command=confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def add_position_dialog(self, x, y, group):
        """添加位置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"添加坐标到{'循环组' if group == 'loop' else '单次组'}")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"坐标: ({x}, {y})", font=("Arial", 12)).pack(pady=10)

        ttk.Label(main_frame, text="点击次数:").pack(pady=5)
        clicks_var = tk.StringVar(value="1")
        clicks_spin = ttk.Spinbox(main_frame, from_=1, to=9999, textvariable=clicks_var, width=10)
        clicks_spin.pack(pady=5)

        ttk.Label(main_frame, text="描述(可选):").pack(pady=5)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(main_frame, textvariable=desc_var, width=30)
        desc_entry.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        def confirm():
            tree = self.loop_tree if group == "loop" else self.once_tree
            tree.insert('', 'end', values=(x, y, clicks_var.get(), desc_var.get()))
            dialog.destroy()
            self.status_text.insert(tk.END,
                                    f"已添加到{'循环组' if group == 'loop' else '单次组'}: ({x}, {y}) 点击{clicks_var.get()}次\n")

        ttk.Button(btn_frame, text="确认", command=confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def edit_item(self, tree):
        """编辑选中的项"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选中要编辑的行")
            return

        # 获取当前值
        item = selected[0]
        values = tree.item(item)['values']
        if len(values) < 3:
            return

        # 创建编辑对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑坐标")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="X坐标:").pack(pady=5)
        x_var = tk.StringVar(value=str(values[0]))
        x_entry = ttk.Entry(main_frame, textvariable=x_var)
        x_entry.pack(fill=tk.X)

        ttk.Label(main_frame, text="Y坐标:").pack(pady=5)
        y_var = tk.StringVar(value=str(values[1]))
        y_entry = ttk.Entry(main_frame, textvariable=y_var)
        y_entry.pack(fill=tk.X)

        ttk.Label(main_frame, text="点击次数:").pack(pady=5)
        clicks_var = tk.StringVar(value=str(values[2]))
        clicks_spin = ttk.Spinbox(main_frame, from_=1, to=9999, textvariable=clicks_var, width=10)
        clicks_spin.pack(pady=5)

        ttk.Label(main_frame, text="描述:").pack(pady=5)
        desc_var = tk.StringVar(value=values[3] if len(values) > 3 else "")
        desc_entry = ttk.Entry(main_frame, textvariable=desc_var, width=30)
        desc_entry.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        def save():
            try:
                new_x = int(x_var.get())
                new_y = int(y_var.get())
                new_clicks = int(clicks_var.get())
                new_desc = desc_var.get()

                tree.item(item, values=(new_x, new_y, new_clicks, new_desc))
                dialog.destroy()
                self.status_text.insert(tk.END, f"已更新坐标: ({new_x}, {new_y}) 点击{new_clicks}次\n")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")

        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def delete_selected(self, tree):
        """删除选中的坐标"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选中要删除的行")
            return

        if messagebox.askyesno("确认", f"确定要删除选中的 {len(selected)} 个坐标吗？"):
            for item in selected:
                tree.delete(item)
            self.status_text.insert(tk.END, f"已删除 {len(selected)} 个坐标\n")

    def clear_group(self, tree):
        """清空组"""
        group_name = "循环组" if tree == self.loop_tree else "单次组"
        if messagebox.askyesno("确认", f"确定要清空{group_name}吗？"):
            for item in tree.get_children():
                tree.delete(item)
            self.status_text.insert(tk.END, f"已清空{group_name}\n")

    def move_to_loop(self):
        """将单次组选中的坐标移到循环组"""
        selected = self.once_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先在单次组中选择要移动的坐标")
            return

        for item in selected:
            values = self.once_tree.item(item)['values']
            self.loop_tree.insert('', 'end', values=values)
            self.once_tree.delete(item)

        self.status_text.insert(tk.END, f"已将 {len(selected)} 个坐标移到循环组\n")

    def move_to_once(self):
        """将循环组选中的坐标移到单次组"""
        selected = self.loop_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先在循环组中选择要移动的坐标")
            return

        for item in selected:
            values = self.loop_tree.item(item)['values']
            self.once_tree.insert('', 'end', values=values)
            self.loop_tree.delete(item)

        self.status_text.insert(tk.END, f"已将 {len(selected)} 个坐标移到单次组\n")

    def get_group_positions(self, tree):
        """获取组内的坐标列表"""
        positions = []
        for item in tree.get_children():
            values = tree.item(item)['values']
            if len(values) >= 3:
                positions.append({
                    'x': int(values[0]),
                    'y': int(values[1]),
                    'clicks': int(values[2]),
                    'desc': values[3] if len(values) > 3 else ''
                })
        return positions

    def load_groups(self):
        """加载保存的分组配置"""
        # 加载循环组
        loop_positions = self.config.get("loop_group", [])
        for pos in loop_positions:
            self.loop_tree.insert('', 'end', values=(pos['x'], pos['y'], pos.get('clicks', 1), pos.get('desc', '')))

        # 加载单次组
        once_positions = self.config.get("once_group", [])
        for pos in once_positions:
            self.once_tree.insert('', 'end', values=(pos['x'], pos['y'], pos.get('clicks', 1), pos.get('desc', '')))

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
            "random_delay": False,
            "random_max": 0.02,
            "loop_mode": "rotation",
            "enable_once_group": True,
            "loop_group": [],
            "once_group": []
        }

    def save_config(self):
        """保存配置"""
        config = {
            "interval": float(self.interval_var.get()),
            "switch_delay": float(self.switch_delay_var.get()),
            "random_delay": self.random_delay_var.get(),
            "random_max": float(self.random_max_var.get()),
            "loop_mode": self.loop_mode_var.get(),
            "enable_once_group": self.enable_once_group_var.get(),
            "loop_group": self.get_group_positions(self.loop_tree),
            "once_group": self.get_group_positions(self.once_tree)
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
        self.loop_positions = self.get_group_positions(self.loop_tree)
        self.once_positions = self.get_group_positions(self.once_tree)

        if not self.loop_positions and (not self.enable_once_group_var.get() or not self.once_positions):
            messagebox.showwarning("警告", "请至少添加一个循环组坐标！")
            return

        # 获取参数
        try:
            self.interval = float(self.interval_var.get())
            self.switch_delay = float(self.switch_delay_var.get())
            self.random_delay = self.random_delay_var.get()
            self.random_max = float(self.random_max_var.get())
            self.loop_mode = self.loop_mode_var.get()
            self.enable_once = self.enable_once_group_var.get()
        except ValueError as e:
            messagebox.showerror("错误", f"参数格式错误: {e}")
            return

        self.is_clicking = True
        self.total_clicks = 0
        self.start_time = time.time()

        # 启动点击线程
        self.click_thread = threading.Thread(target=self.click_loop_with_groups)
        self.click_thread.daemon = True
        self.click_thread.start()

        # 更新UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        self.add_log(f"开始抢票")
        if self.enable_once and self.once_positions:
            self.add_log(f"阶段1: 执行单次组 ({len(self.once_positions)}个坐标)")
        self.add_log(f"阶段2: 循环执行循环组 ({len(self.loop_positions)}个坐标, 模式:{self.loop_mode})")

    def click_loop_with_groups(self):
        """分组点击循环"""
        # 先执行单次组
        if self.enable_once and self.once_positions:
            self.update_stage("执行单次组")
            for pos in self.once_positions:
                if not self.is_clicking:
                    break
                # 执行单次组内的轮换
                for _ in range(pos['clicks']):
                    if not self.is_clicking:
                        break
                    self.perform_click(pos)
                    time.sleep(self.interval)
            self.add_log("单次组执行完成")

        # 执行循环组
        if self.loop_positions and self.is_clicking:
            self.update_stage("循环执行循环组")
            self.add_log(f"开始循环执行 {len(self.loop_positions)} 个坐标")

            # 根据模式构建点击队列
            while self.is_clicking:
                if self.loop_mode == "rotation":
                    # 轮换模式：按顺序每个坐标点击指定次数
                    for pos in self.loop_positions:
                        if not self.is_clicking:
                            break
                        for _ in range(pos['clicks']):
                            if not self.is_clicking:
                                break
                            self.perform_click(pos)
                            time.sleep(self.interval)
                        if self.switch_delay > 0 and self.is_clicking:
                            time.sleep(self.switch_delay)

                elif self.loop_mode == "sequence":
                    # 顺序模式：每个坐标点1次
                    for pos in self.loop_positions:
                        if not self.is_clicking:
                            break
                        self.perform_click(pos)
                        time.sleep(self.interval)
                    if self.switch_delay > 0 and self.is_clicking:
                        time.sleep(self.switch_delay)

                elif self.loop_mode == "random":
                    # 随机模式：随机选择
                    if not self.is_clicking:
                        break
                    pos = random.choice(self.loop_positions)
                    self.perform_click(pos)
                    time.sleep(self.interval)

        self.stop_clicking()

    def perform_click(self, pos):
        """执行点击"""
        try:
            pyautogui.click(pos['x'], pos['y'])
            self.total_clicks += 1

            # 更新显示
            self.update_display(pos)

            # 随机延迟
            if self.random_delay and self.random_max > 0:
                extra_delay = random.uniform(-self.random_max, self.random_max)
                if extra_delay > 0:
                    time.sleep(extra_delay)

        except Exception as e:
            self.add_log(f"点击错误: {e}")

    def update_display(self, current_pos):
        """更新显示"""

        def update():
            self.count_label.config(text=f"总点击次数: {self.total_clicks}")
            self.current_pos_label.config(text=f"当前坐标: ({current_pos['x']}, {current_pos['y']})")

            if self.total_clicks % 50 == 0:
                elapsed = time.time() - self.start_time
                rate = self.total_clicks / elapsed if elapsed > 0 else 0
                self.add_log(f"进度: 已点击{self.total_clicks}次, 速率:{rate:.1f}次/秒")

        self.root.after(0, update)

    def update_stage(self, stage):
        """更新阶段"""

        def update():
            self.stage_label.config(text=f"阶段: {stage}")

        self.root.after(0, update)

    def stop_clicking(self):
        """停止点击"""
        if not self.is_clicking:
            return

        self.is_clicking = False

        # 显示统计
        elapsed = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        if elapsed > 0:
            rate = self.total_clicks / elapsed if elapsed > 0 else 0
            self.add_log(f"========== 抢票结束 ==========")
            self.add_log(f"总点击次数: {self.total_clicks}")
            self.add_log(f"总耗时: {elapsed:.1f}秒")
            self.add_log(f"平均速率: {rate:.1f}次/秒")

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')


if __name__ == "__main__":
    try:
        import pyautogui
    except ImportError:
        print("请先安装依赖: pip install pyautogui")
        exit(1)

    root = tk.Tk()
    app = TicketClickerGUI(root)
    root.mainloop()