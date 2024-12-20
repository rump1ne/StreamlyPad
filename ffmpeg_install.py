import os
import subprocess
import platform
import requests
from zipfile import ZipFile

# Проверка и установка ffmpeg
def install_ffmpeg():
    system = platform.system().lower()
    ffmpeg_url = ""
    if "windows" in system:
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    elif "darwin" in system:  # macOS
        ffmpeg_url = "https://evermeet.cx/ffmpeg/ffmpeg.zip"
    elif "linux" in system:
        print("Установите ffmpeg через менеджер пакетов (например, apt, yum).")
        return

    # Путь для загрузки
    download_path = os.path.join(os.getcwd(), "ffmpeg.zip")

    # Скачиваем ffmpeg
    print("Скачивание ffmpeg...")
    response = requests.get(ffmpeg_url, stream=True)
    with open(download_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)

    # Распаковываем архив
    print("Распаковка ffmpeg...")
    with ZipFile(download_path, "r") as zip_ref:
        extract_path = os.path.join(os.getcwd(), "ffmpeg")
        zip_ref.extractall(extract_path)

    # Установка пути ffmpeg
    for root, dirs, files in os.walk(extract_path):
        if "ffmpeg.exe" in files:
            ffmpeg_path = os.path.join(root, "ffmpeg.exe")
            os.environ["PATH"] += os.pathsep + root
            print(f"ffmpeg установлен в {ffmpeg_path}")
            return

    print("Ошибка установки ffmpeg.")

# Устанавливаем ffmpeg, если он отсутствует
if which("ffmpeg") is None:
    install_ffmpeg()
else:
    print("ffmpeg уже установлен.")
