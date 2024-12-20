import pytest
import sqlite3
from main import init_db, save_hotkey, load_hotkeys, delete_hotkey, db_file

@pytest.fixture
def setup_db():
    # Настраиваем временную базу данных
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hotkeys")
    conn.commit()
    yield
    conn.close()

def test_init_db(setup_db):
    init_db()
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hotkeys'")
    assert cursor.fetchone() is not None
    conn.close()

def test_save_and_load_hotkey(setup_db):
    init_db()
    save_hotkey("ctrl+1", "/path/to/sound1.mp3")
    hotkeys = load_hotkeys()
    assert len(hotkeys) == 1
    assert hotkeys[0] == ("ctrl+1", "/path/to/sound1.mp3")

def test_delete_hotkey(setup_db):
    init_db()
    save_hotkey("ctrl+1", "/path/to/sound1.mp3")
    delete_hotkey("ctrl+1")
    hotkeys = load_hotkeys()
    assert len(hotkeys) == 0
