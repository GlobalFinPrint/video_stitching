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
    wb = openpyxl.load_workbook(in_file)
    set_sheet = wb['Set']
    get_cell_by_name = get_cell_by_name_extractor(get_header_map(sheet.rows[0]))
    for row in sheet.rows[1:]:
        trip_code = get_cell(row, 'trip_code').value
        set_code = get_cell(row, 'set_code').value
        video = get_cell(row, 'video').value
        if trip_code and set_code:
            logging.info('Finding video for trip: {}, set: {}'.format(trip_code, set_code))
            if video:
                video_path = '{}/{}/joined.avi'.format(video_dir, video)
                new_video_path = '{}/{}_{}.avi'.format(output_folder, trip_code, set_code)
                if os.path.isfile(video_path):
                    if os.path.isfile(new_video_path):
                        logging.warning('Overwriting video "{}"'.format(new_video_path))
                    shutil.copyfile(video_path, new_video_path)
                else:
                    logging.error('Video "{}" does not exist'.format(video_path))
            else:
                logging.error('No video specified for this set.')

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
