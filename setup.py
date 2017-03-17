from cx_Freeze import setup, Executable

build_exe_options = {
    "include_files": ["notes", "ffmpeg", "bulk_stitch.bat"],
}

executables = [
    Executable('bulk_stitch.py')
]

setup(
    name="finprint_video_stitching",
    version="0.9",
    description="Scripts for sticthing FinPrint GoPro files",
    options={
        "build_exe": build_exe_options
    },
    executables=executables,
)
