import os
import json
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
from moviepy import VideoFileClip, AudioFileClip

# 原有处理逻辑封装为函数，支持日志回调
def process_folders(input_dict, output_dict, log_func=print, update_total=None):
    if not os.path.exists(output_dict):
        os.makedirs(output_dict)
        log_func(f"创建输出文件夹: {output_dict}")
    else:
        log_func(f"输出文件夹已存在: {output_dict}")

    if not os.path.exists(input_dict):
        log_func(f"输入文件夹不存在: {input_dict}")
        return

    folders = os.listdir(input_dict)
    total = len(folders)
    log_func(f"共检测到 {total} 个视频文件夹，开始处理...")
    for idx, folder in enumerate(folders):
        if update_total:
            update_total(idx)
        subfolder_path = os.path.join(input_dict, folder)
        if not os.path.isdir(subfolder_path):
            continue
        log_func(f"[{idx+1}/{total}] 处理：{folder}")
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
            log_func(f"  跳过：m4s文件不足2个")
            continue
        m4s_paths = [os.path.join(subfolder_path, f) for f in m4s_files]
        tmp_files = []
        for idx2, m4s_path in enumerate(m4s_paths):
            try:
                with open(m4s_path, 'rb') as f:
                    data = f.read()[9:]
                tmp_path = os.path.join(output_dict, f"{video_title}_tmp{idx2}.tmp")
                with open(tmp_path, 'wb') as f:
                    f.write(data)
                tmp_files.append(tmp_path)
            except Exception as e:
                log_func(f"  跳过：m4s转临时文件失败")
        if len(tmp_files) < 2:
            log_func(f"  跳过：临时文件不足")
            continue
        # 尝试识别哪个是视频，哪个是音频
        video_file = audio_file = None
        for f in tmp_files:
            try:
                clip = VideoFileClip(f)
                clip.close()
                video_file = f
            except Exception:
                audio_file = f
        if not video_file or not audio_file:
            log_func(f"  跳过：无法识别视频或音频文件")
            for p in tmp_files:
                try:
                    os.remove(p)
                except Exception:
                    pass
            continue
        try:
            video_clip = VideoFileClip(video_file)
            audio_clip = AudioFileClip(audio_file)
            video_clip.audio = audio_clip
            output_path = os.path.join(output_dict, f"{video_title}.mp4")
            video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            log_func(f"  合成成功: {output_path}")
            video_clip.close()
            audio_clip.close()
        except Exception as e:
            log_func(f"  合成失败: {e}")
        # 清理临时文件
        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass
    if update_total:
        update_total(total)
    log_func("全部处理完成！")

# Tkinter界面
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("B站m4s转mp4工具 made by Fredrick-LX")
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value="output")

        tk.Label(root, text="缓存文件夹:").grid(row=0, column=0, sticky='e')
        tk.Entry(root, textvariable=self.input_var, width=50).grid(row=0, column=1)
        tk.Button(root, text="选择", command=self.choose_input).grid(row=0, column=2)

        tk.Label(root, text="输出文件夹:").grid(row=1, column=0, sticky='e')
        tk.Entry(root, textvariable=self.output_var, width=50).grid(row=1, column=1)
        tk.Button(root, text="选择", command=self.choose_output).grid(row=1, column=2)

        tk.Button(root, text="开始转换", command=self.start_process).grid(row=2, column=1, pady=5)

        # 总进度条
        tk.Label(root, text="总进度:").grid(row=3, column=0, sticky='e')
        self.total_progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.total_progress.grid(row=3, column=1, columnspan=2, sticky='w', pady=2)

        self.log_text = scrolledtext.ScrolledText(root, width=70, height=18, state='disabled')
        self.log_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        self.total_count = 0
        self.current_index = 0

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

    def update_total_progress(self, value):
        self.total_progress['value'] = value
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
        # 统计总数
        try:
            folders = [f for f in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, f))]
            self.total_count = len(folders)
        except Exception:
            self.total_count = 0
        self.total_progress['maximum'] = self.total_count
        self.total_progress['value'] = 0
        self.current_index = 0
        threading.Thread(target=self.threaded_process, args=(input_path, output_path), daemon=True).start()

    def threaded_process(self, input_path, output_path):
        def log_func(msg):
            self.log(msg)
        def update_total(idx):
            self.update_total_progress(idx)
        process_folders(input_path, output_path, log_func, update_total)

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()

