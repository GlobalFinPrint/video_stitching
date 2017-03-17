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
@click.option('--root_tmp_dir', default=None, help='Where tmp folders should be generated')
@click.option('--rename_on_copy', default=True, is_flag=True)
def stitch_videos(root_dir, base_out_dir, root_tmp_dir, rename_on_copy):
    if root_tmp_dir:
        logging.info('Setting directory where temp folders will be created: "{}".'.format(root_tmp_dir))
        os.environ['TMPDIR'] = root_tmp_dir

    logging.info('Starting the stitching process.')
    if rename_on_copy:
        logging.info('** Rename on copy mode enabled.')
        # We have a number of renaming strategies:
        #   1) if there is only a single directory that contains the files, assume it is a full trip + set code
        #   2) if there are two directories, assume the first is the trip code and the second the set code
        #   3) if there are three directories, follow assumption (2) and add a stereo L or R directory
        for trip_name in get_subdirs(root_dir):
            trip_path = os.path.join(root_dir, trip_name)
            join_mp4s(trip_path, base_out_dir, '{}.mp4'.format(trip_name))
            for set_name in get_subdirs(trip_path):
                set_path = os.path.join(trip_path, set_name)
                join_mp4s(set_path, base_out_dir, '{}_{}.mp4'.format(trip_name, set_name))
                for camera in get_subdirs(set_path):
                    camera_path = os.path.join(set_path, camera)
                    if camera.lower().startswith('l'):
                        camera_abbrv = 'L'
                    elif camera.lower().startswith('r'):
                        camera_abbrv = 'R'
                    else:
                        logging.warning('Unexpected camera folder: {}'.format(camera_path))
                        break
                    join_mp4s(camera_path, base_out_dir, '{}_{}_{}.mp4'.format(trip_name, set_name, camera_abbrv))
    else:
        for root, subdirs, files in os.walk(root_dir):
            directory = remove_prefix(root, root_dir)
            out_dir = base_out_dir + os.path.sep + directory
            out_file_name = 'joined.' + FILE_ENDING
            if os.path.exists(out_file_name):
                logging.warning('***Skipping: "{}" already exists'.format(out_file_name))
            else:
                join_mp4s(root, out_dir, out_file_name)


def join_mp4s(in_dir, out_dir, out_file_name):
    files = get_files(in_dir)
    attempt_count = 0
    while attempt_count < MAX_ATTEMPTS:
        attempt_count += 1
        with tempfile.TemporaryDirectory() as tmpdir:
            logging.info('**** Processing folder: {}'.format(in_dir))
            mp4s = sorted([fi for fi in files if fi.lower().endswith('.mp4') and not fi.startswith('._')])
            file_text = ''
            # mp4s should be sorted alpha
            for vid in mp4s:
                logging.info('Copying video {}'.format(vid))
                shutil.copyfile(in_dir + os.path.sep + vid, tmpdir + os.path.sep + vid)
                file_text += "file '{}/{}'\n".format(tmpdir, vid)
            if len(mp4s) > 0:
                mp4_list_file = open('{}/mp4_list.txt'.format(tmpdir), 'w')
                mp4_list_file.write(file_text)
                mp4_list_file.close()

                concat_mp4s(tmpdir)

                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                if FILE_ENDING == 'avi':
                    mp4_to_avi(tmpdir)

                joined_file = tmpdir + os.path.sep + 'joined.' + FILE_ENDING
                if len(sc.get_video_details(joined_file)) == 0:
                    logging.error('Joined file is unreadable! Trying again in a minute.')
                    time.sleep(60)
                else:
                    logging.info('Copying {} to final location...'.format(FILE_ENDING))
                    shutil.copyfile(
                        joined_file,
                        os.path.join(out_dir, out_file_name)
                    )
                    logging.info('Finished folder.\n')
                    break  # exit retry loop
            else:
                logging.info('No mp4s found in folder.')
                attempt_count = MAX_ATTEMPTS
    if attempt_count >= MAX_ATTEMPTS:
        logging.error('Giving up after multiple retries trying to stitch {}'.format(in_dir))


def get_subdirs(folder):
    return [xx for xx in os.listdir(folder) if os.path.isdir(os.path.join(folder, xx))]


def get_files(folder):
    return [xx for xx in os.listdir(folder) if os.path.isfile(os.path.join(folder, xx))]


def concat_mp4s(tmpdir):
    logging.info('Concatenating mp4s...')
    run_external_command(
        'ffmpeg -f concat -safe 0 -i mp4_list.txt -c copy joined.mp4',
        tmpdir)


def mp4_to_avi(tmpdir):
    logging.info('Converting from mp4 to avi...')
    run_external_command(
        'ffmpeg -i joined.mp4 -vcodec copy -r 29.97 -an joined.avi',
        tmpdir)


def run_external_command(command, tmpdir):
    subprocess.call(
        command,
        shell=True,
        cwd=tmpdir
    )


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
    stitch_videos()
