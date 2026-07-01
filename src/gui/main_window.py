# -*- coding: utf-8 -*-
"""GUI main window using Tkinter (Python standard library)."""

import os, sys, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

class MainWindow:
    """Main application window for the PDMS-to-RELAP5 converter."""
    TITLE = "PDMS → RELAP5 输入卡自动转换与生图程序"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.TITLE)
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        ttk.Style().theme_use("clam")
        self.input_path = tk.StringVar()
        self.boundary_path = tk.StringVar()
        self.output_dir = tk.StringVar(value="./output")
        self._diagram_image = None
        self._build_menu()
        self._build_widgets()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="选择 PDMS 文件...", command=self._browse_input)
        file_menu.add_command(label="选择边界文件...", command=self._browse_boundary)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

    def _build_widgets(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="PDMS 导出文件:").grid(row=0, column=0, sticky=tk.W, pady=(0, 2))
        file_frame = ttk.Frame(main)
        file_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))
        ttk.Entry(file_frame, textvariable=self.input_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="浏览...", command=self._browse_input).pack(side=tk.RIGHT, padx=(4, 0))

        ttk.Label(main, text="边界条件 CSV（可选，不选则自动检测悬挂点）:").grid(row=2, column=0, sticky=tk.W, pady=(0, 2))
        bnd_frame = ttk.Frame(main)
        bnd_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))
        ttk.Entry(bnd_frame, textvariable=self.boundary_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bnd_frame, text="浏览...", command=self._browse_boundary).pack(side=tk.RIGHT, padx=(4, 0))

        ttk.Label(main, text="输出目录:").grid(row=4, column=0, sticky=tk.W, pady=(0, 2))
        out_frame = ttk.Frame(main)
        out_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))
        ttk.Entry(out_frame, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_frame, text="浏览...", command=self._browse_output_dir).pack(side=tk.RIGHT, padx=(4, 0))

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))
        self.run_btn = ttk.Button(btn_frame, text="▶  开始转换", command=self._run_conversion)
        self.run_btn.pack(side=tk.LEFT)

        self.diagram_frame = ttk.LabelFrame(main, text="节点化图", padding=4)
        self.diagram_frame.grid(row=7, column=0, columnspan=2, sticky=tk.NSEW, pady=(0, 8))
        self.diagram_canvas = tk.Canvas(self.diagram_frame, bg="#ffffff", highlightthickness=0)
        self.diagram_canvas.pack(fill=tk.BOTH, expand=True)
        self.diagram_canvas.create_text(400, 250, text="点击「开始转换」生成节点化图", font=("Microsoft YaHei", 14), fill="#999999", anchor=tk.CENTER)

        self.status_var = tk.StringVar(value="就绪 — 选择 PDMS 文件后点击「开始转换」，或直接点击从 output/ 目录读取")
        status = ttk.Label(main, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(4, 2))
        status.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=(8, 0))

        main.columnconfigure(0, weight=1)
        main.rowconfigure(7, weight=1)

    def _browse_input(self):
        path = filedialog.askopenfilename(title="选择 PDMS 导出文件", filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.input_path.set(path)

    def _browse_boundary(self):
        path = filedialog.askopenfilename(title="选择边界条件配置文件", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.boundary_path.set(path)

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir.set(path)

    def _run_conversion(self):
        input_file = self.input_path.get().strip()
        # If user selected a file but it doesn't exist, show error
        if input_file and not os.path.isfile(input_file):
            messagebox.showerror("文件不存在", f"找不到文件:\n{input_file}")
            return
        self.run_btn.config(state=tk.DISABLED, text="⏳ 转换中...")
        if input_file:
            self.status_var.set("正在转换...")
        else:
            self.status_var.set("未选择 PDMS 文件，正在从 output/ 目录读取 .i 文件...")
        thread = threading.Thread(target=self._conversion_thread, args=(input_file,), daemon=True)
        thread.start()

    def _conversion_thread(self, input_file: str):
        "Background thread: parse input file or fallback to output directory."
        diagram_path = None
        fallback_msg = ""
        try:
            output_dir = self.output_dir.get()
            from src.parser.relap5_parser import parse_relap5_deck
            from src.diagram.nodalization_diagram import generate_nodalization_diagram

            # Determine the RELAP5 deck file to parse
            deck_path = None
            if input_file and os.path.isfile(input_file):
                deck_path = input_file
            else:
                # Fallback: scan output directory for .i files
                if os.path.isdir(output_dir):
                    for fname in os.listdir(output_dir):
                        if fname.endswith(".i") or fname.endswith(".txt"):
                            candidate = os.path.join(output_dir, fname)
                            if os.path.isfile(candidate):
                                deck_path = candidate
                                break
                # Also try project root
                if not deck_path:
                    for fname in os.listdir("."):
                        if fname.endswith(".i"):
                            candidate = os.path.join(".", fname)
                            if os.path.isfile(candidate):
                                deck_path = candidate
                                break

            if deck_path:
                components = parse_relap5_deck(deck_path)
                diagram_path = os.path.join(output_dir, "nodalization_diagram.png")
                generate_nodalization_diagram(components, diagram_path)
                if not input_file:
                    fallback_msg = f"（数据来源: {deck_path}）"
            else:
                if not input_file:
                    fallback_msg = "未在 output/ 目录中找到 .i 文件，无法生成节点图"

            self.root.after(0, self._conversion_done, True, fallback_msg, diagram_path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, self._conversion_done, False, str(e), None)

    def _conversion_done(self, success: bool, info_msg: str, diagram_path=None):
        self.run_btn.config(state=tk.NORMAL, text="▶  开始转换")
        if success:
            if diagram_path and os.path.isfile(diagram_path):
                self._display_diagram(diagram_path)
                self.status_var.set(f"转换完成 {info_msg}".strip())
            else:
                self.status_var.set(f"转换完成 — 节点化图待模块实现后生成 {info_msg}".strip())
        else:
            self.status_var.set("转换失败")
            messagebox.showerror("错误", f"转换过程中发生错误:\n{info_msg}")

    def _display_diagram(self, path: str):
        img = Image.open(path)
        cw = self.diagram_canvas.winfo_width()
        ch = self.diagram_canvas.winfo_height()
        max_w, max_h = (cw - 20, ch - 20) if cw > 10 and ch > 10 else (860, 500)
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        self._diagram_image = ImageTk.PhotoImage(img)
        self.diagram_canvas.delete("all")
        self.diagram_canvas.create_image(cw // 2, ch // 2, image=self._diagram_image, anchor=tk.CENTER)

    def _show_about(self):
        about_text = f"{self.TITLE}{BSN}{BSN}版本: 0.1.0 (框架){BSN}技术栈: Python 3.9+ / Tkinter / networkx / matplotlib{BSN}{BSN}将 PDMS 三维管道模型数据自动转换为{BSN}RELAP5 热工水力计算输入卡，并生成{BSN}管道网络节点化图。"
        messagebox.showinfo("关于", about_text)


def launch_gui():
    root = tk.Tk()
    app = MainWindow(root)
    try:
        root.mainloop()
    finally:
        root.destroy()
