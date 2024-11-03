import argparse
import os
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Optimized TS to MP4 Converter with Compression Options')
    parser.add_argument('input', help='Input .ts file or directory')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='Recursively process directories')
    parser.add_argument('-c', '--chunk-size', type=int,
                       help='Chunk size in seconds (auto-optimized if not specified)')
    parser.add_argument('--cpu-limit', type=float, default=0.1,
                       help='CPU usage limit (0.1 = 10%)')
    parser.add_argument('--delete-original', action='store_true',
                       help='Delete original files after successful conversion')
    parser.add_argument('--keep-failed', action='store_true',
                       help='Keep original files even if conversion fails')

    # Compression group
    compress_group = parser.add_mutually_exclusive_group()
    compress_group.add_argument('--no-compress', action='store_true', default=True,
                              help='Disable compression (default)')
    compress_group.add_argument('--compress', choices=['light', 'medium', 'high'],
                              help='Compression level (light=720p, medium=480p, high=360p)')
    compress_group.add_argument('--target-size', type=float,
                              help='Target size in MB (will try to compress to this size)')
    
    parser.add_argument('--quality', type=int, choices=range(16, 29), default=23,
                       help='Video quality (16-28, lower is better quality, default: 23)')
    
    return parser.parse_args()

def get_file_list(input_path, recursive=False):
    """Get list of .ts files to process"""
    if os.path.isdir(input_path):
        pattern = '**/*.ts' if recursive else '*.ts'
        return list(Path(input_path).glob(pattern))
    return [Path(input_path)]

def print_settings(args, processor_cores):
    """Print current conversion settings"""
    print(f"\nConverter Settings:")
    print(f"CPU usage limit: {args.cpu_limit*100}% ({processor_cores} cores)")
    print(f"Compression: {'Disabled (maintaining original quality)' if args.no_compress else args.compress or f'Target size {args.target_size}MB'}")
    if not args.no_compress:
        print(f"Quality level: {args.quality} (16=best, 28=worst)")
    print(f"Delete original: {args.delete_original}")
    if args.delete_original:
        print(f"Keep failed files: {args.keep_failed}")