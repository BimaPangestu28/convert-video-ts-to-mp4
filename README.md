# TS to MP4 Video Converter

A Python script for converting video TS (Transport Stream) files to MP4 format using FFmpeg. This tool supports both single file conversion and batch processing of multiple files in directories.

## Features

- Convert single TS files to MP4 format
- Batch convert multiple TS files in a directory
- Recursive directory processing option
- Configurable output file naming
- High-quality video and audio conversion using H.264 and AAC codecs
- Detailed error reporting and progress feedback

## Prerequisites

Before using this script, make sure you have the following installed:

1. Python 3.x
2. FFmpeg

### Installing FFmpeg

#### Windows
1. Download FFmpeg from [FFmpeg Official Website](https://ffmpeg.org/download.html)
2. Extract the downloaded archive
3. Add FFmpeg's bin folder to your system's PATH environment variable

#### macOS (using Homebrew)
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

## Installation

1. Clone this repository or download the script:
```bash
git clone https://github.com/BimaPangestu28/ts-to-mp4-converter.git
cd ts-to-mp4-converter
```

2. No additional Python packages are required as the script uses only standard library modules.

## Usage

### Basic Usage

Convert a single TS file:
```bash
python converter.py input.ts
```
This will create `input.mp4` in the same directory.

### Advanced Usage

1. Convert a file with a specific output name:
```bash
python converter.py input.ts -o output.mp4
```

2. Convert all TS files in a directory:
```bash
python converter.py /path/to/directory
```

3. Convert all TS files in a directory and its subdirectories:
```bash
python converter.py /path/to/directory -r
```

### Command Line Arguments

- `input`: Input .ts file or directory containing .ts files
- `-o, --output`: Output file name (for single file conversion)
- `-r, --recursive`: Recursively process directories

## Video Conversion Settings

The script uses the following FFmpeg settings for optimal quality:

- Video Codec: H.264 (libx264)
- Audio Codec: AAC
- Encoding Preset: medium (balanced between speed and quality)
- CRF (Constant Rate Factor): 23 (range: 18-28, lower means better quality)

## Troubleshooting

1. "FFmpeg not found" error:
   - Ensure FFmpeg is installed correctly
   - Verify FFmpeg is in your system's PATH
   - Try running `ffmpeg -version` in terminal/command prompt

2. "Input file not found" error:
   - Check if the file path is correct
   - Ensure you have read permissions for the input file

3. Conversion fails:
   - Check if you have write permissions in the output directory
   - Ensure you have enough disk space
   - Check if the input file is a valid TS file

## Contributing

Feel free to fork this repository and submit pull requests with improvements. You can also open issues for bug reports or feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This script uses FFmpeg for video conversion
- Thanks to all contributors and users who help improve this tool

## Author

Bima Pangestu