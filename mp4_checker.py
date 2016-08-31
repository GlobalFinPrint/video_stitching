import os
import click
import tempfile
import shutil
import logging
import stitch_common as sc

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

            mp4_details = sc.get_video_details(file_path)
            if len(mp4_details) == 0:
                logging.error('**** bad mp4 detected: {} ****'.format(file_path))
            else:
                logging.info('MP4 details: {}'.format(str(mp4_details)))
        logging.info('Finished folder.\n')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
    get_video_lengths()
