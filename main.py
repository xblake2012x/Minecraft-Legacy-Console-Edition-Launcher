from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox
from PySide6.QtWidgets import QLabel, QPushButton, QProgressBar, QLineEdit, QGridLayout, QScrollArea, QTextEdit, QListWidget, QStackedWidget
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

settings = {}
with open("Launcher_Settings.json") as f:
    settings = json.load(f)

class LogEmitter(QObject):
    new_line = Signal(str)

def check_update():
    try:
        with open("Launcher_Data.json") as f:
            data = json.load(f)
        url = data["Check Update Link"]
    except:
        return "Invalid Launcher Data File"

    try:
        with urllib.request.urlopen(url) as response:
            datedversion = json.load(response)
    except:
        return "Cant Reach"

    try:
        data = data["Version"].split('.')
        datedversion = datedversion["Version"].split('.')
        for i, char in enumerate(data):
            if int(char) > int(datedversion[i]):
                return "Not Valid Local Data"
            elif int(datedversion[i]) > int(char):
                return False
        return True
    except:
        return "Invalid Meta Data"

def check_for_launcher_updates(window):
    status_label = window.findChild(QLabel, "status_label")
    status_label.setText("Checking")
    status_label.show()
    status = check_update()
    if status == True:
        status_label.setText("Up To Date")
    elif status == False:
        status_label.setText("Need to be updated")
    elif status == "Invalid Launcher Data File":
        status_label.setText("Reading Launcher_Data.json ran into an error")
    elif status == "Cant Reach":
        status_label.setText("Couldn\'t reach the set update link in Launcher_Data.json Check you\'r internet and try again")
    elif status == "Not Valid Local Data":
        status_label.setText("Launcher_Data.json states version higher than github version")
    elif status == "Invalid Meta Data":
        status_label.setText("Launcher_Data.json or github version meta data was invalid")

def save_settings(window,json_file):
    global settings

    settings["Theme"] = window.findChild(QComboBox, "Theme").currentText()
    settings["Close Launcher Startup"] = window.findChild(QCheckBox, "Close Launcher Startup").isChecked()
    settings["Instance Path"] = window.findChild(QLineEdit, "Instance Path").text()

    with open(json_file, "w") as f:
        json.dump(settings,f,indent=4)

    load_instances()

