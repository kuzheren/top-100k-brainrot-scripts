ffmpeg -i output_safe_prefinal.mp4 -i watermark.png -filter_complex "overlay=10:main_h-overlay_h-10" -c:a copy -preset medium H:/output_watermark.mp4
