#!/usr/bin/env python3
"""
Virtual Dataset Generator - 生成10万级虚拟数据集用于网页荷载测试
用法: python dataset_generator.py
"""

import os, json, random, uuid, sys
import numpy as np
import cv2
import yaml
from pathlib import Path
from tqdm import tqdm

class DatasetGenerator:
    def __init__(self, num_robots=4, num_effectors=4, num_scenes=6, num_object_categories=8, target_video_size_kb = 100, max_depth=1):
        # 生成随机但合理的机器人名称
        robot_prefixes = ['unitree', 'boston', 'agility', 'pal', 'fetch', 'clearpath']
        robot_models = ['g1', 'h1', 'spot', 'atlas', 'pepper', 'cassie', 'digit', 'tiago', 'freight']
        self.robots = [f"{random.choice(robot_prefixes)}_{random.choice(robot_models)}" 
                      for _ in range(num_robots)]
        
        # 生成末端执行器类型
        gripper_types = ['finger', 'jaw', 'claw', 'pinch']
        self.effectors = [f"{random.choice(['two', 'three', 'five'])}_{random.choice(gripper_types)}_gripper" 
                         if i < num_effectors - 1 else 'suction_cup'
                         for i in range(num_effectors)]
        
        # 场景类型
        self.scenes = ['home', 'restaurant', 'office', 'warehouse', 'laboratory', 'kitchen', 
                      'factory', 'hospital', 'store', 'cafe'][:num_scenes]
        
        # 动作
        self.actions = ['grasp', 'place', 'pick', 'push', 'pull', 'rotate', 'lift', 'lower', 
                       'slide', 'insert', 'remove', 'flip']
        
        # 生成随机对象分类
        base_categories = ['fruit', 'container', 'furniture', 'food', 'toy', 'utensil', 
                          'textile', 'beverage', 'tool', 'electronics', 'stationery', 'kitchenware']
        selected_categories = base_categories[:num_object_categories]
        
        self.objects = {}
        for cat in selected_categories:
            # 为每个类别生成3-5个对象
            num_items = random.randint(3, 5)
            self.objects[cat] = [f"{cat}_{chr(97+i)}" for i in range(num_items)]

        self.target_video_size_kb = target_video_size_kb
        self.max_depth = max_depth
        
    def generate_yml(self, idx):
        cat1 = random.choice(list(self.objects.keys()))
        obj1 = random.choice(self.objects[cat1])
        cat2 = random.choice(list(self.objects.keys()))
        obj2 = random.choice(self.objects[cat2])
        
        action = random.choice(['pick', 'place', 'stack', 'move', 'arrange'])
        task = f"{action}_{obj1}_to_{obj2}_{random.randint(1000,9999)}"
        
        objects = []
        for cat, obj in [(cat1, obj1), (cat2, obj2)]:
            # 为每个对象随机选择一个深度，范围从1到max_depth
            obj_depth = random.randint(1, self.max_depth)
            
            # 构建对象层级
            obj_entry = {
                'object_name': obj,
                'level1': cat,
                'level2': None,
                'level3': None,
                'level4': None,
                'level5': None
            }
            
            # 根据深度填充层级
            if obj_depth >= 1:
                obj_entry['level1'] = cat
            if obj_depth >= 2:
                obj_entry['level2'] = obj
            if obj_depth >= 3:
                obj_entry['level3'] = f"{obj}_sub1"
            if obj_depth >= 4:
                obj_entry['level4'] = f"{obj}_sub2"
            if obj_depth >= 5:
                obj_entry['level5'] = f"{obj}_sub3"
                
            objects.append(obj_entry)
        
        return {
            'dataset_name': task,
            'dataset_uuid': str(uuid.uuid4()),
            'task_descriptions': [f'{action}_the_{obj1}_and_place_in_the_{obj2}'],
            'scene_type': random.sample(self.scenes, random.randint(1, min(3, len(self.scenes)))),
            'atomic_actions': random.sample(self.actions, random.randint(2, min(4, len(self.actions)))),
            'objects': objects,
            'operation_platform_height': round(random.uniform(70, 90), 1),
            'device_model': [random.choice(self.robots)],
            'end_effector_type': random.choice(self.effectors)
        }, task
    
    def generate_video(self, path, name):
        """生成可靠播放的MP4视频 - 使用ffmpeg命令行方案"""
        import subprocess
        import tempfile
        
        # 视频参数 - 以KB为单位
        target_kb = self.target_video_size_kb
        
        if target_kb < 50:  # < 50KB: 极小视频
            width, height = 160, 90
            duration = 1.0
            fps = 15
        elif target_kb < 100:  # 50-100KB: 小视频
            width, height = 240, 135
            duration = 1.5
            fps = 20
        elif target_kb < 200:  # 100-200KB: 标准小视频
            width, height = 320, 180
            duration = 2.0
            fps = 24
        elif target_kb < 500:  # 200-500KB: 中等视频
            width, height = 480, 270
            duration = 2.5
            fps = 25
        elif target_kb < 1024:  # 500KB-1MB: 较大视频
            width, height = 640, 360
            duration = 3.0
            fps = 30
        else:  # > 1MB: 限制最大值
            width, height = 640, 360
            duration = 3.0
            fps = 30
            print(f"警告: 目标大小 {target_kb:.0f}KB ({target_kb/1024:.2f}MB) 超过推荐值(1MB)，已限制为最大参数")

        total_frames = int(fps * duration)
        
        # 先用OpenCV生成原始帧到临时AVI（使用MJPEG，最通用）
        temp_avi = str(path).replace('.mp4', '_temp.avi')
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(temp_avi, fourcc, fps, (width, height))
        
        if not out.isOpened():
            # 如果MJPEG也失败，直接用ffmpeg生成
            cmd = [
                'ffmpeg', '-y', '-f', 'lavfi',
                '-i', f'color=c=blue:s={width}x{height}:d={duration}',
                '-c:v', 'libx264', '-preset', 'ultrafast',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                str(path)
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True, timeout=10)
            except:
                # 最后备选：生成一个占位文件
                Path(path).touch()
            return
        
        # 生成视频帧
        for frame_idx in range(total_frames):
            progress = frame_idx / total_frames
            color_b = int(255 * (1 - progress))
            color_g = int(255 * progress)
            color_r = 100
            
            frame = np.full((height, width, 3), (color_b, color_g, color_r), dtype=np.uint8)
            
            text = f"Frame {frame_idx+1}/{total_frames}"
            cv2.putText(frame, text, (10, height//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            out.write(frame)
        
        out.release()
        
        # 用ffmpeg转换为标准H.264 MP4
        try:
            cmd = [
                'ffmpeg', '-y', '-i', temp_avi,
                '-c:v', 'libx264', '-preset', 'ultrafast',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                str(path)
            ]
            result = subprocess.run(cmd, capture_output=True, check=True, timeout=10)
            os.remove(temp_avi)  # 删除临时文件
        except subprocess.TimeoutExpired:
            # 超时，保留临时文件
            if os.path.exists(temp_avi):
                os.rename(temp_avi, str(path))
        except subprocess.CalledProcessError:
            # ffmpeg失败，保留AVI格式
            if os.path.exists(temp_avi):
                os.rename(temp_avi, str(path))
        except Exception as e:
            # 其他错误，尝试保留任何生成的文件
            if os.path.exists(temp_avi):
                os.rename(temp_avi, str(path))

        # 返回生成文件的实际大小（字节）
        if os.path.exists(path):
            return os.path.getsize(path)
        return 0    

    def generate(self, num, output_dir):
        output = Path(output_dir)
        videos = output / 'videos'
        info = output / 'dataset_info'
        videos.mkdir(parents=True, exist_ok=True)
        info.mkdir(parents=True, exist_ok=True)
        # 初始化统计变量（内存高效的在线算法）
        count = 0
        mean_size = 0.0
        
        index = []
        
        for i in tqdm(range(num), desc="生成中"):
            yml_data, task = self.generate_yml(i)
            robot = yml_data['device_model'][0]
            effector = yml_data['end_effector_type']
            base = f"{robot}_{effector}_{task}"
            
            yml_file = f"{base}.yml"
            with open(info / yml_file, 'w') as f:
                yaml.dump(yml_data, f, default_flow_style=False, sort_keys=False)
            
            file_size = self.generate_video(str(videos / f"{base}.mp4"), task)
            count += 1
            mean_size += (file_size - mean_size) / count
            index.append(yml_file)
        
        with open(info / 'data_index.json', 'w') as f:
            json.dump(index, f, indent=2)

        avg_size_mb = mean_size / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"视频文件平均大小: {avg_size_mb:.2f} MB")
        print(f"{'='*60}")

    def calculate_folder_stats(self, output_dir):
        """使用内存高效算法统计文件夹大小"""
        output = Path(output_dir)
        
        # 统计变量（内存高效的在线算法）
        total_size = 0
        videos_size = 0
        info_size = 0
        
        mp4_count = 0
        mp4_mean = 0.0
        
        meta_count = 0  # JSON + YML
        meta_mean = 0.0
        
        print(f"\n{'='*60}")
        print("正在统计文件夹大小...")
        print(f"{'='*60}")
        
        # 统计 videos 文件夹
        videos_dir = output / 'videos'
        if videos_dir.exists():
            for file in videos_dir.iterdir():
                if file.is_file():
                    size = file.stat().st_size
                    videos_size += size
                    total_size += size
                    
                    if file.suffix == '.mp4':
                        mp4_count += 1
                        mp4_mean += (size - mp4_mean) / mp4_count
        
        # 统计 dataset_info 文件夹
        info_dir = output / 'dataset_info'
        if info_dir.exists():
            for file in info_dir.iterdir():
                if file.is_file():
                    size = file.stat().st_size
                    info_size += size
                    total_size += size
                    
                    if file.suffix in ['.json', '.yml', '.yaml']:
                        meta_count += 1
                        meta_mean += (size - meta_mean) / meta_count
        
        # 转换为易读格式
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.2f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.2f} TB"
        
        # 输出统计结果
        print(f"\n{'='*60}")
        print("文件夹统计结果:")
        print(f"{'='*60}")
        print(f"总大小:              {format_size(total_size)}")
        print(f"├─ videos/           {format_size(videos_size)}")
        print(f"└─ dataset_info/     {format_size(info_size)}")
        print(f"\n文件类型平均大小:")
        print(f"├─ MP4 视频          {format_size(mp4_mean)} (共 {mp4_count} 个)")
        print(f"└─ JSON/YML 元数据   {format_size(meta_mean)} (共 {meta_count} 个)")
        print(f"{'='*60}\n")

