import subprocess
import json

def get_video_details(file_path):
    pipe = subprocess.Popen(
        'ffprobe -v quiet -print_format json -show_format "{}"'.format(file_path),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    output = pipe.stdout.read().decode('utf-8')
    return json.loads(output)
