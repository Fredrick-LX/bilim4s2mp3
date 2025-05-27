import os
import json
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading

# 原有处理逻辑封装为函数，支持日志回调
def process_folders(input_dict, output_dict, log_func=print):
    if not os.path.exists(output_dict):
        os.makedirs(output_dict)
        log_func(f"创建输出文件夹: {output_dict}")
    else:
        log_func(f"输出文件夹已存在: {output_dict}")

    if not os.path.exists(input_dict):
        log_func(f"输入文件夹不存在: {input_dict}")
        return

    folders = os.listdir(input_dict)
    for folder in folders:
        subfolder_path = os.path.join(input_dict, folder)
        if not os.path.isdir(subfolder_path):
            continue
        videoinfo_path = os.path.join(subfolder_path, '.videoinfo')
        video_title = folder
        if os.path.exists(videoinfo_path):
            try:
                with open(videoinfo_path, 'r', encoding='utf-8') as vf:
                    info = json.load(vf)
                    if 'title' in info:
                        video_title = info['title']
                        video_title = re.sub(r'[\\/:*?\"<>|]', '_', video_title)
            except Exception:
                pass
        m4s_files = [f for f in os.listdir(subfolder_path) if f.endswith('.m4s')]
        if len(m4s_files) < 2:
            continue
        m4s_paths = [os.path.join(subfolder_path, f) for f in m4s_files]
        sizes = [os.path.getsize(p) for p in m4s_paths]
        min_idx = sizes.index(min(sizes))
        target_m4s = m4s_paths[min_idx]
        log_func(f"[{folder}] 视频名: {video_title}")
        log_func(f"  选中: {m4s_files[min_idx]} -> 输出: {video_title}.mp3")
        try:
            with open(target_m4s, 'rb') as f:
                data = f.read()
            data = data[9:]
            output_path = os.path.join(output_dict, f"{video_title}.mp3")
            with open(output_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            log_func(f"  处理失败: {e}")
    log_func("全部处理完成！")

# Tkinter界面
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("B站m4s转mp3工具 made by Highmore")
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value="output")

        tk.Label(root, text="缓存文件夹:").grid(row=0, column=0, sticky='e')
        tk.Entry(root, textvariable=self.input_var, width=50).grid(row=0, column=1)
        tk.Button(root, text="选择", command=self.choose_input).grid(row=0, column=2)

        tk.Label(root, text="输出文件夹:").grid(row=1, column=0, sticky='e')
        tk.Entry(root, textvariable=self.output_var, width=50).grid(row=1, column=1)
        tk.Button(root, text="选择", command=self.choose_output).grid(row=1, column=2)

        tk.Button(root, text="开始转换", command=self.start_process).grid(row=2, column=1, pady=5)

        self.log_text = scrolledtext.ScrolledText(root, width=70, height=20, state='disabled')
        self.log_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    def choose_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_var.set(path)

    def choose_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def start_process(self):
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        if not input_path or not output_path:
            messagebox.showwarning("提示", "请输入输入和输出文件夹路径！")
            return
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        threading.Thread(target=process_folders, args=(input_path, output_path, self.log), daemon=True).start()

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()

