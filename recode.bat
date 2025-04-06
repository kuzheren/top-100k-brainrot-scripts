@echo off
set "input_video=%~1"
if "%input_video%"=="" (
    echo Usage: script.bat "path_to_video.mp4"
    exit /b 1
)

ffmpeg -i "%input_video%" ^
-c:v h264 ^
-profile:v main ^
-b:v 68896 ^
-vsync cfr ^
-r 24 ^
-bf 0 ^
-vf "scale=854:480,setsar=1:1" ^
-c:a aac ^
-ar 44100 ^
-b:a 2201 ^
-channels 2 ^
-pix_fmt yuv420p ^
"%~dp1%~n1_processed.mp4"