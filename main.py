from logging import exception
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox
from PySide6.QtWidgets import QLabel, QPushButton, QProgressBar, QLineEdit, QGridLayout, QScrollArea, QTextEdit, QListWidget, QStackedWidget, QMessageBox, QMenu, QDialog
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtCore import Signal, QObject
import subprocess
import urllib.request
import zipfile
import os
import ssl
import json
import sys
import shutil
from PySide6.QtGui import QFontMetrics
import threading
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def get_executable_dir():
    """ Get the directory where the executable (or script) is located """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# Use get_executable_dir() for config files that should persist beside the exe
CONFIG_DIR = get_executable_dir()
SETTINGS_FILE = os.path.join(CONFIG_DIR, "Launcher_Settings.json")
DATA_FILE = os.path.join(CONFIG_DIR, "Launcher_Data.json")
INSTANCES_BASE_DIR = os.path.join(CONFIG_DIR, "Instances")

settings = {}
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE) as f:
        settings = json.load(f)
else:
    # Default settings if file doesn't exist
    settings = {
        "Theme": "Dark",
        "Instance Path": "Instances/",
        "Close Launcher Startup": False
    }
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def get_theme_stylesheet(theme_name):
    if theme_name == "Light":
        return """
            QWidget { background-color: rgb(240, 240, 240); color: black; }
            QPushButton { background-color: rgb(225, 225, 225); color: black; border: 1px solid rgb(200, 200, 200); border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background-color: rgb(210, 210, 210); }
            QPushButton:pressed { background-color: rgb(190, 190, 190); }
            QLineEdit, QComboBox, QListWidget, QTextEdit { background-color: white; color: black; border: 1px solid rgb(200, 200, 200); }
            QScrollArea { border: none; }
            #topBar { background-color: rgb(220, 220, 220); }
            #sidebar { background-color: rgb(230, 230, 230); }
            #categoryList { background-color: rgb(220, 220, 220); }
            #subtabList { background-color: rgb(210, 210, 210); }
        """
    else: # Dark
        return """
            QWidget { background-color: rgb(32, 35, 38); color: white; }
            QPushButton { background-color: rgb(45, 48, 50); color: white; border: 1px solid rgb(60, 63, 65); border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background-color: rgb(55, 58, 60); }
            QPushButton:pressed { background-color: rgb(35, 38, 40); }
            QLineEdit, QComboBox, QListWidget, QTextEdit { background-color: rgb(45, 48, 50); color: white; border: 1px solid rgb(60, 63, 65); }
            QScrollArea { border: none; }
            #topBar { background-color: rgb(27, 30, 32); }
            #sidebar { background-color: rgb(24, 26, 27); }
            #categoryList { background-color: rgb(24, 26, 27); }
            #subtabList { background-color: rgb(27, 30, 32); }
        """

def apply_theme(app_or_widget, theme_name):
    app_or_widget.setStyleSheet(get_theme_stylesheet(theme_name))

def open_about_window():
    about = QDialog()
    about.setWindowTitle("About")
    about.setFixedSize(500, 220)

    layout = QVBoxLayout()

    text = QLabel("""
        <b>Legacy Console Edition Launcher</b><br>
        the peakest of the peakest launchers (probably not).<br><br>
        Made by Blake because no one else wanted to make one and I got bored.<br>
        If something breaks, contact me or make a github issue, and dont be a jerk.<br><br>
        Github: https://github.com/xblake2012x/Minecraft-Legacy-Console-Edition-Launcher
        Discord: xblake.2012x<br>
        Email: Blake_Brent@outlook.com
        """)
    text.setAlignment(Qt.AlignCenter)
    text.setWordWrap(True)

    close_btn = QPushButton("Close")
    close_btn.clicked.connect(about.close)

    layout.addWidget(text)
    layout.addWidget(close_btn)
    about.setLayout(layout)
    about.exec()


class LogEmitter(QObject):
    new_line = Signal(str)

def perform_launcher_update(window, download_url):
    status_label = window.findChild(QLabel, "status_label")
    status_label.setText("Updating... Please  do not close the launcher.")
    status_label.show()

    def update_thread():
        try:
            zip_path = "launcher_update.zip"
            # Download
            with urllib.request.urlopen(download_url) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            
            os.remove(zip_path)
            
            # Restart notice
            status_label.setText("Update complete! Restarting...")
            time.sleep(2)
            
            # Restart the application
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            status_label.setText(f"Update failed: {str(e)}")

    threading.Thread(target=update_thread).start()

