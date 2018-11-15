import os
import inspect
import click
import tempfile
import shutil
import subprocess
import logging
import time

import stitch_common as sc

FILE_ENDING = 'mp4'
MAX_ATTEMPTS = 3
LOCAL_FFMPEG_PATH = 'ffmpeg/bin'


@click.command()
@click.argument('root_dir')
@click.argument('base_out_dir')
@click.option('--root_tmp_dir', default=None, help='Where tmp folders should be generated')
@click.option('--rename_on_copy', default=True, is_flag=True)
@click.option('--local_ffmpeg', default=True, is_flag=True)
def stitch_videos(root_dir, base_out_dir, root_tmp_dir, rename_on_copy, local_ffmpeg):
    if root_tmp_dir:
        logging.info('Setting directory where temp folders will be created: "{}".'.format(root_tmp_dir))
        os.environ['TMPDIR'] = root_tmp_dir

    if local_ffmpeg:
        ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: 0))),
                                   LOCAL_FFMPEG_PATH)
        if not os.path.isdir(ffmpeg_path):
            logging.fatal('ffmpeg path is incorrect:'.format(ffmpeg_path))
    else:
        ffmpeg_path = 'ffmpeg'

    logging.info('Using ffmpeg:  {}'.format(ffmpeg_path))

    logging.info('Starting the stitching process.')
    if rename_on_copy:
        logging.info('** Rename on copy mode enabled.')
        # We have a number of renaming strategies:
        #   1) if there is only a single directory that contains the files, assume it is a full trip + set code
        #   2) if there are two directories, assume the first is the trip code and the second the set code
        #   3) if there are three directories, follow assumption (2) and add a stereo L or R directory
        for trip_name in get_subdirs(root_dir):
            trip_path = os.path.join(root_dir, trip_name)
            join_mp4s(trip_path, base_out_dir, '{}.mp4'.format(trip_name), ffmpeg_path)
            for set_name in get_subdirs(trip_path):
                set_path = os.path.join(trip_path, set_name)
                join_mp4s(set_path, base_out_dir, '{}_{}.mp4'.format(trip_name, set_name), ffmpeg_path)
                for camera in get_subdirs(set_path):
                    camera_path = os.path.join(set_path, camera)
                    if camera.lower().startswith('l'):
                        camera_abbrv = 'L'
                    elif camera.lower().startswith('r'):
                        camera_abbrv = 'R'
                    else:
                        logging.warning('Unexpected camera folder: {}'.format(camera_path))
                        break
                    join_mp4s(camera_path, base_out_dir, '{}_{}_{}.mp4'.format(trip_name, set_name, camera_abbrv),
                              ffmpeg_path)
    else:
        for root, subdirs, files in os.walk(root_dir):
            directory = remove_prefix(root, root_dir)
            out_dir = base_out_dir + os.path.sep + directory
            out_file_name = 'joined.' + FILE_ENDING
            if os.path.exists(out_file_name):
                logging.warning('***Skipping: "{}" already exists'.format(out_file_name))
            else:
                join_mp4s(root, out_dir, out_file_name, ffmpeg_path)