def get_input(prompt, default):
    """获取用户输入，回车使用默认值"""
    user_input = input(f"{prompt} [默认: {default}]: ").strip()
    if user_input == "":
        return str(default)
    return user_input

def main():
    print("=" * 60)
    print("虚拟数据集生成器")
    print("=" * 60)
    print("提示: 直接按回车使用默认值\n")
    
    # 询问参数
    try:
        num_datasets = int(get_input("数据集数量", "100"))
        if num_datasets < 1 or num_datasets > 100000:
            print("错误: 数量必须在1-100000之间")
            return
    except ValueError:
        print("错误: 请输入有效数字")
        return
    
    try:
        num_robots = int(get_input("机器人类型数量", "4"))
    except ValueError:
        num_robots = 4
    
    try:
        num_effectors = int(get_input("末端执行器类型数量", "4"))
    except ValueError:
        num_effectors = 4
    
    try:
        num_scenes = int(get_input("场景类型数量", "6"))
    except ValueError:
        num_scenes = 6
    
    try:
        num_categories = int(get_input("对象分类数量", "8"))
    except ValueError:
        num_categories = 8

    # 获取操作目标目录最大深度
    while True:
        try:
            max_depth = int(get_input("操作目标目录最大深度(1-5)", "1"))
            if max_depth < 1 or max_depth > 5:
                print("错误: 最大深度必须在1-5之间")
                continue
            if max_depth >= num_datasets:
                print(f"错误: 最大深度({max_depth})必须小于数据集数量({num_datasets})")
                continue
            break
        except ValueError:
            print("错误: 请输入有效数字")
            continue

    try:
        target_size_kb = float(get_input("目标视频大小(KB)", "100"))
        if target_size_kb <= 0:
            print("错误: 大小必须大于0")
            return
        if target_size_kb > 1024:
            print(f"⚠️  警告: 输入 {target_size_kb}KB ({target_size_kb/1024:.2f}MB) 超过推荐值(1MB)")
            confirm = input("是否继续? (y/n) [默认: n]: ").lower()
            if confirm not in ['y', 'yes']:
                return
    except ValueError:
        target_size_kb = 100  # 默认 100KB
    
    # 创建输出目录 - 输出到 docs/assets
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_assets_dir = project_root / 'docs' / 'assets'
    
    # 确保 docs/assets 目录存在
    docs_assets_dir.mkdir(parents=True, exist_ok=True)
    
    # 输出到 docs/assets
    output_dir = docs_assets_dir
    
    print(f"\n⚠️  注意: 将生成到 docs/assets/ 目录")
    print(f"   路径: {output_dir.absolute()}")
    
    # 检查目录是否已有数据
    videos_dir = output_dir / 'videos'
    info_dir = output_dir / 'dataset_info'
    
    if videos_dir.exists() and any(videos_dir.iterdir()):
        print(f"\n⚠️  警告: {videos_dir} 目录已存在且包含文件")
        overwrite = input("是否覆盖现有数据? (y/n) [默认: n]: ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("已取消生成")
            return
        
        # 清空现有数据
        import shutil
        if videos_dir.exists():
            print(f"正在清空 {videos_dir.name}/...")
            shutil.rmtree(videos_dir)
        if info_dir.exists():
            print(f"正在清空 {info_dir.name}/...")
            shutil.rmtree(info_dir)
    
    print(f"\n生成配置:")
    print(f"  数据集数量: {num_datasets}")
    print(f"  机器人类型: {num_robots}")
    print(f"  末端执行器: {num_effectors}")
    print(f"  场景类型: {num_scenes}")
    print(f"  对象分类: {num_categories}")
    print(f"  操作目标目录最大深度: {max_depth}")
    print(f"  输出目录: docs/assets/")
    print(f"  目标视频大小: {target_size_kb} KB ({target_size_kb/1024:.2f} MB)")
    print()
    
    # 生成数据
    print("开始生成...")
    generator = DatasetGenerator(num_robots, num_effectors, num_scenes, num_categories, target_size_kb, max_depth)
    generator.generate(num_datasets, str(output_dir))

    # 计算文件夹的总大小和平均大小
    generator.calculate_folder_stats(str(output_dir))
    
    print(f"\n✓ 完成! 数据已生成到 docs/assets/ 目录")
    print(f"   完整路径: {output_dir.absolute()}")
    print(f"\n💡 提示: 可以通过以下方式查看:")
    print(f"   1. 启动开发服务器: python3 scripts/dev_server.py")
    print(f"   2. 或直接打开: docs/index.html")

if __name__ == '__main__':
    main()