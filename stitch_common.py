import os
import subprocess
import json

def get_video_details(file_path, ffmpeg_path):
    pipe = subprocess.Popen(
        '{} -v quiet -print_format json -show_format "{}"'.format(os.path.join(ffmpeg_path, 'ffprobe'), file_path),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    output = pipe.stdout.read().decode('utf-8')
    return json.loads(output)
