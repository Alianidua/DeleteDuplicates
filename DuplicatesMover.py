import os
from cv2 import VideoCapture
import numpy as np
import tkinter as tk
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DuplicatesMover:
    """Display duplicates, wait for user confirmation to move the newest duplicate in BIN_DIR"""

    def __init__(self, ROOT_DIR, BIN_DIR, VIDEOS_EXT, duplicates):

        self.ROOT_DIR = ROOT_DIR
        self.BIN_DIR = BIN_DIR
        self.VIDEOS_EXT = VIDEOS_EXT
        self.duplicates = duplicates
        self.duplicates_len = len(duplicates)
        self.root_dir_len = len(ROOT_DIR) + 1
        self.i = 0

        # Configure tkinter root
        tk_root = tk.Tk()
        self.tk_root = tk_root
        tk_root.wm_title("Duplicated images - check the images you want to remove")
        # Handle window closure
        tk_root.wm_protocol(
            "WM_DELETE_WINDOW", func=DuplicatesMover.delete_window_event
        )
        # Fonts
        small_font = tk.font.Font(size=15)
        font = tk.font.Font(size=20)
        # Buttons frame
        bottom_frame = tk.Frame(tk_root)
        bottom_frame.pack(side=tk.BOTTOM, pady=20)
        buttons_frame = tk.Frame(bottom_frame)
        buttons_frame.pack(side=tk.LEFT)
        # Check button
        self.remove = tk.BooleanVar()
        self.remove.set(True)
        check_button = tk.Checkbutton(
            buttons_frame,
            text="Remove image",
            variable=self.remove,
            onvalue=True,
            offvalue=False,
            command=self.check_image_event,
        )
        check_button.pack(side=tk.TOP)
        check_button["font"] = small_font
        tk_root.bind("<KeyPress-space>", self.check_image_keybind_event)
        # Button previous
        button_prev = tk.Button(
            buttons_frame, text="Prev", width=6, bg="#DCDCDC", command=self.prev_event
        )
        button_prev.pack(side=tk.LEFT)
        button_prev["font"] = font
        tk_root.bind("<Left>", self.prev_event)
        # Button next
        button_next = tk.Button(
            buttons_frame, text="Next", width=6, bg="#DCDCDC", command=self.next_event
        )
        button_next.pack()
        button_next["font"] = font
        tk_root.bind("<Right>", self.next_event)
        # Button confirm
        button_confirm = tk.Button(
            bottom_frame, text="Confirm", bg="red", command=self.confirm_event
        )
        button_confirm.pack(side=tk.RIGHT)
        button_confirm["font"] = font
        # Images to display
        self.ax, self.fig = None, None
        self.ax_old, self.ax_new = None, None
        self.plt_cache = [None for _ in range(self.duplicates_len)]

        # First display
        files = self.duplicates[self.i]
        # Compare creation dates
        old, new, old_date, new_date = (
            files.old,
            files.new,
            files.old_date,
            files.new_date,
        )
        # Plt figure
        self.fig, self.ax = plt.subplots(1, 2)
        self.fig.set_size_inches(15, 15)
        title = f"Duplicates {self.i + 1}/{self.duplicates_len}"
        if old.split(".")[-1] in self.VIDEOS_EXT:
            videos = (VideoCapture(old), VideoCapture(new))
            _, old_image = videos[0].read()
            _, new_image = videos[1].read()
            old_title = f"Oldest video\n{old[self.root_dir_len:]}\n{old_date}"
            new_title = f"Newest video\n{new[self.root_dir_len:]}\n{new_date}"
            videos[0].release(), videos[1].release()
        else:
            old_image = Image.open(old)
            new_image = Image.open(new)
            old_title = f"Oldest image\n{old[self.root_dir_len:]}\n{old_date}"
            new_title = f"Newest image\n{new[self.root_dir_len:]}\n{new_date}"
        self.plt_cache[self.i] = (np.asarray(old_image), np.asarray(new_image), old_title, new_title, title)
        # Update plot
        self.ax_old = self.ax[0].imshow(self.plt_cache[self.i][0])
        self.ax_new = self.ax[1].imshow(self.plt_cache[self.i][1])
        self.ax[0].set_title(self.plt_cache[self.i][2], fontsize=10)
        self.ax[1].set_title(self.plt_cache[self.i][3], fontsize=10)
        plt.suptitle(self.plt_cache[self.i][4], y=0.9)
        # Tkinter
        fig_canvas = FigureCanvasTkAgg(self.fig, master=self.tk_root)
        fig_canvas.get_tk_widget().pack(side=tk.TOP)

    @staticmethod
    def delete_window_event():
        print("Window closed. Program exiting 2...")
        exit(2)

    def display_new_images(self):
        files = self.duplicates[self.i]
        # Compare creation dates
        old, new, old_date, new_date, remove = (
            files.old,
            files.new,
            files.old_date,
            files.new_date,
            files.remove,
        )
        # Update check button value
        self.remove.set(remove)
        # Load images
        if not self.plt_cache[self.i]:  # First time showing these duplicates
            title = f"Duplicates {self.i + 1}/{self.duplicates_len}"
            if old.split(".")[-1] in self.VIDEOS_EXT:   # Show first frame of videos for first time
                videos = (VideoCapture(old), VideoCapture(new))
                _, old_image = videos[0].read()
                _, new_image = videos[1].read()
                old_title = f"Oldest video\n{old[self.root_dir_len:]}\n{old_date}"
                new_title = f"Newest video\n{new[self.root_dir_len:]}\n{new_date}"
                videos[0].release(), videos[1].release()
            else:   # Show images for first time
                old_image = Image.open(old)
                new_image = Image.open(new)
                old_title = f"Oldest image\n{old[self.root_dir_len:]}\n{old_date}"
                new_title = f"Newest image\n{new[self.root_dir_len:]}\n{new_date}"
            self.plt_cache[self.i] = (np.asarray(old_image), np.asarray(new_image), old_title, new_title, title)
        # Update plot
        self.ax_old.set_data(self.plt_cache[self.i][0])
        self.ax_new.set_data(self.plt_cache[self.i][1])
        self.ax[0].set_title(self.plt_cache[self.i][2], fontsize=10)
        self.ax[1].set_title(self.plt_cache[self.i][3], fontsize=10)
        plt.suptitle(self.plt_cache[self.i][4], y=0.9)
        # Flush
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def check_image_event(self):
        self.duplicates[self.i].remove = self.remove.get()

    def check_image_keybind_event(self, event):
        self.remove.set(not self.remove.get())
        self.duplicates[self.i].remove = self.remove.get()

    def prev_event(self, *args):
        self.i -= 1
        if self.i < 0:
            self.i = self.duplicates_len - 1
        self.display_new_images()

    def next_event(self, *args):
        self.i += 1
        if self.i >= self.duplicates_len:
            self.i = 0
        self.display_new_images()

    def confirm_event(self):
        self.tk_root.destroy()
        self.tk_root.quit()

    def move_images(self):
        to_remove = tuple(files.new for files in self.duplicates if files.remove)
        print(f"Registered {len(to_remove)} files to move.")
        if self.BIN_DIR:
            print(f"Moving them to bin folder: {self.BIN_DIR}")
            for duplicate_path in to_remove:
                if os.path.exists(duplicate_path):
                    os.rename(
                        duplicate_path,
                        f"{self.BIN_DIR}/{duplicate_path.split('/')[-1]}",
                    )
        else:
            print("No BIN_DIR defined. Duplicates will not be moved.")

    def window_loop(self):
        # Start tkinter loop
        print(f"Detected {self.duplicates_len} duplicated files. ")
        self.tk_root.mainloop()
        # Move images
        self.move_images()
