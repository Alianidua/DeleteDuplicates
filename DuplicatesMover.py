import os
from PIL import Image
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DuplicatesMover:
    """Display duplicates, wait for user confirmation to move the newest duplicate in BIN_DIR"""

    def __init__(self, ROOT_DIR, BIN_DIR, duplicates):

        self.ROOT_DIR = ROOT_DIR
        self.BIN_DIR = BIN_DIR
        self.duplicates = duplicates
        self.duplicates_len = len(duplicates)
        self.root_dir_len = len(ROOT_DIR) + 1
        self.i = 0

        # Configure tkinter root
        tk_root = tk.Tk()
        self.tk_root = tk_root
        tk_root.wm_title("Duplicated images - check the images you want to remove")
        tk_root.geometry('1200x900')
        # Handle window closure
        tk_root.wm_protocol("WM_DELETE_WINDOW", func=DuplicatesMover.delete_window_event)
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
        check_button = tk.Checkbutton(
            buttons_frame,
            text="Remove newest image",
            variable=self.remove,
            onvalue=True,
            offvalue=False,
            command=self.check_image_event
        )
        check_button.pack(side=tk.TOP)
        check_button["font"] = small_font
        # Button previous
        button_prev = tk.Button(buttons_frame, text="Prev", width=6, bg="#A9A9A9", command=self.prev_event)
        button_prev.pack(side=tk.LEFT)
        button_prev["font"] = font
        # Button next
        button_next = tk.Button(buttons_frame, text="Next", width=6, bg="#A9A9A9", command=self.next_event)
        button_next.pack()
        button_next["font"] = font
        # Button confirm
        button_confirm = tk.Button(bottom_frame, text="Confirm", bg="red", command=self.confirm_event)
        button_confirm.pack(side=tk.RIGHT)
        button_confirm["font"] = font
        # Images to display
        self.fig_canvas = None

    @staticmethod
    def delete_window_event():
        print("Window closed. Program exiting 2...")
        exit(2)

    def display_new_images(self):
        files = self.duplicates[self.i]
        # Compare creation dates
        old, new, old_date, new_date, remove = files.old, files.new, files.old_date, files.new_date, files.remove
        # Update check button value
        self.remove.set(remove)
        # Plt figure
        fig, ax = plt.subplots(1, 2)
        fig.set_size_inches(15, 15)
        plt.suptitle(f"Image {self.i + 1}/{self.duplicates_len}", y=0.9)
        ax[0].imshow(Image.open(old))
        ax[0].set_title(f"Oldest image\n{old[self.root_dir_len:]}\n{old_date}", fontsize=10)
        ax[1].imshow(Image.open(new))
        ax[1].set_title(f"Newest image\n{new[self.root_dir_len:]}\n{new_date}", fontsize=10)
        # Tkinter
        if self.fig_canvas:
            self.fig_canvas.get_tk_widget().destroy()
            plt.close('all')
        self.fig_canvas = FigureCanvasTkAgg(fig, master=self.tk_root)
        self.fig_canvas.get_tk_widget().pack(side=tk.TOP)

    def check_image_event(self):
        self.duplicates[self.i].remove = self.remove.get()

    def prev_event(self):
        self.i -= 1
        if self.i < 0:
            self.i = self.duplicates_len - 1
        self.display_new_images()

    def next_event(self):
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
            print(f"Moving them to bin folder: {self.BIN_DIR} ...")
            for duplicate_path in to_remove:
                if os.path.exists(duplicate_path):
                    os.rename(duplicate_path, f"{self.BIN_DIR}/{duplicate_path.split('/')[-1]}")
        else:
            print("No BIN_DIR defined. Duplicates will not be moved.")

    def window_loop(self):
        # Start tkinter loop
        print(f"Detected {self.duplicates_len} duplicated files. ")
        self.display_new_images()
        self.tk_root.mainloop()
        # Move images
        self.move_images()