def check_for_launcher_updates(window):
    status_label = window.findChild(QLabel, "status_label")
    update_btn = window.findChild(QPushButton, "launcher_update_btn")
    if update_btn:
        update_btn.hide()

    status_label.setText("Checking...")
    status_label.show()
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                local_data = json.load(f)
        else:
            # Fallback if Data.json is missing
            local_data = {"Version": "0.0.0", "Check Update Link": "https://raw.githubusercontent.com/xblake2012x/Minecraft-Legacy-Console-Edition-Launcher/main/Launcher_Data.json"}
        
        url = local_data["Check Update Link"]
        with urllib.request.urlopen(url) as response:
            remote_data = json.load(response)
    except Exception as e:
        status_label.setText(f"Error checking updates: {str(e)}")
        return

    local_version = local_data.get("Version", "0.0.0").split('.')
    remote_version = remote_data.get("Version", "0.0.0").split('.')
    
    is_newer = False
    for i in range(max(len(local_version), len(remote_version))):
        v1 = int(local_version[i]) if i < len(local_version) else 0
        v2 = int(remote_version[i]) if i < len(remote_version) else 0
        if v2 > v1:
            is_newer = True
            break
        elif v1 > v2:
            break

    if is_newer:
        status_label.setText(f"Update available: {remote_data.get('Version')}")
        if update_btn and "Download URL" in remote_data:
            update_btn.show()
            # Disconnect previous if any
            try: update_btn.clicked.disconnect()
            except: pass
            update_btn.clicked.connect(lambda: perform_launcher_update(window, remote_data["Download URL"]))
    else:
        status_label.setText("Launcher is up to date.")

def apply_sort_logic(mode, instances):
    if mode == "A–Z":
        instances.sort(key=lambda x: x.get("Name", "No Name").lower())
    elif mode == "Z–A":
        instances.sort(key=lambda x: x.get("Name", "No Name").lower(), reverse=True)
    elif mode == "Newest":
        instances.sort(key=lambda x: float(x.get("Created", 0)), reverse=True)
    elif mode == "Oldest":
        instances.sort(key=lambda x: float(x.get("Created", 0)))

def apply_sort(sort_box, instances):
    mode = sort_box.currentText()
    apply_sort_logic(mode, instances)
    refresh_instance_buttons(instances)


def save_settings(window,json_file):
    global settings
    global app

    settings["Theme"] = window.findChild(QComboBox, "Theme").currentText()
    settings["Close Launcher Startup"] = window.findChild(QCheckBox, "Close Launcher Startup").isChecked()
    settings["Instance Path"] = window.findChild(QLineEdit, "Instance Path").text()

    with open(json_file, "w") as f:
        json.dump(settings,f,indent=4)

    apply_theme(app, settings["Theme"])
    refresh_instance_buttons()

