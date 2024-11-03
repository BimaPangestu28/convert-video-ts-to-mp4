# Compression presets
COMPRESSION_SETTINGS = {
    'light': {
        'scale': '-vf scale=-1:720',
        'bitrate': '-b:v 1500k -maxrate 2000k -bufsize 2000k',
        'audio': '-ac 2 -ar 44100 -b:a 128k'
    },
    'medium': {
        'scale': '-vf scale=-1:480',
        'bitrate': '-b:v 1000k -maxrate 1500k -bufsize 1500k',
        'audio': '-ac 2 -ar 44100 -b:a 96k'
    },
    'high': {
        'scale': '-vf scale=-1:360',
        'bitrate': '-b:v 500k -maxrate 700k -bufsize 700k',
        'audio': '-ac 2 -ar 44100 -b:a 64k'
    }
}

# FFmpeg default parameters
DEFAULT_FFMPEG_PARAMS = {
    'video_codec': 'libx264',
    'audio_codec': 'aac',
    'video_params': [
        '-preset', 'faster',
        '-tune', 'fastdecode',
        '-movflags', '+faststart'
    ],
    'audio_params': [
        '-ac', '2',
        '-ar', '44100'
    ]
}

# Chunk processing settings
MIN_CHUNK_SIZE = 30  # seconds
MAX_CHUNK_SIZE = 300  # seconds
DEFAULT_KEYFRAME_INTERVAL = 10  # seconds