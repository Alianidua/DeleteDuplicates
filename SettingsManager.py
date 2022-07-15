import os
import tkinter as tk


class SettingsManager:
    def __init__(self):
        # Settings
        self.ROOT_DIR = None
        self.BIN_DIR = None
        self.IMAGE_EXTENSIONS = None
        self.VIDEO_EXTENSIONS = None
        self.PERCENTAGE = None
        self.load_default_settings()

        # Tkinter root
        tk_root = tk.Tk()
        tk_root.wm_title("Duplicates Remover - Settings")
        tk_root.geometry("1000x200")
        self.tk_root = tk_root
        labels_shape = (40, 2)
        entries_width = 90
        buttons_width = 15
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
        self.image_ext_entry.insert(0, self.IMAGE_EXTENSIONS)
        # VIDEO_EXT entry
        self.video_ext_entry = tk.Entry(tk_root, width=entries_width)
        self.video_ext_entry.grid(row=3, column=1)
        tk.Label(
            tk_root,
            text="Videos extensions to consider",
            width=labels_shape[0],
            height=labels_shape[1],
        ).grid(row=3, column=0)
        self.video_ext_entry.insert(0, self.VIDEO_EXTENSIONS)
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
        print(f"Opening tkinter parameters window. ")
        self.tk_root.mainloop()

    @staticmethod
    def delete_window_event():
        print("Settings window closed. Program exiting 2...")
        exit(2)

    def replace_root_dir(self):
        self.root_dir_entry.delete(0, tk.END)
        self.root_dir_entry.insert(0, tk.filedialog.askdirectory())

    def replace_bin_dir(self):
        self.root_dir_entry.delete(0, tk.END)
        self.root_dir_entry.insert(0, tk.filedialog.askdirectory())

    def confirm_event(self):
        # Format values
        ROOT_DIR = self.root_dir_entry.get()
        print(ROOT_DIR)
        while ROOT_DIR[-1] == "\\" or ROOT_DIR[-1] == " ":
            ROOT_DIR = ROOT_DIR[:-1]
        while ROOT_DIR[0] == " ":
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
        PERCENTAGE = float(
            self.percentage_entry.get().strip(" ").strip("\n").strip("\t")
        )
        print(
            f"Final settings loaded :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {IMAGE_EXTENSIONS}\n\tPROGRESSION_FREQUENCY: {PERCENTAGE}\n\tVIDEO_EXTENSIONS: {VIDEO_EXTENSIONS}\n"
        )
        # Logs for BIN_DIR
        if BIN_DIR:
            if not os.path.exists(BIN_DIR) or not os.path.isdir(BIN_DIR):
                print(
                    f"{BIN_DIR} does not exist or is not a directory. Creating BIN_DIR directory..."
                )
                os.mkdir(BIN_DIR)
            elif os.listdir(BIN_DIR):
                print(
                    f"Warning : the following directory already exists and is not empty : {BIN_DIR}. \nYou may overwrite some files."
                )
        else:
            print("No BIN_DIR specified. The duplicates will not be removed.")
        # Set settings values
        self.ROOT_DIR = ROOT_DIR
        self.BIN_DIR = BIN_DIR
        self.IMAGE_EXTENSIONS = IMAGE_EXTENSIONS
        self.VIDEO_EXTENSIONS = VIDEO_EXTENSIONS
        self.PERCENTAGE = PERCENTAGE
        # Close tkinter window
        self.tk_root.destroy()

    def load_default_settings(self):
        with open("./settings.txt", encoding="utf-8") as settings:
            lines = settings.readlines()
        ROOT_DIR = lines[0].split("=")[1]
        while ROOT_DIR[-1] == "\\" or ROOT_DIR[-1] == " " or ROOT_DIR[-1] == "\n":
            ROOT_DIR = ROOT_DIR[:-1]
        while ROOT_DIR[0] == " ":
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
        PERCENTAGE = float(lines[4].split("=")[1].strip(" ").strip("\n").strip("\t"))
        print(
            f"Default settings loaded :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {IMAGE_EXTENSIONS}\n\tPROGRESSION_FREQUENCY: {PERCENTAGE}\n\tVIDEO_EXTENSIONS: {VIDEO_EXTENSIONS}\n"
        )
        self.ROOT_DIR = ROOT_DIR
        self.BIN_DIR = BIN_DIR
        self.IMAGE_EXTENSIONS = IMAGE_EXTENSIONS
        self.VIDEO_EXTENSIONS = VIDEO_EXTENSIONS
        self.PERCENTAGE = PERCENTAGE

    def get_settings(self):
        return (
            self.ROOT_DIR,
            self.BIN_DIR,
            self.IMAGE_EXTENSIONS,
            self.VIDEO_EXTENSIONS,
            self.PERCENTAGE,
        )