def open_settings_window():
    settings_file = SETTINGS_FILE
    # Re-load to ensure we have latest
    global settings
    if os.path.exists(settings_file):
        with open(settings_file) as f:
            settings = json.load(f)

    win = QWidget()
    win.setWindowTitle("Settings")
    win.resize(800, 500)

    layout = QHBoxLayout(win)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # LEFT: Category list
    Left_List = QVBoxLayout()
    category_list = QListWidget()
    category_list.setObjectName("categoryList")
    category_list.addItems(["Launcher", "Minecraft", "Updates"])
    category_list.setFixedWidth(150)
    
    # Save Button
    save_btn = QPushButton("Save Settings")
    save_btn.setFixedHeight(40)
    save_btn.clicked.connect(lambda: save_settings(win,settings_file))
    
    Left_List.addWidget(category_list)
    Left_List.addWidget(save_btn)
    layout.addLayout(Left_List)
    # MIDDLE: Sub-tabs
    subtab_list = QListWidget()
    subtab_list.setObjectName("subtabList")
    subtab_list.setFixedWidth(150)
    layout.addWidget(subtab_list)

    # RIGHT: Settings panel (stacked pages)
    settings_stack = QStackedWidget()
    layout.addWidget(settings_stack)

    pages = ["launcher_graphics","minecraft_general","minecraft_paths","updates_launcher","error_page"]
    setting_pages = {}
    for page in pages:
        setting_pages[page] = QWidget()
    for page in setting_pages.values():
        settings_stack.addWidget(page)
    error_page = QVBoxLayout(setting_pages["error_page"])
    error_label = QLabel("Error, this sub-category do not have a page, update your launcher if possible")
    error_page.addWidget(error_label)

    # Launcher Graphics Sub Category
    graphics_layout = QVBoxLayout(setting_pages["launcher_graphics"])
    graphics_layout.setContentsMargins(20, 20, 20, 20)
    graphics_layout.setSpacing(15)

    theme_label = QLabel("Theme")
    theme_label.setStyleSheet("font-size: 14px;")
    graphics_layout.addWidget(theme_label)

    theme_dropdown = QComboBox()
    theme_dropdown.setObjectName("Theme")
    theme_dropdown.addItems(["Dark", "Light"])
    theme_dropdown.setCurrentText(settings.get("Theme","Dark"))
    theme_dropdown.currentTextChanged.connect(lambda t: apply_theme(app, t))
    graphics_layout.addWidget(theme_dropdown)
    graphics_layout.addStretch()

    # Minecraft General Sub Category
    minecraft_general_layout = QVBoxLayout(setting_pages["minecraft_general"])
    minecraft_general_layout.setContentsMargins(20, 20, 20, 20)
    minecraft_general_layout.setSpacing(15)

    bootup_label = QCheckBox("Close Launcher when the game starts")
    bootup_label.setObjectName("Close Launcher Startup")
    bootup_label.setChecked(settings.get("Close Launcher Startup",False))
    bootup_label.setStyleSheet("font-size: 14px;")
    minecraft_general_layout.addWidget(bootup_label)

    minecraft_general_layout.addStretch()

    # Minecraft Path Sub Category
    minecraft_path_layout = QVBoxLayout(setting_pages["minecraft_paths"])
    minecraft_path_layout.setContentsMargins(20, 20, 20, 20)
    minecraft_path_layout.setSpacing(15)

    path_label = QLabel("Instance path")
    minecraft_path_layout.addWidget(path_label)

    path_input = QLineEdit()
    path_input.setObjectName("Instance Path")
    path_input.setPlaceholderText("Enter path...")
    path_input.setText(settings.get("Instance Path","Instances/"))
    minecraft_path_layout.addWidget(path_input)

    minecraft_path_layout.addStretch()

    # Updates Launcher Sub Category
    updates_launcher_layout = QVBoxLayout(setting_pages["updates_launcher"])
    updates_launcher_layout.setContentsMargins(20, 20, 20, 20)
    updates_launcher_layout.setSpacing(15)

    status_label = QLabel("Status Label")
    status_label.setObjectName("status_label")
    status_label.hide()
    updates_launcher_layout.addWidget(status_label)

    update_now_btn = QPushButton("Update Now")
    update_now_btn.setObjectName("launcher_update_btn")
    update_now_btn.setFixedHeight(40)
    update_now_btn.hide()
    updates_launcher_layout.addWidget(update_now_btn)

    btn = QPushButton("Check for updates")
    btn.setFixedHeight(40)
    btn.clicked.connect(lambda: check_for_launcher_updates(win))
    updates_launcher_layout.addWidget(btn)

    updates_launcher_layout.addStretch()

    # When category changes, update sub-tabs
    def update_subtabs():
        save_index = subtab_list.currentRow()
        subtab_list.clear()
        cat = category_list.currentItem().text()

        if cat == "Launcher":
            subtab_list.addItems(["Graphics"])
        elif cat == "Minecraft":
            subtab_list.addItems(["General", "Paths"])
        elif cat == "Updates":
            subtab_list.addItems(["Launcher"])

        if subtab_list.count() - 1 >= save_index and save_index > -1:
            subtab_list.setCurrentRow(save_index)
        elif subtab_list.count() > 0:
            subtab_list.setCurrentRow(0)

    category_list.currentRowChanged.connect(update_subtabs)
    category_list.setCurrentRow(0)

    # When sub-tab changes, switch pages
    def update_page():
        if subtab_list.currentItem() is None:
            return
        cat = category_list.currentItem().text()
        sub = subtab_list.currentItem().text()

        page_id = f"{cat.lower()}_{sub.lower()}"
        if page_id in setting_pages:
            settings_stack.setCurrentWidget(setting_pages[page_id])
        else:
            settings_stack.setCurrentWidget(setting_pages["error_page"])

    subtab_list.currentRowChanged.connect(update_page)

    win.show()
    open_windows.append(win)

