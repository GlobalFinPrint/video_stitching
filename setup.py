from cx_Freeze import setup, Executable

build_exe_options = {
    "include_files": ["notes", "ffmpeg", "bulk_stitch.bat"],
}

executables = [
    Executable('bulk_stitch.py')
]

setup(
    name="finprint_video_stitching",
    version="0.1",
    description="Scripts for stitching FinPrint GoPro files",
    author="Vulcan, Inc",
    options={
        "build_exe": build_exe_options
    },
    executables=executables,
)
