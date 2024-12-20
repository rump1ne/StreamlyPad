import keyboard
import sounddevice as sd
import soundfile as sf
import threading
from pydub import AudioSegment
from pydub.playback import play
import tkinter as tk
from tkinter import filedialog, ttk
import sqlite3
import os
from pydub.utils import which
import numpy as np

# Устанавливаем путь к ffmpeg вручную
ffmpeg_path = which("ffmpeg")
if ffmpeg_path is None:
    print("Ошибка: ffmpeg не найден. Убедитесь, что он установлен и добавлен в PATH.")
    exit(1)
AudioSegment.converter = ffmpeg_path

# Глобальные настройки
global_volume = 1.0  # Громкость (от 0.0 до 1.0)
repeat_count = 1  # Количество повторений
activation_phrases = {}  # Словарь фраз для активации

current_output_device = None
hotkeys = {}
db_file = "hotkeys.db"  # Имя файла базы данных

# Получить список устройств вывода
def get_output_devices():
    devices = sd.query_devices()
    output_devices = [(idx, dev['name']) for idx, dev in enumerate(devices) if dev['max_output_channels'] > 0]
    return output_devices

# Установить устройство вывода звука
def set_output_device(device_id):
    global current_output_device
    current_output_device = device_id
    print(f"Устройство вывода установлено: {sd.query_devices(device_id)['name']}")

