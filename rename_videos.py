"""
rename_videos
Author: Tyler Sellon

Renames a set of stitched videos from bulk_stitch to their canonical names,
based off of an Excel mapping file. This is the same file used in import_excel.

File format is specified here:
https://www.dropbox.com/s/5yy0bb4mxbm0mdj/data_collection_standards.xlsx?dl=0

Only the Sets worksheet is used, and only the trip, set, and video columns.
"""
import logging
import openpyxl
import click
import os.path
import shutil

@click.command()
@click.argument('video_dir')
@click.argument('excel_file')
@click.argument('output_folder')
def rename_videos(video_dir, excel_file, output_folder):
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb['Set']
    get_cell = get_cell_by_name_extractor(get_header_map(sheet.rows[0]))
    for row in sheet.rows[1:]:
        trip_code = get_cell(row, 'trip_code').value
        set_code = get_cell(row, 'set_code').value
        video = get_cell(row, 'video').value
        try:
            camera = get_cell(row, 'camera').value
        except KeyError:
            camera = None
        if trip_code and set_code:
            logging.info('Finding video for trip: {}, set: {}'.format(trip_code, set_code))
            if video:
                video_path = '{}/{}'.format(video_dir, video)
                video_candidates = [xx for xx in os.walk(video_path) if 'joined.mp4' in xx[2]]
                if len(video_candidates) == 2:
                    camera_types = ['L', 'R']
                    processed = {}
                    for ct in camera_types:
                        processed[ct] = False
                    for camera in camera_types:
                        for candidate in video_candidates:
                            if os.path.basename(candidate[0]).upper().startswith(camera):
                                if processed[camera]:
                                    logging.error('Second {} camera video found: {}'.format(camera, candidate[0]))
                                else:
                                    orig_video_path = '{}/joined.mp4'.format(candidate[0])
                                    rename_video(trip_code, set_code, camera, output_folder, orig_video_path)
                                    processed[camera] = True
                elif len(video_candidates) > 1:
                    logging.error('More than two videos found for this set.')
                elif len(video_candidates) == 0:
                    logging.warning('No video found for this set.')
                else:
                    joined_video_info = video_candidates[0]
                    orig_video_path = '{}/joined.mp4'.format(joined_video_info[0])
                    rename_video(trip_code, set_code, camera, output_folder, orig_video_path)
            else:
                logging.error('No video specified for this set.')

def rename_video(trip_code, set_code, camera, output_folder, orig_video_path):
    name_pieces = [trip_code, set_code]
    if camera:
        name_pieces.append(camera)
    new_video_path = '{}/{}.mp4'.format(output_folder, '_'.join(name_pieces))
    if os.path.isfile(orig_video_path):
        logging.info('Moving "{}" to "{}"'.format(orig_video_path, new_video_path))
        if os.path.isfile(new_video_path):
            logging.warning('Overwriting video "{}"'.format(new_video_path))
        shutil.move(orig_video_path, new_video_path)
        logging.info('Finished copying video for trip: {}, set: {}'.format(trip_code, set_code))
    else:
        logging.error('Video "{}" does not exist'.format(orig_video_path))

def get_cell_by_name_extractor(headers):
    extractor_func = lambda row, column_name: row[headers[column_name]]
    return extractor_func

def get_header_map(header_row):
    result = {}
    for idx, header in enumerate(header_row):
        if header.value:
            result[header.value] = idx
    return result

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
    rename_videos()