def open_settings_window():
    settings_file = "Launcher_Settings.json"
    settings = {}
    with open(settings_file) as f:
        settings = json.load(f)

    win = QWidget()
    win.setWindowTitle("Settings")
    win.resize(800, 500)
    win.setStyleSheet("background-color: rgb(32, 35, 38);")

    layout = QHBoxLayout(win)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    # LEFT: Category list
    Left_List = QVBoxLayout()
    category_list = QListWidget()
    category_list.addItems(["Launcher", "Minecraft", "Updates"])
    category_list.setFixedWidth(150)
    category_list.setStyleSheet("color: white; background-color: rgb(24, 26, 27);")
    save_btn = QPushButton("Save Settings")
    save_btn.setFixedHeight(40)
    save_btn.setStyleSheet("""
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
    save_btn.clicked.connect(lambda: save_settings(win,settings_file))

    Left_List.addWidget(category_list)
    Left_List.addWidget(save_btn)
    layout.addLayout(Left_List)
    # MIDDLE: Sub-tabs
    subtab_list = QListWidget()
    subtab_list.setFixedWidth(150)
    subtab_list.setStyleSheet("color: white; background-color: rgb(27, 30, 32);")
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
    theme_label.setStyleSheet("color: white; font-size: 14px;")
    graphics_layout.addWidget(theme_label)

    theme_dropdown = QComboBox()
    theme_dropdown.setObjectName("Theme")
    theme_dropdown.addItems(["Dark", "Light"])
    theme_dropdown.setStyleSheet("color: white; background-color: rgb(45,48,50);")
    theme_dropdown.setCurrentText(settings.get("Theme","Dark"))
    graphics_layout.addWidget(theme_dropdown)
    graphics_layout.addStretch()

    # Minecraft General Sub Category
    minecraft_general_layout = QVBoxLayout(setting_pages["minecraft_general"])
    minecraft_general_layout.setContentsMargins(20, 20, 20, 20)
    minecraft_general_layout.setSpacing(15)

    bootup_label = QCheckBox("Close Launcher when the game starts")
    bootup_label.setObjectName("Close Launcher Startup")
    bootup_label.setChecked(settings.get("Close Launcher Startup",False))
    bootup_label.setStyleSheet("color: white; font-size: 14px;")
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
    path_input.setStyleSheet("color: white; background-color: rgb(45,48,50);")
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

    btn = QPushButton("Check for updates")
    btn.setFixedHeight(40)
    btn.setStyleSheet("""
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
    folder = os.path.dirname(os.path.dirname(inst["Path"]))

    if sys.platform.startswith("linux"):
        subprocess.Popen(["xdg-open", folder])
    elif sys.platform.startswith("win"):
        os.startfile(folder)
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", folder])

def delete_instance(inst):
    global selected_instance
    folder = os.path.dirname(os.path.dirname(inst["Path"]))
    if os.path.exists(folder):
        shutil.rmtree(folder)
        selected_instance = {"Name": "None", "Path": None, "Icon": "Instances/icon.png", "Args": [], "WinePrefix": ""}
    text_label.setText("Nothing Selected")
    refresh_instance_buttons()

def enable_rename():
    if selected_instance["Name"] == "None":
        return

    rename_box.setText(selected_instance["Name"])
    text_label.hide()
    rename_box.show()
    rename_box.setFocus()

def finish_rename():
    global selected_instance

    new_name = rename_box.text().strip()
    if not new_name:
        rename_box.hide()
        text_label.show()
        return

    old_name = selected_instance["Name"]
    old_dir = os.path.join("Instances", old_name)
    new_dir = os.path.join("Instances", new_name)

    # rename folder
    if os.path.exists(old_dir):
        os.rename(old_dir, new_dir)

    # update JSON paths
    selected_instance["Name"] = new_name
    selected_instance["Icon"] = os.path.join(new_dir, "icon.png")
    selected_instance["Path"] = os.path.join(new_dir, "minecraft", "Minecraft.Client.exe")

    # write updated JSON
    with open(os.path.join(new_dir, "instance.json"), "w") as f:
        json.dump(selected_instance, f, indent=4)

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
selected_instance = {"Name": "None", "Path": None, "Icon": "Instances/icon.png", "Args": [], "WinePrefix": ""}
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


def create_instance_tile(inst):
    w = QWidget()
    w.setFixedSize(120, 140)

    # selected highlight
    if selected_instance == inst:
        w.setStyleSheet("""
            QWidget {
                background-color: rgb(55, 58, 60);
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
    w.mousePressEvent = lambda _, i=inst: select_instance(i)

    return w


def refresh_instance_buttons():
    # Clear old widgets
    for i in reversed(range(content_layout.count())):
        item = content_layout.itemAt(i)
        if item and item.widget():
            item.widget().deleteLater()

    instances = load_instances()

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
    base = "Instances"

    if not os.path.exists(base):
        os.makedirs(base, exist_ok=True)
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

        icon_src = "Instances/icon.png"
        icon_dest = f"Instances/{instance_name}/icon.png"

        shutil.copy(icon_src, icon_dest)

        progress_bar.setValue(50)

        instance_json = {
            "Name": instance_name,
            "Path": os.path.join(minecraft_path, "Minecraft.Client.exe"),
            "Icon": icon_dest,
            "Args": "",
            "WinePrefix": ""
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

# Button Functions
def launch_game(instance_json):
    print("Launching Minecraft...")
    command = []
    if not settings.get("Close Launcher Startup",False) or settings.get("Open Logs Startup",True):
        log_win, log_box, emitter = open_logs_window(instance_json.get("Name","Unknown"))
    print(f"Detected platform:{sys.platform}")
    if not instance_json["Path"] is None:
        exe_path = instance_json["Path"]
        try:
            os.chmod(exe_path, 0o755)
        except:
            pass
        if sys.platform.startswith("linux"):
            print("Setting up Linux command")
            wine = selected_instance.get("WinePrefix", "")
            if wine_available() or not wine == "":
                args = selected_instance.get("Args", "").split()
                command += [wine if wine != "" else "wine", exe_path] + args
            else:
                print("Wine is not installed!")
                return

        elif sys.platform.startswith("win"):
            print("Setting up Windows command")
            args = selected_instance.get("Args", "").split()
            command += [exe_path] + args

        elif sys.platform.startswith("darwin"):
            print("Setting up MacOS command")
            args = selected_instance.get("Args", "").split()
            wine = selected_instance.get("WinePrefix", "")
            command += [wine if wine != "" else "wine", exe_path] + args

        else:
            print("Unsupported OS")
            return
    else:
        print("No Path")
        return

    proc = subprocess.Popen(command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True)

    if not settings.get("Close Launcher Startup",False) or settings.get("Open Logs Startup",True):
        def read_output():
            for line in proc.stdout:
                if log_win.closed:
                    break
                emitter.new_line.emit(line.rstrip())

        threading.Thread(target=read_output, daemon=True).start()

    if settings.get("Close Launcher Startup",False):
        window.close()

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

window = QWidget()
window.setWindowTitle("Legacy Launcher")
window.resize(850, 650)
window.setStyleSheet("background-color: rgb(32, 35, 38);")

root = QVBoxLayout()
root.setContentsMargins(0, 0, 0, 0)
root.setSpacing(0)
window.setLayout(root)

# Top Bar
top_bar = QWidget()
top_bar_layout = QHBoxLayout(top_bar)
top_bar.setFixedHeight(50)
top_bar.setStyleSheet("background-color: rgb(27, 30, 32);")

# Add Instance Button
add_instance_button = QPushButton("Add Instance")
add_instance_button.setFixedHeight(40)

add_instance_button.setStyleSheet("""
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
add_instance_button.clicked.connect(open_add_instance_window)

# Settings
settings_button = QPushButton("Settings")
settings_button.setFixedHeight(40)

settings_button.setStyleSheet("""
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
settings_button.clicked.connect(open_settings_window)

top_bar_layout.addWidget(add_instance_button)
top_bar_layout.addWidget(settings_button)
top_bar_layout.addStretch()

root.addWidget(top_bar)

# Main Area
middle = QHBoxLayout()
middle.setContentsMargins(0, 0, 0, 0)
middle.setSpacing(0)
root.addLayout(middle)

content = QWidget()
content.setStyleSheet("background-color: rgb(32, 35, 38);")
scroll = QScrollArea()
scroll.setWidgetResizable(True)

content = QWidget()
content_layout = QGridLayout(content)

scroll.setWidget(content)
middle.addWidget(scroll)

content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
content_layout.setContentsMargins(10, 10, 10, 10)
content_layout.setSpacing(10)
refresh_instance_buttons()

# Sidebar
sidebar = QWidget()
sidebar.setFixedWidth(200)
sidebar.setStyleSheet("background-color: rgb(24, 26, 27);")
sidebar_layout = QVBoxLayout(sidebar)
sidebar_layout.setContentsMargins(0, 0, 0, 0)
sidebar_layout.setSpacing(10)

# Image
img_label = QLabel()
pixmap = QPixmap("Instances/icon.png")
img_label.setPixmap(pixmap)
img_label.setScaledContents(True)
img_label.setMaximumHeight(200)

# Text
text_label = QLabel("Nothing Selected")
rename_box = QLineEdit()
rename_box.setStyleSheet("color: white; font-size: 16px;")
rename_box.setAlignment(Qt.AlignHCenter)
rename_box.hide()
text_label.setStyleSheet("color: white; font-size: 16px;")
text_label.setAlignment(Qt.AlignHCenter)
text_label.mousePressEvent = lambda _: enable_rename()
rename_box.returnPressed.connect(finish_rename)


# Play Button
play_button = QPushButton("Play")
play_button.setFixedHeight(40)

play_button.setStyleSheet("""
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
play_button.clicked.connect(lambda: launch_game(selected_instance))

# Delete Button
delete_button = QPushButton("Delete")
delete_button.setFixedHeight(40)

delete_button.setStyleSheet("""
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
delete_button.clicked.connect(lambda: delete_instance(selected_instance))

# Open Instance Folder
open_instance_folder_button = QPushButton("Open Folder")
open_instance_folder_button.setFixedHeight(40)

open_instance_folder_button.setStyleSheet("""
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
open_instance_folder_button.clicked.connect(lambda: open_instance_folder(selected_instance))

# Edit
edit_button = QPushButton("Edit")
edit_button.setFixedHeight(40)

edit_button.setStyleSheet("""
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
