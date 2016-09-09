import os
import click
import tempfile
import shutil
import subprocess
import logging
import time

import stitch_common as sc

FILE_ENDING = 'mp4'
MAX_ATTEMPTS = 3

@click.command()
@click.argument('root_dir')
@click.argument('base_out_dir')
def stitch_videos(root_dir, base_out_dir):
    logging.info('Starting the stitching process.')
    for root, subdirs, files in os.walk(root_dir):
        directory = remove_prefix(root, root_dir)
        out_dir = base_out_dir + os.path.sep + directory
        out_file_name = out_dir + os.path.sep + 'joined.' + FILE_ENDING
        if os.path.exists(out_file_name):
            logging.warning('***Skipping: "{}" already exists'.format(out_file_name))
        else:
            attempt_count = 0
            while attempt_count < MAX_ATTEMPTS:
                attempt_count += 1
                with tempfile.TemporaryDirectory() as tmpdir:
                    logging.info('**** Processing folder: {}'.format(root))
                    mp4s = [fi for fi in files if fi.lower().endswith('.mp4') and not fi.startswith('._')]
                    file_text = ''
                    for vid in mp4s:
                        logging.info('Copying video {}'.format(vid))
                        shutil.copyfile(root + os.path.sep + vid, tmpdir + os.path.sep + vid)
                        file_text += "file '{}/{}'\n".format(tmpdir, vid)
                    if len(mp4s) > 0:
                        mp4_list_file = open('{}/mp4_list.txt'.format(tmpdir), 'w')
                        mp4_list_file.write(file_text)
                        mp4_list_file.close()

                        logging.info('Concatenating mp4s...')
                        subprocess.call(
                            'ffmpeg -f concat -safe 0 -i mp4_list.txt -c copy joined.mp4',
                            shell=True,
                            cwd=tmpdir
                        )

                        if not os.path.exists(out_dir):
                            os.makedirs(out_dir)
                        if FILE_ENDING == 'avi':
                            logging.info('Converting from mp4 to avi...')
                            subprocess.call(
                                'ffmpeg -i joined.mp4 -vcodec copy -r 29.97 -an joined.avi'.format(out_dir),
                                shell=True,
                                cwd=tmpdir
                            )

                        joined_file = tmpdir + os.path.sep + 'joined.' + FILE_ENDING
                        if len(sc.get_video_details(joined_file)) == 0:
                            logging.error('Joined file is unreadable! Trying again in a minute.')
                            time.sleep(60)
                        else:
                            logging.info('Copying {} to final location...'.format(FILE_ENDING))
                            shutil.copyfile(
                                joined_file,
                                out_file_name
                            )
                            logging.info('Finished folder.\n')
                            attempt_count = MAX_ATTEMPTS
                    else:
                        logging.info('No mp4s found in folder.')
                        attempt_count = MAX_ATTEMPTS
            if attempt_count >= MAX_ATTEMPTS:
                logging.error('Giving up after multiple retries trying to stitch {}'.format(root))

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
    stitch_videos()