def join_mp4s(in_dir, out_dir, out_file_name, ffmpeg_path):
    files = get_files(in_dir)
    attempt_count = 0
    while attempt_count < MAX_ATTEMPTS:
        attempt_count += 1
        with tempfile.TemporaryDirectory() as tmpdir:
            logging.info('**** Processing folder: {}'.format(in_dir))
            mp4s = sorted([fi for fi in files if not fi.startswith('._')])
            file_text = ''
            # mp4s should be sorted alpha
            for vid in mp4s:
                logging.info('Copying video {}'.format(vid))
                shutil.copyfile(in_dir + os.path.sep + vid, tmpdir + os.path.sep + vid)
                if vid.lower().endswith('.mts'):
                    logging.info('Processing mts videos')
                    output_name = vid.rsplit('.', 1)
                    output_file = output_name[0] + '.mp4'
                    mts_to_mp4(tmpdir, ffmpeg_path, vid, output_file)
                    file_text += "file '{}/{}'\n".format(tmpdir, output_file)
                else:
                    file_text += "file '{}/{}'\n".format(tmpdir, vid)
            if len(mp4s) > 0:
                mp4_list_file = open('{}/mp4_list.txt'.format(tmpdir), 'w')
                mp4_list_file.write(file_text)
                mp4_list_file.close()

                concat_mp4s(tmpdir, ffmpeg_path)

                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                if FILE_ENDING == 'avi':
                    mp4_to_avi(tmpdir, ffmpeg_path)

                joined_file = tmpdir + os.path.sep + 'joined.' + FILE_ENDING
                if len(sc.get_video_details(joined_file, ffmpeg_path)) == 0:
                    logging.error('Joined file is unreadable! Trying again in a minute.')
                    time.sleep(60)
                else:
                    logging.info('-----------------------------------------')
                    # get fps values
                    output_result = check_fps(tmpdir, ffmpeg_path, joined_file)
                    split_array = output_result.split("/")
                    numerator = int(split_array[0])
                    denominator = int(split_array[1])
                    # do the math
                    math = numerator / denominator

                    if math > 30:
                        downsample(tmpdir, ffmpeg_path, joined_file)
                        ouput_file = tmpdir + os.path.sep + 'output.' + FILE_ENDING
                        logging.info('Copying {} to final location...'.format(ouput_file))
                        shutil.copyfile(
                            ouput_file,
                            os.path.join(out_dir, out_file_name)
                        )
                        logging.info('Finished folder.\n')
                        break  # exit retry loop
                    else:
                        logging.info('Copying {} to final location...'.format(joined_file))
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


def concat_mp4s(tmpdir, ffmpeg_path):
    logging.info('Concatenating mp4s...')
    run_external_command(
        '{} -f concat -safe 0 -i mp4_list.txt -c copy joined.mp4'.format(os.path.join(ffmpeg_path, 'ffmpeg')),
        tmpdir)
    logging.info('-----------------------------------------')


def mp4_to_avi(tmpdir, ffmpeg_path):
    logging.info('Converting from mp4 to avi...')
    run_external_command(
        '{} -i joined.mp4 -vcodec copy -r 29.97 -an joined.avi'.format(os.path.join(ffmpeg_path, 'ffmpeg')),
        tmpdir)


def mts_to_mp4(tmpdir, ffmpeg_path, input_file, output_file):
    logging.info('Converting from mts to mp4...')
    run_external_command(
        '{} -i {} -vcodec mpeg4 -b:v 15M -acodec libmp3lame -b:a 192k {}'.format(os.path.join(ffmpeg_path, 'ffmpeg'),
                                                                                 input_file, output_file),
        tmpdir)
    logging.info('-----------------------------------------')


def avi_to_mp4(tmpdir, ffmpeg_path, input_file, output_file):
    logging.info('Converting from avi to mp4...')
    run_external_command(
        '{} -i {} -c:v libx264 -c:a copy {}'.format(os.path.join(ffmpeg_path, 'ffmpeg'), input_file, output_file),
        tmpdir)
    logging.info('-----------------------------------------')


def downsample(tmpdir, ffmpeg_path, input_file):
    logging.info('Downsampling...')
    run_external_command(
        '{} -i {} -r 29.97 -y output.mp4'.format(os.path.join(ffmpeg_path, 'ffmpeg'), input_file),
        tmpdir)
    logging.info('-----------------------------------------')


def check_fps(tmpdir, ffmpeg_path, inputfile):
    logging.info('Checking fps...')
    # the shell command
    command = '{} -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate {}'.format(
        os.path.join(ffmpeg_path, 'ffprobe'), inputfile)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True, cwd=tmpdir)
    # Launch the shell command:
    output, error = process.communicate()
    return output.decode("utf-8")


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
