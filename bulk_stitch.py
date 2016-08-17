import os
import click
import tempfile
import shutil
import subprocess
import logging

@click.command()
@click.argument('root_dir')
@click.argument('base_out_dir')
def stitch_videos(root_dir, base_out_dir):
    logging.info('Starting the stitching process.')
    for root, subdirs, files in os.walk(root_dir):
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
                subprocess.run(
                    'ffmpeg -f concat -i mp4_list.txt -c copy output.MP4',
                    shell=True,
                    cwd=tmpdir
                )

                directory = remove_prefix(root, root_dir)
                out_dir = base_out_dir + os.path.sep + directory
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                logging.info('Converting from mp4 to avi...')
                subprocess.run(
                    'ffmpeg -i output.MP4 -vcodec copy -r 29.97 -an joined.avi'.format(out_dir),
                    shell=True,
                    cwd=tmpdir
                )
                logging.info('Copying avi to final location...')
                shutil.copyfile(
                    tmpdir + os.path.sep + 'joined.avi',
                    out_dir + os.path.sep + 'joined.avi'
                )
                logging.info('Finished folder.\n')

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
    stitch_videos()