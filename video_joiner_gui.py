import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import glob
import threading
from tkinter.ttk import Progressbar
import random

class VideoMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Merger Tool")
        self.root.geometry("600x400")
        
        # Biến lưu trữ đường dẫn
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.progress = tk.DoubleVar(value=0)
        
        # Tạo giao diện
        self.create_widgets()
        
    def create_widgets(self):
        # Frame cho input folder
        tk.Label(self.root, text="Input Folder:").pack(pady=10)
        tk.Entry(self.root, textvariable=self.input_folder, width=50).pack()
        tk.Button(self.root, text="Browse", command=self.browse_input).pack(pady=5)
        
        # Frame cho output folder
        tk.Label(self.root, text="Output Folder:").pack(pady=10)
        tk.Entry(self.root, textvariable=self.output_folder, width=50).pack()
        tk.Button(self.root, text="Browse", command=self.browse_output).pack(pady=5)
        
        # Nút Action
        tk.Button(self.root, text="Merge Videos", command=self.start_merge, 
                 bg="green", fg="black", width=20).pack(pady=20)
        
        # Thanh tiến trình
        self.progress_bar = Progressbar(self.root, variable=self.progress, 
                                      maximum=100, length=400)
        self.progress_bar.pack(pady=10)
        
    def browse_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)
            
    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)
            
    def get_video_files(self, folder):
        # Lấy danh sách các file video (hỗ trợ các định dạng phổ biến)
        video_extensions = ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(glob.glob(os.path.join(folder, ext)))
        # Chọn ngẫu nhiên thứ tự các video
        random.shuffle(video_files)
        return video_files
        
    def merge_videos(self):
        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()
        
        if not input_folder or not output_folder:
            messagebox.showerror("Error", "Please select both input and output folders!")
            return
            
        video_files = self.get_video_files(input_folder)
        if not video_files:
            messagebox.showerror("Error", "No video files found in the input folder!")
            return
            
        # Tạo file danh sách tạm thời cho FFmpeg
        temp_list = os.path.join(output_folder, "video_list.txt")
        with open(temp_list, 'w', encoding='utf-8') as f:
            for video in video_files:
                f.write(f"file '{video}'\n")
                
        # Đường dẫn file đầu ra
        output_file = os.path.join(output_folder, f"merged_video_{random.randint(1000, 9999)}.mp4")
        
        # Lệnh FFmpeg để ghép video với re-encoding
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list,
            '-c:v', 'libx264',  # Mã hóa lại video bằng libx264
            '-c:a', 'aac',      # Mã hóa lại audio bằng AAC
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1',
            '-r', '30',         # Chuẩn hóa frame rate thành 30fps
            '-preset', 'medium',# Tốc độ mã hóa
            '-crf', '23',       # Chất lượng video (23 là chất lượng tốt, cân bằng kích thước file)
            output_file
        ]
        
        try:
            # Chạy lệnh FFmpeg
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, universal_newlines=True)
            
            # Cập nhật thanh tiến trình (giả lập dựa trên số file)
            total_files = len(video_files)
            for i in range(total_files):
                self.progress.set((i + 1) / total_files * 100)
                self.root.update()
                
            # Chờ quá trình hoàn tất
            stdout, stderr = process.communicate()
            
            # Kiểm tra xem có lỗi không
            if process.returncode == 0:
                messagebox.showinfo("Success", f"Videos merged successfully into {output_file}!")
            else:
                messagebox.showerror("Error", f"Failed to merge videos: {stderr}")
                
            # Xóa file danh sách tạm thời
            if os.path.exists(temp_list):
                os.remove(temp_list)
                
        except FileNotFoundError:
            messagebox.showerror("Error", "FFmpeg not found! Please ensure FFmpeg is installed and added to PATH.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
        finally:
            self.progress.set(0)
            
    def start_merge(self):
        # Chạy quá trình ghép video trong luồng riêng để không làm đơ giao diện
        threading.Thread(target=self.merge_videos, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMergerApp(root)
    root.mainloop()
