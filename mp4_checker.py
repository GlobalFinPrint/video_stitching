import os
import click
import tempfile
import shutil
import subprocess
import logging
import json

@click.command()
@click.argument('root_dir')
def get_video_lengths(root_dir):
    for root, subdirs, files in os.walk(root_dir):
        logging.info('**** Processing folder: {}'.format(root))
        mp4s = [fi for fi in files if fi.lower().endswith('.mp4') and not fi.startswith('._')]
        file_text = ''
        for vid in mp4s:
            file_path = "{}/{}".format(root, vid)
            logging.info('Grabbing details from {}'.format(file_path))

            pipe = subprocess.Popen(
                'ffprobe -v quiet -print_format json -show_format "{}"'.format(file_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            output = pipe.stdout.read().decode('utf-8')
            mp4_details = json.loads(output)

            if len(mp4_details) == 0:
                logging.error('**** bad mp4 detected: {} ****'.format(file_path))
            else:
                logging.info('MP4 details: {}'.format(output))
        logging.info('Finished folder.\n')

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
    get_video_lengths()
