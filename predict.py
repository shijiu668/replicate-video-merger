import os
import subprocess
from typing import List
from cog import BasePredictor, Input, Path
import chardet

class Predictor(BasePredictor):
    def predict(
        self,
        video_file: Path = Input(description="输入视频文件"),
        audio_file: Path = Input(description="输入音频文件", default=None),
        subtitle_file: Path = Input(description="字幕文件 (.srt)", default=None),
        output_format: str = Input(
            description="输出格式", 
            choices=["mp4", "mov", "avi"], 
            default="mp4"
        ),
    ) -> Path:
        
        # 创建输出文件路径
        output_path = f"/tmp/output.{output_format}"
        
        # 预处理字幕文件（如果存在）
        processed_subtitle_file = None
        if subtitle_file:
            try:
                # 检测字幕文件编码
                with open(subtitle_file, 'rb') as f:
                    raw_data = f.read()
                    encoding = chardet.detect(raw_data)['encoding']
                
                print(f"检测到字幕文件编码: {encoding}")
                
                # 读取并转换为UTF-8
                with open(subtitle_file, 'r', encoding=encoding or 'utf-8') as f:
                    content = f.read()
                
                # 写入UTF-8格式的临时文件
                processed_subtitle_file = "/tmp/subtitle_utf8.srt"
                with open(processed_subtitle_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"字幕文件已转换为UTF-8: {processed_subtitle_file}")
                
            except Exception as e:
                print(f"字幕文件处理警告: {e}")
                # 如果处理失败，使用原文件
                processed_subtitle_file = str(subtitle_file)
        
        # 构建FFmpeg命令
        cmd = ["ffmpeg", "-y"]  # -y 覆盖输出文件
        
        # 添加视频输入
        cmd.extend(["-i", str(video_file)])
        
        # 添加音频输入（如果提供）
        if audio_file:
            cmd.extend(["-i", str(audio_file)])
        
        # 添加字幕输入（如果提供）
        if subtitle_file:
            cmd.extend(["-i", str(subtitle_file)])
        
        # 根据不同情况构建命令
        if processed_subtitle_file:
            # 有字幕：需要重新编码视频以烧录字幕
            # 使用更安全的字幕滤镜，设置字体样式
            subtitle_filter = f"subtitles='{processed_subtitle_file}':force_style='FontSize=24,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,Outline=2,FontName=Arial'"
            cmd.extend(["-vf", subtitle_filter])
            cmd.extend(["-c:v", "libx264"])  # 重新编码视频
            cmd.extend(["-preset", "medium"])  # 编码速度预设
            cmd.extend(["-crf", "23"])  # 质量设置
            
            if audio_file:
                # 有音频：使用新音频
                cmd.extend(["-c:a", "aac"])
                cmd.extend(["-map", "0:v:0"])  # 视频来自输入0
                cmd.extend(["-map", "1:a:0"])  # 音频来自输入1
            else:
                # 无音频：保持原音频
                cmd.extend(["-c:a", "copy"])
                
        elif audio_file:
            # 只有音频，无字幕：替换音轨
            cmd.extend(["-c:v", "copy"])  # 复制视频流
            cmd.extend(["-c:a", "aac"])   # 重新编码音频
            cmd.extend(["-map", "0:v:0"]) # 使用第一个输入的视频
            cmd.extend(["-map", "1:a:0"]) # 使用第二个输入的音频
            
        else:
            # 既无音频也无字幕：直接复制
            cmd.extend(["-c", "copy"])
        
        # 添加输出路径
        cmd.append(output_path)
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 执行FFmpeg命令
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=300  # 5分钟超时
            )
            print(f"FFmpeg输出: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg错误: {e.stderr}")
            raise Exception(f"视频处理失败: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("视频处理超时，请检查文件大小")
        
        return Path(output_path)
