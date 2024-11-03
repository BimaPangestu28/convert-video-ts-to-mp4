import os
import subprocess
import json
from datetime import datetime

def get_video_info(input_file):
    """Get video duration and details using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            input_file
        ]
        result = subprocess.check_output(cmd).decode('utf-8')
        return json.loads(result)
    except Exception as e:
        print(f"Error getting video info: {str(e)}")
        return None

def generate_output_filename(input_file, output_dir):
    """Generate output filename with timestamp"""
    input_filename = os.path.basename(input_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{os.path.splitext(input_filename)[0]}_{timestamp}.mp4"
    return os.path.join(output_dir, output_filename)

def calculate_target_bitrate(duration, target_size_mb):
    """Calculate target bitrate for desired file size"""
    target_size_bits = target_size_mb * 8 * 1024 * 1024
    bitrate = int(target_size_bits / duration)
    audio_bitrate = 128000  # 128k audio
    video_bitrate = max(500000, bitrate - audio_bitrate)  # minimum 500k video
    return video_bitrate, audio_bitrate

def print_conversion_result(result, original_size=None):
    """Print conversion result details"""
    if result['success']:
        print(f"\nSuccessfully converted: {result['input_file']}")
        if original_size:
            print(f"Original size: {original_size:.2f} MB")
        print(f"Output size: {result['size']:.2f} MB")
        if original_size:
            print(f"Space saved: {(original_size - result['size']):.2f} MB")
        print(f"Duration: {result.get('duration', 'Unknown')}")
        print(f"Compression ratio: {result['compression_ratio']:.2f}x")
        print(f"Location: {result['output_file']}")
    else:
        print(f"\nFailed to convert {result['input_file']}")
        print(f"Error: {result['error']}")

def print_summary(stats):
    """Print conversion summary"""
    print("\nConversion Summary:")
    print(f"Total files processed: {stats['total']}")
    print(f"Successful conversions: {stats['successful']}")
    print(f"Failed conversions: {stats['failed']}")
    print(f"Average compression ratio: {stats['avg_compression']:.2f}x")
    print(f"Total time elapsed: {stats['elapsed_time']:.2f} seconds")
    print(f"Average time per file: {stats['avg_time']:.2f} seconds")
    
    if stats.get('deleted_files'):
        print(f"\nCleanup Summary:")
        print(f"Files deleted: {stats['deleted_files']}")
        print(f"Total space saved: {stats['saved_space']:.2f} MB")