def open_logs_window(name):
    log_win = QWidget()
    log_win.setWindowTitle(f"Game Logs for Minecraft Instance \"{name}\"")
    log_win.resize(600, 400)
    log_win.setStyleSheet("background-color: rgb(32, 35, 38);")

    layout = QVBoxLayout(log_win)
    layout.setContentsMargins(10, 10, 10, 10)

    log_box = QTextEdit()
    log_box.setReadOnly(True)
    log_box.setStyleSheet("color: white; font-size: 14px;")
    layout.addWidget(log_box)

    emitter = LogEmitter()
    emitter.new_line.connect(log_box.append)

    log_win.closed = False

    def on_close(event):
        log_win.closed = True
        event.accept()

    log_win.closeEvent = on_close

    log_win.show()
    open_windows.append(log_win)

    return log_win, log_box, emitter

def open_instance_folder(inst):
    if not inst or not inst.get("Path"):
        return
    folder = os.path.dirname(os.path.dirname(inst["Path"]))

    if sys.platform.startswith("linux"):
        subprocess.Popen(["xdg-open", folder])
    elif sys.platform.startswith("win"):
        os.startfile(folder)
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", folder])

def delete_instance(inst):
    global selected_instance
    if not inst or not inst.get("Path"):
        return
    folder = os.path.dirname(os.path.dirname(inst["Path"]))
    if os.path.exists(folder):
        shutil.rmtree(folder)
        selected_instance = {"Name": "None", "Path": None, "Icon": "Instances/icon.png", "Args": [], "WinePrefix": ""}
    text_label.setText("Nothing Selected")
    refresh_instance_buttons()

def enable_rename(inst):
    if inst["Name"] == "None":
        return

    rename_box.setText(inst["Name"])
    text_label.hide()
    rename_box.show()
    rename_box.setFocus()

def finish_rename(inst, new_name):
    new_name = new_name.strip()
    if not new_name:
        rename_box.hide()
        text_label.show()
        return

    old_name = inst["Name"]
    old_dir = os.path.join(INSTANCES_BASE_DIR, old_name)
    new_dir = os.path.join(INSTANCES_BASE_DIR, new_name)

    # rename folder
    if os.path.exists(old_dir):
        os.rename(old_dir, new_dir)

    # update JSON paths
    inst["Name"] = new_name
    inst["Icon"] = os.path.join(new_dir, "icon.png")
    inst["Path"] = os.path.join(new_dir, "minecraft", "Minecraft.Client.exe")

    # write updated JSON
    with open(os.path.join(new_dir, "instance.json"), "w") as f:
        json.dump(inst, f, indent=4)

    # update UI
    text_label.setText(new_name)
    rename_box.hide()
    text_label.show()
    refresh_instance_buttons()



def elide_text(text, width, font):
    metrics = QFontMetrics(font)
    return metrics.elidedText(text, Qt.ElideRight, width)

def wine_available():
    return shutil.which("wine") is not None

if sys.platform.startswith("linux"):
    print("Running on Linux")
elif sys.platform.startswith("win"):
    print("Running on Windows")
elif sys.platform.startswith("darwin"):
    print("Running on macOS")

# Use resource_path for the default icon which might be bundled
DEFAULT_ICON = resource_path("Instances/icon.png")

selected_instance = {"Name": "None", "Path": None, "Icon": DEFAULT_ICON, "Args": [], "WinePrefix": ""}
url = "https://github.com/MCLCE/MinecraftConsoles/releases/download/nightly/LCEWindows64.zip"
def select_instance(inst):
    global selected_instance
    selected_instance = inst

    rename_box.hide()
    text_label.show()

    text_label.setText(inst["Name"])
    pixmap = QPixmap(inst["Icon"])
    img_label.setPixmap(pixmap)
    refresh_instance_buttons()

