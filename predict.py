import os
import subprocess
from typing import List
from cog import BasePredictor, Input, Path

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
        
        # 构建过滤器
        filter_parts = []
        input_count = 1
        
        # 如果有音频文件，替换原音轨
        if audio_file:
            cmd.extend(["-c:v", "copy"])  # 复制视频流
            cmd.extend(["-c:a", "aac"])   # 重新编码音频
            cmd.extend(["-map", "0:v:0"]) # 使用第一个输入的视频
            cmd.extend(["-map", "1:a:0"]) # 使用第二个输入的音频
            input_count = 2
        
        # 如果有字幕文件，烧录字幕
        if subtitle_file:
            if audio_file:
                # 有音频的情况：video + audio + subtitle
                cmd.extend(["-vf", f"subtitles={subtitle_file}"])
            else:
                # 只有字幕的情况：video + subtitle
                cmd.extend(["-vf", f"subtitles={subtitle_file}"])
                cmd.extend(["-c:a", "copy"])  # 保持原音频
        
        # 如果都没有额外文件，直接复制
        if not audio_file and not subtitle_file:
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
                check=True
            )
            print(f"FFmpeg输出: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg错误: {e.stderr}")
            raise Exception(f"视频处理失败: {e.stderr}")
        
        return Path(output_path)