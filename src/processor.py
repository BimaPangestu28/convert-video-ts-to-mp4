import os
import subprocess
import tempfile
import shutil
import psutil
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from .constants import COMPRESSION_SETTINGS, DEFAULT_FFMPEG_PARAMS, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, DEFAULT_KEYFRAME_INTERVAL
from .utils import get_video_info, calculate_target_bitrate

class VideoProcessor:
    def __init__(self, cpu_limit=0.1, compression_level=None, target_size=None, quality=23):
        self.cpu_limit = cpu_limit
        self.compression_level = compression_level
        self.target_size = target_size
        self.quality = quality
        self.cores_to_use = self._set_cpu_affinity()
        self._init_ffmpeg_params()

    def _set_cpu_affinity(self):
        """Set CPU affinity based on limit"""
        try:
            process = psutil.Process(os.getpid())
            cpu_count = multiprocessing.cpu_count()
            cores_to_use = max(1, int(cpu_count * self.cpu_limit))
            available_cores = list(range(cpu_count))
            cores_to_use_list = available_cores[:cores_to_use]
            process.cpu_affinity(cores_to_use_list)
            return cores_to_use
        except:
            return 1

    def _init_ffmpeg_params(self):
        """Initialize FFmpeg parameters"""
        self.ffmpeg_params = DEFAULT_FFMPEG_PARAMS.copy()
        self.ffmpeg_params['video_params'] = self.ffmpeg_params['video_params'].copy()
        self.ffmpeg_params['video_params'].extend(['-crf', str(self.quality)])
        self.ffmpeg_params['thread_params'] = ['-threads', str(self.cores_to_use)]

        if self.compression_level:
            self.ffmpeg_params['compression'] = COMPRESSION_SETTINGS[self.compression_level]

    def optimize_video_params(self, video_info):
        """Optimize video parameters based on input analysis"""
        try:
            video_stream = next((s for s in video_info['streams'] 
                               if s['codec_type'] == 'video'), None)
            
            if video_stream:
                width = int(video_stream.get('width', 0))
                height = int(video_stream.get('height', 0))
                
                # Optimize for HD content
                if width >= 1920 or height >= 1080:
                    self.ffmpeg_params['video_params'].extend([
                        '-profile:v', 'high',
                        '-level', '4.1'
                    ])
                else:
                    self.ffmpeg_params['video_params'].extend([
                        '-profile:v', 'main',
                        '-level', '3.1'
                    ])

                # Calculate optimal bitrate based on resolution
                pixels = width * height
                if not self.compression_level and not self.target_size:
                    if pixels > 2073600:  # 1080p
                        self.ffmpeg_params['video_params'].extend([
                            '-b:v', '5000k',
                            '-maxrate', '7500k',
                            '-bufsize', '10000k'
                        ])
                    elif pixels > 921600:  # 720p
                        self.ffmpeg_params['video_params'].extend([
                            '-b:v', '2500k',
                            '-maxrate', '4000k',
                            '-bufsize', '5000k'
                        ])

            return True
        except Exception as e:
            print(f"Error optimizing video parameters: {str(e)}")
            return False

    def create_optimized_chunks(self, input_file, temp_dir, chunk_duration=60):
        """Create optimized chunks for processing"""
        try:
            chunks = []
            video_info = get_video_info(input_file)
            if not video_info:
                return []

            duration = float(video_info['format']['duration'])
            self.optimize_video_params(video_info)

            num_chunks = math.ceil(duration / chunk_duration)
            keyframe_interval = min(chunk_duration, DEFAULT_KEYFRAME_INTERVAL)
            
            print(f"Creating {num_chunks} optimized chunks...")
            with tqdm(total=num_chunks, desc="Splitting video", unit="chunk") as pbar:
                for i in range(num_chunks):
                    start_time = i * chunk_duration
                    chunk_file = os.path.join(temp_dir, f"chunk_{i:03d}.ts")
                    
                    command = [
                        'ffmpeg',
                        '-ss', str(start_time),
                        '-i', input_file,
                        '-t', str(chunk_duration),
                        '-c', 'copy',
                        '-force_key_frames', f'expr:gte(t,n_forced*{keyframe_interval})',
                        '-avoid_negative_ts', '1',
                        '-y',
                        chunk_file
                    ]
                    
                    if os.name != 'nt':  # For Unix/Linux
                        command = ['nice', '-n', '19'] + command

                    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    chunks.append(chunk_file)
                    pbar.update(1)

            return chunks, duration
        except Exception as e:
            print(f"Error creating chunks: {str(e)}")
            return [], None

    def convert_chunk(self, chunk_file, output_file):
        """Convert a single chunk with optimized settings"""
        try:
            command = ['ffmpeg', '-i', chunk_file]
            
            # Add video codec and basic parameters
            command.extend(['-c:v', self.ffmpeg_params['video_codec']])
            
            # Add compression settings if specified
            if self.compression_level:
                settings = self.ffmpeg_params['compression']
                command.extend(settings['scale'].split())
                command.extend(settings['bitrate'].split())
                command.extend(settings['audio'].split())
            elif self.target_size:
                chunk_info = get_video_info(chunk_file)
                if chunk_info:
                    chunk_duration = float(chunk_info['format']['duration'])
                    chunk_target = (self.target_size / self.total_duration) * chunk_duration
                    video_bitrate, audio_bitrate = calculate_target_bitrate(
                        chunk_duration, chunk_target
                    )
                    command.extend([
                        '-b:v', f'{video_bitrate}',
                        '-maxrate', f'{int(video_bitrate * 1.5)}',
                        '-bufsize', f'{video_bitrate * 2}',
                        '-b:a', f'{audio_bitrate}'
                    ])
            else:
                command.extend(self.ffmpeg_params['video_params'])
                command.extend(self.ffmpeg_params['audio_params'])
            
            # Add thread parameters
            command.extend(self.ffmpeg_params['thread_params'])
            command.extend(['-y', output_file])

            if os.name != 'nt':
                command = ['nice', '-n', '19'] + command

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return os.path.exists(output_file)
        except:
            return False

    def merge_chunks(self, chunk_files, final_output):
        """Merge converted chunks into final video"""
        try:
            list_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            for chunk in chunk_files:
                list_file.write(f"file '{chunk}'\n")
            list_file.close()

            command = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file.name,
                '-c', 'copy',
                '-movflags', '+faststart',
                '-y',
                final_output
            ]

            if os.name != 'nt':
                command = ['nice', '-n', '19'] + command

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.unlink(list_file.name)
            return os.path.exists(final_output)
        except:
            return False

    def convert_video(self, input_file, output_dir, chunk_size=None):
        """Convert video with all optimizations"""
        try:
            input_filename = os.path.basename(input_file)
            output_file = os.path.join(
                output_dir, 
                f"{os.path.splitext(input_filename)[0]}_{int(time.time())}.mp4"
            )

            print(f"\nProcessing: {input_filename}")
            print(f"Analyzing video...")
            
            # Create temporary directories
            temp_dir = tempfile.mkdtemp()
            temp_output_dir = tempfile.mkdtemp()

            try:
                # Create optimized chunks
                chunks, duration = self.create_optimized_chunks(
                    input_file, 
                    temp_dir, 
                    chunk_size or min(MAX_CHUNK_SIZE, max(MIN_CHUNK_SIZE, duration / 10))
                )
                
                if not chunks:
                    raise Exception("Failed to create chunks")

                self.total_duration = duration  # Store for target size calculations

                # Convert chunks
                converted_chunks = []
                with tqdm(total=len(chunks), desc="Converting chunks", unit="chunk") as pbar:
                    with ThreadPoolExecutor(max_workers=self.cores_to_use) as executor:
                        futures = []
                        for i, chunk in enumerate(chunks):
                            chunk_output = os.path.join(temp_output_dir, f"converted_{i:03d}.mp4")
                            future = executor.submit(self.convert_chunk, chunk, chunk_output)
                            futures.append((future, chunk_output))

                        for future, chunk_output in futures:
                            if future.result():
                                converted_chunks.append(chunk_output)
                                pbar.update(1)
                            else:
                                raise Exception("Failed to convert chunk")

                # Merge chunks
                print("\nMerging chunks...")
                if not self.merge_chunks(converted_chunks, output_file):
                    raise Exception("Failed to merge chunks")

                # Calculate results
                input_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
                output_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
                compression_ratio = input_size / output_size
                
                return {
                    'success': True,
                    'input_file': input_filename,
                    'output_file': output_file,
                    'size': output_size,
                    'duration': f"{duration:.1f} seconds" if duration else "Unknown",
                    'compression_ratio': compression_ratio
                }

            finally:
                # Clean up temporary directories
                shutil.rmtree(temp_dir, ignore_errors=True)
                shutil.rmtree(temp_output_dir, ignore_errors=True)

        except Exception as e:
            return {
                'success': False,
                'input_file': input_filename,
                'error': str(e)
            }