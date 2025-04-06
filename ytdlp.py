import subprocess

def invoke(cmd, log=True):
    command = [r"C:\Users\Admin\Programs\yt-dlp\yt-dlp.exe"] + cmd

    try:
        result = []
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            if log:
                print(line, end="")
            result.append(line)

        process.wait()

        return process.returncode, "".join(result)
    except Exception as e:
        print(f"Ошибка выполнения команды yt-dlp: {e}")
        return -1, None