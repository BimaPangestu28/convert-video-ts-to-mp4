import os
from pathlib import Path
import subprocess
import argparse
import time
import sys
from datetime import datetime
from tqdm import tqdm
import math
import tempfile
import shutil

def get_video_info(input_file):
    """Get video duration and bitrate using ffprobe"""
    try:
        # Get duration
        duration_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_file
        ]
        duration = float(subprocess.check_output(duration_cmd).decode().strip())

        # Get bitrate
        bitrate_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_file
        ]
        try:
            bitrate = int(subprocess.check_output(bitrate_cmd).decode().strip())
        except:
            bitrate = 4000000  # Default to 4Mbps if can't detect

        return duration, bitrate
    except Exception as e:
        print(f"Error getting video info: {str(e)}")
        return None, None

def create_chunks(input_file, chunk_duration=60):
    """Split video into chunks for faster processing"""
    try:
        duration, _ = get_video_info(input_file)
        if not duration:
            return None, None

        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        chunks = []

        # Calculate number of chunks
        num_chunks = math.ceil(duration / chunk_duration)
        
        # Create chunks
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_file = os.path.join(temp_dir, f"chunk_{i:03d}.ts")
            
            command = [
                'ffmpeg',
                '-i', input_file,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-c', 'copy',  # Copy without re-encoding for speed
                '-y',
                chunk_file
            ]
            
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            chunks.append(chunk_file)

        return temp_dir, chunks
    except Exception as e:
        print(f"Error creating chunks: {str(e)}")
        return None, None

def convert_chunk(chunk_file, output_file):
    """Convert a single chunk to MP4"""
    command = [
        'ffmpeg',
        '-i', chunk_file,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-preset', 'medium',
        '-crf', '23',
        '-y',
        output_file
    ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(output_file)

def merge_chunks(chunk_files, final_output):
    """Merge converted chunks into final video"""
    # Create merge file list
    list_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    for chunk in chunk_files:
        list_file.write(f"file '{chunk}'\n")
    list_file.close()

    # Merge chunks
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file.name,
        '-c', 'copy',
        '-y',
        final_output
    ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(list_file.name)
    return os.path.exists(final_output)

def convert_video(input_file, output_dir):
    """Convert a single video file with chunk processing"""
    try:
        input_filename = os.path.basename(input_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{os.path.splitext(input_filename)[0]}_{timestamp}.mp4"
        output_file = os.path.join(output_dir, output_filename)

        print(f"\nProcessing: {input_filename}")
        
        # Get video duration for progress calculation
        duration, _ = get_video_info(input_file)
        if duration:
            print(f"Duration: {duration:.1f} seconds")

        # Create chunks
        print("Splitting video into chunks...")
        temp_dir, chunks = create_chunks(input_file)
        if not chunks:
            raise Exception("Failed to create chunks")

        # Convert chunks with progress bar
        converted_chunks = []
        temp_output_dir = tempfile.mkdtemp()
        
        with tqdm(total=len(chunks), desc="Converting chunks", unit="chunk") as pbar:
            for i, chunk in enumerate(chunks):
                chunk_output = os.path.join(temp_output_dir, f"converted_{i:03d}.mp4")
                if convert_chunk(chunk, chunk_output):
                    converted_chunks.append(chunk_output)
                    pbar.update(1)
                else:
                    raise Exception(f"Failed to convert chunk {i}")

        # Merge converted chunks
        print("\nMerging chunks...")
        if not merge_chunks(converted_chunks, output_file):
            raise Exception("Failed to merge chunks")

        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(temp_output_dir, ignore_errors=True)

        # Get output file size
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # Size in MB
        
        return {
            'success': True,
            'input_file': input_filename,
            'output_file': output_file,
            'size': file_size,
            'duration': f"{duration:.1f} seconds" if duration else "Unknown"
        }

    except Exception as e:
        return {
            'success': False,
            'input_file': input_filename,
            'error': str(e)
        }
    finally:
        # Ensure cleanup of temporary directories
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if 'temp_output_dir' in locals():
            shutil.rmtree(temp_output_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description='Convert .ts video files to .mp4 format with chunk processing')
    parser.add_argument('input', help='Input .ts file or directory containing .ts files')
    parser.add_argument('-o', '--output', help='Output directory for converted files')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='Recursively process directories')
    parser.add_argument('-c', '--chunk-size', type=int, default=60,
                       help='Chunk size in seconds (default: 60)')
    
    args = parser.parse_args()

    # Create results directory
    output_dir = args.output if args.output else os.path.join(os.path.dirname(os.path.abspath(args.input)), 'results')
    os.makedirs(output_dir, exist_ok=True)

    # Collect all files to process
    if os.path.isdir(args.input):
        pattern = '**/*.ts' if args.recursive else '*.ts'
        files = list(Path(args.input).glob(pattern))
    else:
        files = [Path(args.input)]

    if not files:
        print("No .ts files found to convert!")
        return

    print(f"\nFound {len(files)} files to convert")
    print(f"Output directory: {output_dir}")
    print(f"Chunk size: {args.chunk_size} seconds\n")

    # Process files one by one
    successful = 0
    failed = 0
    start_time = time.time()

    for i, file in enumerate(files, 1):
        print(f"\nProcessing file {i} of {len(files)}")
        result = convert_video(str(file), output_dir)
        
        if result['success']:
            successful += 1
            print(f"\nSuccessfully converted: {result['input_file']}")
            print(f"Output size: {result['size']:.2f} MB")
            print(f"Duration: {result.get('duration', 'Unknown')}")
            print(f"Location: {result['output_file']}")
        else:
            failed += 1
            print(f"\nFailed to convert {result['input_file']}")
            print(f"Error: {result['error']}")

    # Print summary
    elapsed_time = time.time() - start_time
    print("\nConversion Summary:")
    print(f"Total files processed: {len(files)}")
    print(f"Successful conversions: {successful}")
    print(f"Failed conversions: {failed}")
    print(f"Total time elapsed: {elapsed_time:.2f} seconds")
    print(f"Average time per file: {elapsed_time/len(files):.2f} seconds")
    print(f"All converted files are stored in: {output_dir}")

if __name__ == "__main__":
    main()