def duplicate_instance(inst):
    old_name = inst["Name"]
    base = "Instances"

    new_name = old_name + "_Copy"
    new_dir = os.path.join(base, new_name)

    i = 1
    while os.path.exists(new_dir):
        new_name = f"{old_name}_Copy{i}"
        new_dir = os.path.join(base, new_name)
        i += 1

    shutil.copytree(os.path.join(base, old_name), new_dir)

    json_path = os.path.join(new_dir, "instance.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    data["Name"] = new_name
    data["Created"] = time.time()

    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    refresh_instance_buttons()


def create_instance_tile(inst):
    w = QWidget()
    w.setFixedSize(120, 140)

    # selected highlight
    is_selected = (selected_instance.get("Path") == inst.get("Path")) if (selected_instance and inst) else False
    if is_selected:
        w.setStyleSheet("""
            QWidget {
                border: 2px solid rgb(85, 170, 255);
                border-radius: 6px;
            }
        """)
    else:
        w.setStyleSheet("""
            QWidget {
                background-color: rgb(45, 48, 50);
                border: 1px solid rgb(60, 63, 65);
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: rgb(55, 58, 60);
            }
        """)

    layout = QVBoxLayout(w)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(8)

    # inner container
    inner = QWidget()
    inner_layout = QVBoxLayout(inner)
    inner_layout.setContentsMargins(0, 0, 0, 0)
    inner_layout.setSpacing(6)
    inner_layout.setAlignment(Qt.AlignHCenter)

    # icon
    icon_label = QLabel()
    pix = QPixmap(inst["Icon"])
    icon_label.setPixmap(pix)
    icon_label.setScaledContents(True)
    icon_label.setFixedSize(90, 90)
    inner_layout.addWidget(icon_label, alignment=Qt.AlignHCenter)

    # name
    name_label = QLabel()
    name_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
    name_label.setWordWrap(True)
    name_label.setFixedWidth(100)
    name_label.setMinimumHeight(35)
    name_label.setMaximumHeight(40)

    font = name_label.font()
    name_label.setText(elide_text(inst["Name"], 130, font))

    inner_layout.addWidget(name_label)

    layout.addWidget(inner, alignment=Qt.AlignHCenter)

    # click handler
    def mousePress(event, inst=inst):
        if event.button() == Qt.RightButton:
            select_instance(inst)
            menu = QMenu()

            separators = []
            title = menu.addSection(inst.get("Name", "Unknown"))
            rename = menu.addAction("Rename")
            separators.append(menu.addSeparator())
            play = menu.addAction("Play")
            separators.append(menu.addSeparator())
            edit = menu.addAction("Edit")
            duplicate = menu.addAction("Duplicate")
            open_folder = menu.addAction("Open Folder")
            delete = menu.addAction("Delete")

            action = menu.exec(w.mapToGlobal(event.position().toPoint()))

            if action == play:
                launch_game(inst)

            elif action == edit:
                select_instance(inst)
                open_edit_instance_window()

            elif action == duplicate:
                duplicate_instance(inst)

            elif action == open_folder:
                open_instance_folder(inst)

            elif action == delete:
                delete_instance(inst)

            elif action == rename:
                enable_rename(inst)

        else:
            # Left click = select instance
            select_instance(inst)

    w.mousePressEvent = mousePress
    w.instance_name = inst["Name"]

    return w

def filter_instances(self, content_layout, text):
    text = text.lower()

    for i in range(content_layout.count()):
        item = content_layout.itemAt(i)
        widget = item.widget()

        if widget is None:
            continue

        # Assuming each instance widget has a .instance_name attribute
        name = getattr(widget, "instance_name", "").lower()

        widget.setVisible(text in name)


def refresh_instance_buttons(instances=None):
    # Clear old widgets
    for i in reversed(range(content_layout.count())):
        item = content_layout.itemAt(i)
        if item and item.widget():
            item.widget().deleteLater()

    if instances is None:
        instances = load_instances()
        try:
            apply_sort_logic(sort_box.currentText(), instances)
        except NameError:
            pass

    cols = max(1, content.width() // 140)
    row = 0
    col = 0

    for inst in instances:
        w = create_instance_tile(inst)  # we’ll define this below

        content_layout.addWidget(w, row, col)

        col += 1
        if col >= cols:
            col = 0
            row += 1

def load_instances():
    instances = []
    base = INSTANCES_BASE_DIR

    if not os.path.exists(base):
        os.makedirs(base, exist_ok=True)
        # Copy default icon to Instances dir if it doesn't exist there yet
        icon_dest = os.path.join(base, "icon.png")
        if not os.path.exists(icon_dest):
            try:
                shutil.copy(resource_path("Instances/icon.png"), icon_dest)
            except:
                pass
        return instances

    for name in os.listdir(base):
        json_path = os.path.join(base, name, "instance.json")
        if os.path.isfile(json_path):
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                    instances.append(data)
            except:
                pass

    return instances


def download_and_extract_repo(url, extract_to, instance_name, progress_bar, status):
    base_path = os.path.join(extract_to,instance_name)
    extract_to = os.path.join(extract_to,instance_name,"minecraft")
    print(extract_to)
    os.makedirs(extract_to, exist_ok=True)
    zip_path = os.path.join(extract_to, "temp.zip")

    try:
        status.setText('Downloading')
        print("Downloading repo...")
        download_with_progress(url, zip_path, progress_bar)

        progress_bar.setValue(0)
        status.setText('Extracting')
        print("Extracting...")
        extract_with_progress(zip_path, extract_to, progress_bar)

        status.setText('Setting Up')
        progress_bar.setValue(0)

        instance_root = base_path
        minecraft_path = os.path.join(instance_root, "minecraft")
        json_path = os.path.join(instance_root, "instance.json")

        os.makedirs(instance_root, exist_ok=True)

        icon_src = resource_path("Instances/icon.png")
        icon_dest = os.path.join(INSTANCES_BASE_DIR, instance_name, "icon.png")

        shutil.copy(icon_src, icon_dest)

        progress_bar.setValue(50)

        instance_json = {
            "Name": instance_name,
            "Path": os.path.join(minecraft_path, "Minecraft.Client.exe"),
            "Icon": icon_dest,
            "Args": "",
            "WinePrefix": "",
            "Created": time.time()
        }

        with open(json_path, "w") as f:
            json.dump(instance_json, f, indent=4)

        progress_bar.setValue(100)

    except Exception as e:
        print("Error:", e)

    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

    status.setText('Done')
    progress_bar.setValue(100)
    refresh_instance_buttons()
    print("Done!")

def extract_with_progress(zip_path, extract_to, progress_bar):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        file_list = zip_ref.infolist()
        total_files = len(file_list)

        for i, file in enumerate(file_list):
            zip_ref.extract(file, extract_to)

            percent = int((i + 1) / total_files * 100)
            progress_bar.setValue(percent)


def download_with_progress(url, zip_path, progress_bar):
    context = ssl.create_default_context()

    with urllib.request.urlopen(url, context=context) as response:
        total_size = int(response.getheader("Content-Length", 0))
        downloaded = 0

        with open(zip_path, "wb") as out_file:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break

                out_file.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = int(downloaded / total_size * 100)
                    progress_bar.setValue(percent)


open_windows = []

def check_game(instance_json,start_logs):
    if instance_json["Path"] is not None:
        return False
    else:
        root_dir = os.path.dirname("~/hi")
        missing_files = []
        required_files = ["Minecraft.Client.exe", "Minecraft.Client.exp", "Minecraft.Client.lib", "iggy_w64.dll", "Common","music",'Windows64','Windows64Media']
        for file in required_files:
            if not os.path.exists(os.path.join(root_dir, file)):
                missing_files.append(file)
        if missing_files:
            for file in missing_files:
                start_logs.append(f"Missing file: {file}")
            return False

        return True

def show_crash_popup(exit_code):
    msg = QMessageBox()
    msg.setWindowTitle("Game Crashed")
    msg.setText(f"Minecraft exited with code {exit_code}")
    msg.setIcon(QMessageBox.Critical)
    msg.exec()


# Button Functions
def launch_game(instance_json):
    start_logs = []
    check_game(instance_json,start_logs)
    start_logs.append("Launching Minecraft...")
    command = []
    start_game = True
    if not settings.get("Close Launcher Startup",False) or settings.get("Open Logs Startup",True):
        log_win, log_box, emitter = open_logs_window(instance_json.get("Name","Unknown"))
    start_logs.append(f"Detected platform: {sys.platform}")
    if not instance_json["Path"] is None:
        exe_path = instance_json["Path"]
        try:
            os.chmod(exe_path, 0o755)
        except:
            pass
        if sys.platform.startswith("linux"):
            start_logs.append("Setting up Linux command")
            wine = selected_instance.get("WinePrefix", "")
            if wine_available() or not wine == "":
                args = selected_instance.get("Args", "").split()
                command += [wine if wine != "" else "wine", exe_path] + args
            else:
                start_logs.append("Wine is not installed!")
                start_game = False

        elif sys.platform.startswith("win"):
            start_logs.append("Setting up Windows command")
            args = selected_instance.get("Args", "").split()
            command += [exe_path] + args

        elif sys.platform.startswith("darwin"):
            start_logs.append("Setting up MacOS command")
            args = selected_instance.get("Args", "").split()
            wine = selected_instance.get("WinePrefix", "")
            command += [wine if wine != "" else "wine", exe_path] + args

        else:
            start_logs.append("Unsupported OS")
            start_game = False
    else:
        print("No Path")
        start_logs.append("No Path")
        start_game = False

    proc = None
    try:
        proc = subprocess.Popen(command if start_game else instance_json["Path"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True)

    except Exception as E:
        start_logs.append(f"Error: {E}")

    if not settings.get("Close Launcher Startup",False) or settings.get("Open Logs Startup",True):
        for line in start_logs:
            if log_win.closed:
                break
            emitter.new_line.emit(line.rstrip())
        if proc:
            def read_output():
                for line in proc.stdout:
                    if log_win.closed:
                        break
                    emitter.new_line.emit(line.rstrip())

            threading.Thread(target=read_output, daemon=True).start()

            def watch_process():
                exit_code = proc.wait()
                emitter.new_line.emit(f"[Launcher] Game exited with code {exit_code}")
                if exit_code != 193:
                    show_crash_popup(exit_code)

            threading.Thread(target=watch_process, daemon=True).start()

        else:
            pass

    if settings.get("Close Launcher Startup",False):
        window.close()
        return


def open_add_instance_window():
    print('making window')
    add_window = QWidget()
    add_window.setWindowTitle("Add Instance")
    add_window.resize(400, 300)
    add_window.setStyleSheet("background-color: rgb(32, 35, 38);")

    layout = QVBoxLayout(add_window)
    layout.setSpacing(8)
    layout.setContentsMargins(10, 10, 10, 10)

    label = QLabel("Create a new instance")
    label.setStyleSheet("color: white; font-size: 16px;")
    label.setAlignment(Qt.AlignHCenter)
    layout.addWidget(label)

    # name field
    name_input = QLineEdit()
    name_input.setPlaceholderText("Instance Name")
    name_input.setText("My Minecraft Instance")
    name_input.setStyleSheet("color: white; font-size: 14px;")

    layout.addWidget(name_input)

    layout.addStretch()

    bottom = QVBoxLayout()
    bottom.setSpacing(8)
    bottom.setContentsMargins(10, 10, 10, 10)

    add_button = QPushButton("Download and Install instance")
    add_button.setFixedHeight(40)

    add_button.setStyleSheet("""
        QPushButton {
            background-color: rgb(45, 48, 50);
            color: white;
            border: 1px solid rgb(60, 63, 65);
            border-radius: 6px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: rgb(55, 58, 60);
        }
        QPushButton:pressed {
            background-color: rgb(35, 38, 40);
        }
    """)
    add_button.clicked.connect(
        lambda: download_and_extract_repo(url, settings.get("Instance Path","Instances/"), name_input.text(), progress, status)
    )

    # Status Text
    status = QLabel("Not Doing Anything")
    status.setStyleSheet("color: white; font-size: 14px;")
    status.setAlignment(Qt.AlignHCenter)

    # Progress Bar
    progress = QProgressBar()
    progress.setValue(0)
    progress.setStyleSheet("""
        QProgressBar {
            background-color: rgb(45, 48, 50);
            color: white;
            border: 1px solid rgb(60, 63, 65);
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: rgb(85, 170, 85);
        }
    """)

    bottom.addWidget(status)
    bottom.addWidget(progress)
    bottom.addWidget(add_button)

    layout.addLayout(bottom)
    add_window.show()
    open_windows.append(add_window)
    print('made window')

def save_instance_settings(args, prefix, window):
    selected_instance["Args"] = args
    selected_instance["WinePrefix"] = prefix

    inst_dir = os.path.dirname(os.path.dirname(selected_instance["Path"]))
    json_path = os.path.join(inst_dir, "instance.json")

    with open(json_path, "w") as f:
        json.dump(selected_instance, f, indent=4)

    window.close()


def open_edit_instance_window():
    if selected_instance["Name"] == "None":
        return

    edit = QWidget()
    edit.setWindowTitle(f"Edit Instance - {selected_instance['Name']}")
    edit.resize(400, 300)
    edit.setStyleSheet("background-color: rgb(32, 35, 38);")

    layout = QVBoxLayout(edit)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Launch Args
    args_label = QLabel("Launch Arguments")
    args_label.setStyleSheet("color: white; font-size: 14px;")
    layout.addWidget(args_label)

    args_box = QLineEdit()
    args_box.setText(selected_instance.get("Args", ""))
    args_box.setStyleSheet("color: white; font-size: 14px;")
    layout.addWidget(args_box)

    # Wine Prefix
    if not sys.platform.startswith("win"):
        prefix_label = QLabel("Wine Prefix ")
        prefix_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(prefix_label)

        prefix_box = QLineEdit()
        prefix_box.setText(selected_instance.get("WinePrefix", ""))
        prefix_box.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(prefix_box)

    # Open Folder Button
    folder_btn = QPushButton("Open Instance Folder")
    folder_btn.setFixedHeight(35)
    folder_btn.clicked.connect(lambda: open_instance_folder(selected_instance))
    layout.addWidget(folder_btn)

    # Save Button
    save_btn = QPushButton("Save")
    save_btn.setFixedHeight(40)
    save_btn.clicked.connect(lambda: save_instance_settings(args_box.text(), prefix_box.text(), edit))
    layout.addWidget(save_btn)

    edit.show()
    open_windows.append(edit)


app = QApplication([])
apply_theme(app, settings.get("Theme", "Dark"))

window = QWidget()
window.setWindowTitle("Legacy Launcher")
window.resize(850, 650)

root = QVBoxLayout()
root.setContentsMargins(0, 0, 0, 0)
root.setSpacing(0)
window.setLayout(root)

# Top Bar
top_bar = QWidget()
top_bar.setObjectName("topBar")
top_bar_layout = QHBoxLayout(top_bar)
top_bar.setFixedHeight(50)

# Add Instance Button
add_instance_button = QPushButton("Add Instance")
add_instance_button.setFixedHeight(40)
add_instance_button.clicked.connect(open_add_instance_window)

# Settings
settings_button = QPushButton("Settings")
settings_button.setFixedHeight(40)
settings_button.clicked.connect(open_settings_window)

# About
about_button = QPushButton("About")
about_button.setFixedHeight(40)
about_button.clicked.connect(open_about_window)

top_bar_layout.addWidget(add_instance_button)
top_bar_layout.addWidget(settings_button)
top_bar_layout.addWidget(about_button)
top_bar_layout.addStretch()

root.addWidget(top_bar)

search_bar = QLineEdit()
search_bar.setPlaceholderText("Search instances...")
search_bar.textChanged.connect(lambda: filter_instances(search_bar,content_layout,search_bar.text()))

# Main Area
middle = QHBoxLayout()
middle.setContentsMargins(0, 0, 0, 0)
middle.setSpacing(0)
root.addLayout(middle)
left_side = QVBoxLayout()
middle.addLayout(left_side)
left_side.addWidget(search_bar)

sort_box = QComboBox()
sort_box.addItems(["A–Z", "Z–A", "Newest", "Oldest"])
sort_box.currentIndexChanged.connect(lambda: apply_sort(sort_box, load_instances()))
left_side.addWidget(sort_box)


content = QWidget()
scroll = QScrollArea()
scroll.setWidgetResizable(True)


content = QWidget()
content_layout = QGridLayout(content)

scroll.setWidget(content)
left_side.addWidget(scroll)

content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
content_layout.setContentsMargins(10, 10, 10, 10)
content_layout.setSpacing(10)
refresh_instance_buttons()

# Sidebar
sidebar = QWidget()
sidebar.setObjectName("sidebar")
sidebar.setFixedWidth(200)
sidebar_layout = QVBoxLayout(sidebar)
sidebar_layout.setContentsMargins(0, 0, 0, 0)
sidebar_layout.setSpacing(10)

# Image
img_label = QLabel()
pixmap = QPixmap(DEFAULT_ICON)
img_label.setPixmap(pixmap)
img_label.setScaledContents(True)
img_label.setMaximumHeight(200)

# Text
text_label = QLabel("Nothing Selected")
rename_box = QLineEdit()
rename_box.setAlignment(Qt.AlignHCenter)
rename_box.hide()
text_label.setAlignment(Qt.AlignHCenter)
text_label.mousePressEvent = lambda _: enable_rename(selected_instance)
rename_box.returnPressed.connect(lambda: finish_rename(selected_instance,rename_box.text()))


# Play Button
play_button = QPushButton("Play")
play_button.setFixedHeight(40)
play_button.clicked.connect(lambda: launch_game(selected_instance))

# Delete Button
delete_button = QPushButton("Delete")
delete_button.setFixedHeight(40)
delete_button.clicked.connect(lambda: delete_instance(selected_instance))

# Open Instance Folder
open_instance_folder_button = QPushButton("Open Folder")
open_instance_folder_button.setFixedHeight(40)
open_instance_folder_button.clicked.connect(lambda: open_instance_folder(selected_instance))

# Edit
edit_button = QPushButton("Edit")
edit_button.setFixedHeight(40)
edit_button.clicked.connect(open_edit_instance_window)

# Add Widgets
sidebar_layout.addWidget(img_label)
sidebar_layout.addWidget(text_label)
sidebar_layout.addWidget(play_button)
sidebar_layout.addWidget(edit_button)
sidebar_layout.addWidget(open_instance_folder_button)
sidebar_layout.addWidget(delete_button)

sidebar_layout.addStretch()
middle.addWidget(sidebar)

window.show()
app.exec()
