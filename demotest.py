import os
import subprocess

front = os.path.dirname(__file__)
ffmpegaddress = front + "\\ffmpeg.exe"
videoprocessaddress = front + "\\videoprocess"

all_file = os.listdir(videoprocessaddress)
print(ffmpegaddress)
print(videoprocessaddress)

for file in all_file:
    shipid = os.path.splitext(file)[0]
    ext = os.path.splitext(file)[1]
    print(file)
    print(shipid)
    print(ext)
    if ext == ".dav":
        parameter = " -i {}\\{} -r 1 {}\\%3d.jpeg".format(videoprocessaddress, file, videoprocessaddress)
        print(parameter)
        cmd = ffmpegaddress + parameter
        print(cmd)
        subprocess.Popen(cmd)

# .\ffmpeg.exe -i .\videoprocess\123.mp4 -r 1 -framerate 12 .\videoprocess\%3d.jpeg
