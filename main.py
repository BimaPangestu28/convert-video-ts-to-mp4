import os
import time
from src.settings import parse_arguments, get_file_list, print_settings
from src.processor import VideoProcessor
from src.utils import print_conversion_result, print_summary

def main():
    # Parse arguments
    args = parse_arguments()

    # Initialize processor
    processor = VideoProcessor(
        cpu_limit=args.cpu_limit,
        compression_level=args.compress,
        target_size=args.target_size,
        quality=args.quality
    )

    # Print settings
    print_settings(args, processor.cores_to_use)

    # Setup output directory
    output_dir = args.output or os.path.join(os.path.dirname(os.path.abspath(args.input)), 'results')
    os.makedirs(output_dir, exist_ok=True)

    # Get file list
    files = get_file_list(args.input, args.recursive)
    if not files:
        print("No .ts files found!")
        return

    print(f"\nFound {len(files)} files to convert")
    print(f"Output directory: {output_dir}\n")

    # Initialize statistics
    stats = {
        'successful': 0,
        'failed': 0,
        'total_size_reduction': 0,
        'deleted_files': 0,
        'saved_space': 0,
        'start_time': time.time()
    }

    # Process files
    for i, file in enumerate(files, 1):
        print(f"\nProcessing file {i} of {len(files)}")
        original_size = os.path.getsize(file) / (1024 * 1024)
        result = processor.convert_video(str(file), output_dir, args.chunk_size)
        
        if result['success']:
            stats['successful'] += 1
            stats['total_size_reduction'] += result['compression_ratio']
            
            if args.delete_original:
                try:
                    os.remove(file)
                    stats['deleted_files'] += 1
                    stats['saved_space'] += original_size - result['size']
                except Exception as e:
                    print(f"Warning: Could not delete original file: {str(e)}")
        else:
            stats['failed'] += 1
            if args.delete_original and not args.keep_failed:
                try:
                    os.remove(file)
                    stats['deleted_files'] += 1
                except Exception as e:
                    print(f"Warning: Could not delete original file: {str(e)}")
        
        print_conversion_result(result, original_size)

    # Calculate final statistics
    elapsed_time = time.time() - stats['start_time']
    total_files = len(files)
    
    summary_stats = {
        'total': total_files,
        'successful': stats['successful'],
        'failed': stats['failed'],
        'avg_compression': stats['total_size_reduction'] / stats['successful'] if stats['successful'] > 0 else 0,
        'elapsed_time': elapsed_time,
        'avg_time': elapsed_time / total_files,
        'deleted_files': stats['deleted_files'],
        'saved_space': stats['saved_space']
    }

    # Print summary
    print_summary(summary_stats)
    print(f"\nAll converted files are stored in: {output_dir}")

if __name__ == "__main__":
    main()