# Создание и настройка базы данных
def init_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS hotkeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotkey TEXT UNIQUE,
            file_path TEXT
        )
    """)
    conn.commit()
    conn.close()

# Функция для воспроизведения звука через выбранное устройство вывода
def play_sound(file_path):
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        return
    try:
        # Чтение аудиофайла
        audio, samplerate = sf.read(file_path)
        audio = (audio * global_volume).astype(np.float32)  # Применение глобальной громкости

        # Получение информации об устройстве вывода
        device_info = sd.query_devices(current_output_device, 'output')
        num_channels = device_info['max_output_channels']

        # Приведение числа каналов к поддерживаемому устройством
        if audio.ndim == 1:  # Монофайл
            audio = np.tile(audio[:, None], (1, num_channels))  # Преобразуем в нужное количество каналов
        elif audio.shape[1] != num_channels:  # Многоканальный файл
            audio = audio[:, :num_channels]  # Урезаем лишние каналы

        # Воспроизведение аудио через устройство вывода
        sd.play(audio, samplerate=samplerate, device=current_output_device)
        sd.wait()  # Ждем завершения воспроизведения
    except Exception as e:
        print(f"Ошибка воспроизведения через устройство вывода: {e}")

# Добавить звук и горячую клавишу
def add_sound(hotkey, file_path):
    global hotkeys
    hotkeys[hotkey] = file_path
    handle_hotkey(hotkey, file_path)
    save_hotkey(hotkey, file_path)

# Загрузка горячих клавиш из базы данных
def load_hotkeys():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT hotkey, file_path FROM hotkeys")
    rows = cursor.fetchall()
    conn.close()
    for hotkey, file_path in rows:
        hotkeys[hotkey] = file_path
    return rows

# Сохранение горячей клавиши в базу данных
def save_hotkey(hotkey, file_path):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO hotkeys (hotkey, file_path) VALUES (?, ?)", (hotkey, file_path))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Горячая клавиша {hotkey} уже существует в базе данных.")
    conn.close()

# Удаление горячей клавиши из базы данных
def delete_hotkey(hotkey):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hotkeys WHERE hotkey = ?", (hotkey,))
    conn.commit()
    conn.close()

# Настройка горячей клавиши
def handle_hotkey(hotkey, file_path):
    keyboard.add_hotkey(hotkey, lambda: threading.Thread(target=play_sound, args=(file_path,)).start())

# Функция для настройки глобальной громкости
def set_volume(value):
    global global_volume
    global_volume = float(value)

# Функция для настройки количества повторений
def set_repeat(value):
    global repeat_count
    repeat_count = value

# Настройки приложения (всплывающее окно)
def open_settings():
    settings_window = tk.Toplevel()
    settings_window.title("Настройки")

    ttk.Label(settings_window, text="Выберите устройство вывода:").grid(row=0, column=0)

    output_devices = get_output_devices()
    device_var = tk.StringVar(value=output_devices[0][1])

    def update_device():
        selected_device_name = device_var.get()
        for device_id, device_name in output_devices:
            if device_name == selected_device_name:
                set_output_device(device_id)

    device_menu = ttk.Combobox(
        settings_window,
        textvariable=device_var,
        values=[name for _, name in output_devices],
        state="readonly"
    )
    device_menu.grid(row=0, column=1)
    device_menu.bind("<<ComboboxSelected>>", lambda _: update_device())

    ttk.Label(settings_window, text="Громкость:").grid(row=1, column=0)
    volume_slider = ttk.Scale(settings_window, from_=0.0, to=1.0, value=global_volume, orient="horizontal", command=set_volume)
    volume_slider.grid(row=1, column=1)

    ttk.Label(settings_window, text="Повторения:").grid(row=2, column=0)
    repeat_slider = ttk.Scale(settings_window, from_=1, to=10, value=repeat_count, orient="horizontal", command=lambda v: set_repeat(int(float(v))))
    repeat_slider.grid(row=2, column=1)

# Графический интерфейс
class SoundpadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Streamlypad")

        ttk.Label(root, text="Горячая клавиша:").grid(row=0, column=0)
        self.hotkey_entry = ttk.Entry(root)
        self.hotkey_entry.grid(row=0, column=1)

        self.file_path = None
        ttk.Button(root, text="Выбрать файл", command=self.select_file).grid(row=1, column=0, columnspan=2)
        ttk.Button(root, text="Добавить", command=self.add_hotkey).grid(row=2, column=0, columnspan=2)
        ttk.Button(root, text="Удалить", command=self.remove_hotkey).grid(row=3, column=0, columnspan=2)
        ttk.Button(root, text="Настройки", command=open_settings).grid(row=4, column=0, columnspan=2)

        ttk.Label(root, text="Добавленные горячие клавиши:").grid(row=5, column=0, columnspan=2)
        self.hotkey_list = tk.Text(root, height=10, width=40, state="disabled")
        self.hotkey_list.grid(row=6, column=0, columnspan=2)

        self.load_hotkeys()

    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac")])

    def add_hotkey(self):
        hotkey = self.hotkey_entry.get()
        if not hotkey or not self.file_path:
            print("Введите горячую клавишу и выберите файл!")
            return
        if hotkey in hotkeys:
            print(f"Горячая клавиша {hotkey} уже существует!")
            return
        add_sound(hotkey, self.file_path)
        self.update_hotkey_list()

    def remove_hotkey(self):
        hotkey = self.hotkey_entry.get()
        if not hotkey:
            print("Введите горячую клавишу для удаления!")
            return
        if hotkey not in hotkeys:
            print(f"Горячая клавиша {hotkey} не найдена!")
            return
        delete_hotkey(hotkey)
        del hotkeys[hotkey]
        self.update_hotkey_list()

    def update_hotkey_list(self):
        self.hotkey_list.config(state="normal")
        self.hotkey_list.delete("1.0", tk.END)
        for hotkey, file_path in hotkeys.items():
            self.hotkey_list.insert("end", f"{hotkey}: {file_path}\n")
        self.hotkey_list.config(state="disabled")

    def load_hotkeys(self):
        hotkey_data = load_hotkeys()
        for hotkey, file_path in hotkey_data:
            hotkeys[hotkey] = file_path
        self.update_hotkey_list()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = SoundpadApp(root)
    print("Программа запущена. Нажмите горячие клавиши для воспроизведения звуков.")
    root.mainloop()
