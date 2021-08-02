from ctypes import *
import platform
import re
import os

def system_get_platform_info():
    sys_platform = platform.system().lower().strip()
    python_bit = platform.architecture()[0]
    python_bit_num = re.findall('(\d+)\w*', python_bit)[0]
    return sys_platform, python_bit_num

sys_platform, python_bit_num = system_get_platform_info()
system_type = sys_platform + python_bit_num

print(system_type)



# import os
# import subprocess

# front = os.path.dirname(__file__)
# ffmpegaddress = front + "\\ffmpeg.exe"
# videoprocessaddress = front + "\\videoprocess"

# all_file = os.listdir(videoprocessaddress)
# print(ffmpegaddress)
# print(videoprocessaddress)

# for file in all_file:
#     shipid = os.path.splitext(file)[0]
#     ext = os.path.splitext(file)[1]
#     print(file)
#     print(shipid)
#     print(ext)
#     if ext == ".dav":
#         parameter = " -i {}\\{} -r 1 {}\\%3d.jpeg".format(videoprocessaddress, file, videoprocessaddress)
#         print(parameter)
#         cmd = ffmpegaddress + parameter
#         print(cmd)
#         subprocess.Popen(cmd)

# # .\ffmpeg.exe -i .\videoprocess\123.mp4 -r 1 -framerate 12 .\videoprocess\%3d.jpeg
