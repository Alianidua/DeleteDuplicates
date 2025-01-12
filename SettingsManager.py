import os
import sys
import tkinter as tk
from Utils import logs


class SettingsManager:
  def __init__(self):
    # Settings
    self.ROOT_DIR = ""
    self.BIN_DIR = ""
    self.IMAGE_EXTENSIONS = ""
    self.VIDEO_EXTENSIONS = ""
    self.PERCENTAGE = 0.1
    self.settings = "./settings.txt"
    self.load_default_settings()

    # Tkinter root
    tk_root = tk.Tk()
    tk_root.wm_title("Duplicates Remover - Settings")
    tk_root.geometry("1000x200")
    self.tk_root = tk_root
    labels_shape = (35, 2)
    entries_width = 70
    buttons_width = 10
    # Handle window closure
    tk_root.wm_protocol(
      "WM_DELETE_WINDOW", func=SettingsManager.delete_window_event
    )
    # ROOT_DIR entry
    self.root_dir_entry = tk.Entry(tk_root, width=entries_width)
    self.root_dir_entry.grid(row=0, column=1, padx=20)
    tk.Label(
      tk_root,
      text="Directory of your images/videos",
      width=labels_shape[0],
      height=labels_shape[1],
    ).grid(row=0, column=0)
    root_dir_button = tk.Button(
      tk_root,
      text="Browse...",
      width=buttons_width,
      command=self.replace_root_dir,
      bg="#DCDCDC",
    )
    root_dir_button.grid(row=0, column=2)
    self.root_dir_entry.insert(0, self.ROOT_DIR)
    # BIN_DIR entry
    self.bin_dir_entry = tk.Entry(tk_root, width=entries_width)
    self.bin_dir_entry.grid(row=1, column=1, padx=20)
    tk.Label(
      tk_root,
      text="Target directory for duplicates",
      width=labels_shape[0],
      height=labels_shape[1],
    ).grid(row=1, column=0)
    bin_dir_button = tk.Button(
      tk_root,
      text="Browse...",
      width=buttons_width,
      command=self.replace_bin_dir,
      bg="#DCDCDC",
    )
    bin_dir_button.grid(row=1, column=2)
    self.bin_dir_entry.insert(0, self.BIN_DIR)
    # IMAGE_EXT entry
    self.image_ext_entry = tk.Entry(tk_root, width=entries_width)
    self.image_ext_entry.grid(row=2, column=1)
    tk.Label(
      tk_root,
      text="Images extensions to consider",
      width=labels_shape[0],
      height=labels_shape[1],
    ).grid(row=2, column=0)
    self.image_ext_entry.insert(0, ",".join(self.IMAGE_EXTENSIONS))
    # VIDEO_EXT entry
    self.video_ext_entry = tk.Entry(tk_root, width=entries_width)
    self.video_ext_entry.grid(row=3, column=1)
    tk.Label(
      tk_root,
      text="Videos extensions to consider",
      width=labels_shape[0],
      height=labels_shape[1],
    ).grid(row=3, column=0)
    self.video_ext_entry.insert(0, ",".join(self.VIDEO_EXTENSIONS))
    # PERCENTAGE entry
    self.percentage_entry = tk.Entry(tk_root, width=entries_width)
    self.percentage_entry.grid(row=4, column=1)
    tk.Label(
      tk_root,
      text="Progression display frequency (in terminal)",
      width=labels_shape[0],
      height=labels_shape[1],
    ).grid(row=4, column=0)
    self.percentage_entry.insert(0, self.PERCENTAGE)
    # Set current as default button
    confirm_button = tk.Button(
      tk_root,
      width=buttons_width,
      text="Set as default",
      command=self.set_default_event,
      bg="#A9A9A9",
    )
    confirm_button.grid(row=3, column=2)
    # Confirm button
    confirm_button = tk.Button(
      tk_root,
      width=buttons_width,
      text="Confirm",
      command=self.confirm_event,
      bg="#A9A9A9",
    )
    confirm_button.grid(row=4, column=2)
    # Start tkinter loop
    logs(f"Opening tkinter parameters window.", level="INFO")
    self.tk_root.mainloop()

  @staticmethod
  def delete_window_event():
    logs("Settings window closed; program exiting 0", level="OK")
    sys.exit(0)

  def replace_root_dir(self):
    new_dir = tk.filedialog.askdirectory()
    if new_dir:
      self.root_dir_entry.delete(0, tk.END)
      self.root_dir_entry.insert(0, new_dir)

  def replace_bin_dir(self):
    new_dir = tk.filedialog.askdirectory()
    if new_dir:
      self.bin_dir_entry.delete(0, tk.END)
      self.bin_dir_entry.insert(0, new_dir)

  def confirm_event(self, destroy=True):
    # Format values
    ROOT_DIR = self.root_dir_entry.get()
    while ROOT_DIR and (ROOT_DIR[-1] == "\\" or ROOT_DIR[-1] == " "):
      ROOT_DIR = ROOT_DIR[:-1]
    while ROOT_DIR and ROOT_DIR[0] == " ":
      ROOT_DIR = ROOT_DIR[1:]
    BIN_DIR = self.bin_dir_entry.get()
    while BIN_DIR and (BIN_DIR[-1] == "\\" or BIN_DIR[-1] == " "):
      BIN_DIR = BIN_DIR[:-1]
    while BIN_DIR and BIN_DIR[0] == " ":
      BIN_DIR = BIN_DIR[1:]
    IMAGE_EXTENSIONS = (
      self.image_ext_entry.get().strip(" ").strip("\n").strip("\t").split(",")
    )
    VIDEO_EXTENSIONS = (
      self.video_ext_entry.get().strip(" ").strip("\n").strip("\t").split(",")
    )
    PERCENTAGE = self.percentage_entry.get().strip(" ").strip("\n").strip("\t")
    if not PERCENTAGE:
      PERCENTAGE = 0.01
    else:
      PERCENTAGE = float(PERCENTAGE)
    # Logs for BIN_DIR
    if BIN_DIR:
      if not os.path.exists(BIN_DIR) or not os.path.isdir(BIN_DIR):
        logs(
          f"{BIN_DIR} does not exist or is not a directory. It will be created when you close the window.",
          level="WARN"
        )
      elif os.listdir(BIN_DIR):
        logs(
          f"The following directory already exists and is not empty : '{BIN_DIR}'\nSome files in this directory may be overwritten",
          level="WARN"
        )
    else:
      logs("No BIN_DIR specified; the duplicates will not be removed", level="WARN")
    # Set settings values
    self.ROOT_DIR = ROOT_DIR
    self.BIN_DIR = BIN_DIR
    self.IMAGE_EXTENSIONS = IMAGE_EXTENSIONS
    self.VIDEO_EXTENSIONS = VIDEO_EXTENSIONS
    self.PERCENTAGE = PERCENTAGE
    # Close tkinter window
    if destroy:
      self.tk_root.destroy()
      self.tk_root.quit()
      logs(
        f"Final settings loaded :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {IMAGE_EXTENSIONS}\n\tPROGRESSION_FREQUENCY: {PERCENTAGE}\n\tVIDEO_EXTENSIONS: {VIDEO_EXTENSIONS}\n",
        level="OK"
      )
      if not os.path.exists(BIN_DIR) or not os.path.isdir(BIN_DIR):
        logs(
          f"{BIN_DIR} does not exist or is not a directory. Creating BIN_DIR directory...",
          level="INFO"
        )
        os.mkdir(BIN_DIR)
    else:
      logs(
        f"Settings loaded and written as default in {self.settings} :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {IMAGE_EXTENSIONS}\n\tPROGRESSION_FREQUENCY: {PERCENTAGE}\n\tVIDEO_EXTENSIONS: {VIDEO_EXTENSIONS}\n",
        level="OK"
      )

  def set_default_event(self):
    self.confirm_event(destroy=False)
    if os.path.exists(self.settings):
      os.remove(self.settings)
    with open(self.settings, "w", encoding="utf-8") as settings:
      settings.write("ROOT_DIRECTORY=" + self.ROOT_DIR + "\n")
      settings.write("BIN_DIRECTORY=" + self.BIN_DIR + "\n")
      settings.write("IMAGE_FORMATS=" + ",".join(self.IMAGE_EXTENSIONS) + "\n")
      settings.write("VIDEO_FORMATS=" + ",".join(self.VIDEO_EXTENSIONS) + "\n")
      settings.write("PROGRESSION_FREQUENCY=" + str(self.PERCENTAGE))

  def load_default_settings(self):
    if not os.path.exists(self.settings):
      logs("No default settings", level="INFO")
      return
    try:
      with open(self.settings, encoding="utf-8") as settings:
        lines = settings.readlines()
      ROOT_DIR = lines[0].split("=")[1]
      while ROOT_DIR and (
        ROOT_DIR[-1] == "\\" or ROOT_DIR[-1] == " " or ROOT_DIR[-1] == "\n"
      ):
        ROOT_DIR = ROOT_DIR[:-1]
      while ROOT_DIR and ROOT_DIR[0] == " ":
        ROOT_DIR = ROOT_DIR[1:]
      BIN_DIR = lines[1].split("=")[1]
      while BIN_DIR and (
        BIN_DIR[-1] == "\\" or BIN_DIR[-1] == " " or BIN_DIR[-1] == "\n"
      ):
        BIN_DIR = BIN_DIR[:-1]
      while BIN_DIR and BIN_DIR[0] == " ":
        BIN_DIR = BIN_DIR[1:]
      IMAGE_EXTENSIONS = (
        lines[2].split("=")[1].strip(" ").strip("\n").strip("\t").split(",")
      )
      VIDEO_EXTENSIONS = (
        lines[3].split("=")[1].strip(" ").strip("\n").strip("\t").split(",")
      )
      PERCENTAGE = lines[4].split("=")[1].strip(" ").strip("\n").strip("\t")
      if not PERCENTAGE:
        PERCENTAGE = 0.01
      else:
        PERCENTAGE = float(PERCENTAGE)
      logs(
        f"Default settings loaded :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {IMAGE_EXTENSIONS}\n\tPROGRESSION_FREQUENCY: {PERCENTAGE}\n\tVIDEO_EXTENSIONS: {VIDEO_EXTENSIONS}\n",
        level = "INFO"
      )
      self.ROOT_DIR = ROOT_DIR
      self.BIN_DIR = BIN_DIR
      self.IMAGE_EXTENSIONS = IMAGE_EXTENSIONS
      self.VIDEO_EXTENSIONS = VIDEO_EXTENSIONS
      self.PERCENTAGE = PERCENTAGE
    except Exception as e:
      logs("Error while parsing default settings. Continuing", level="ERROR")

  def get_settings(self):
    return self.ROOT_DIR, self.BIN_DIR, self.IMAGE_EXTENSIONS, self.VIDEO_EXTENSIONS, self.PERCENTAGE,
