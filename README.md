# 🎫 抢票自动点击器

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v1.0.0-orange.svg)](https://github.com/NCHU-wqy/click/releases)

> 一款功能强大的自动化抢票工具，支持轮换点击、多坐标设置、可调频率等特性。

## 📖 项目简介

这是一个用 Python 编写的图形化抢票辅助工具，通过模拟鼠标点击实现自动化抢票。支持自定义多个点击位置、调整点击频率、轮换点击等高级功能，帮助你在抢票时获得速度优势。

### ✨ 主要特性

- 🖱️ **多坐标轮换点击** - 支持设置多个点击位置，自动轮换
- ⚡ **可调节点击频率** - 0.001秒到1秒可调，支持随机延迟
- 🔄 **多种点击模式** - 轮换模式、随机模式、顺序模式
- 💾 **配置保存** - 自动保存你的设置，下次打开即用
- 🎨 **图形化界面** - 简单易用的 GUI 界面，无需编程知识
- 📊 **实时统计** - 显示点击次数、速率等实时数据
- 🖱️ **特别提示** - 当点击“添加当前鼠标位置”之后，把鼠标移动到需要点击的地方,3秒后会自动记录当前鼠标位置的坐标

## 📥 下载与安装

### 方式一：下载可执行文件（推荐）

👉 **[点击这里下载最新版本](https://github.com/NCHU-wqy/click/releases/latest)** 👈

选择 `TicketClicker.exe` 下载，双击即可运行，**无需安装 Python 环境**。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/NCHU-wqy/click.git

# 进入目录
cd click

# 安装依赖
pip install pyautogui

# 运行程序
python version_3.py
