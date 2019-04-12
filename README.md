**Global Finprint video stitching helper files.**

Copyright 2015-2017 Vulcan, Inc.

To build:
1. Create a python 3.5+ virtual environment
2. Run `python -m pip install --upgrade pip` command 
3. Activate the environment and `pip install -r requirements.txt` from the project root
4. If FFmpeg is being used, assure that its libraries and executable are in the /lib/ directory 
(these can be found here:  http://ffmpeg.zeranoe.com/builds/) 
5. `python setup.py build_exe`

To deploy:
1. Copy contents of build directory to deployment location (e.g., `C:\Vulcan\video_stitching\`)
2. Create a desktop shortcut with the following target:
  C:\Windows\System32\cmd.exe /k "C:\Vulcan\video_stitching\exe.win-amd64-3.5\bulk_stitch.bat"
3. Note:  execution requires Visual C++ redistributables.  These can be found here:  
https://www.microsoft.com/en-us/download/details.aspx?id=52685
