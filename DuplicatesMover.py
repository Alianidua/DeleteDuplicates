import os
import sys
import numpy as np
import tkinter as tk
from ImageLoader import ImageLoader, bPx, wPx
from Utils import logs
import multiprocessing
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


mediaLoading = np.asarray((
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  (wPx, bPx, wPx, wPx, bPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, bPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx),
  (wPx, bPx, wPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx),
  (wPx, bPx, wPx, wPx, bPx, wPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, wPx, bPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx),
  (wPx, bPx, wPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx, wPx),
  (wPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, bPx, wPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, wPx),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23)),
  tuple(wPx for _ in range(23))
))

class DuplicatesMover:
  """Display duplicates, user may choose to move the more recent file/the older one/none/both into BIN_DIR"""

  def __init__(self, ROOT_DIR, BIN_DIR, VIDEO_EXT, duplicates):
    self.ROOT_DIR = ROOT_DIR
    self.BIN_DIR = BIN_DIR
    self.VIDEO_EXT = VIDEO_EXT
    self.duplicates = duplicates
    self.duplicates_len = len(duplicates)
    self.root_dir_len = len(ROOT_DIR) + 1
    self.i = multiprocessing.Value('i', 0)
    self.current_showed_i = -1

    # Start subprocess that images
    self.image_dict = multiprocessing.Manager().dict()
    self.p = multiprocessing.Process(
      target=ImageLoader,
      args=(VIDEO_EXT, ROOT_DIR, duplicates, self.image_dict, self.i)
    )
    self.p.daemon = True
    self.p.start()

    # Configure tkinter root
    tk_root = tk.Tk()
    self.tk_root = tk_root
    tk_root.wm_title("Duplicated images - check the images you want to remove")
    tk_root.geometry("1500x800")
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
    # Check button old
    self.remove_old = tk.BooleanVar()
    self.remove_old.set(False)
    check_button_old = tk.Checkbutton(
      buttons_frame,
      text="Remove left image",
      variable=self.remove_old,
      onvalue=True,
      offvalue=False,
      command=self.check_old_image_event,
    )
    check_button_old.pack(side=tk.TOP)
    check_button_old["font"] = small_font
    # Check button new
    self.remove_new = tk.BooleanVar()
    self.remove_new.set(True)
    check_button_new = tk.Checkbutton(
      buttons_frame,
      text="Remove right image",
      variable=self.remove_new,
      onvalue=True,
      offvalue=False,
      command=self.check_new_image_event,
    )
    check_button_new.pack(side=tk.TOP)
    check_button_new["font"] = small_font
    tk_root.bind("<KeyPress-space>", self.check_new_image_keybind_event)
    # Button previous
    button_prev = tk.Button(
      buttons_frame, text="Prev", width=6, bg="#DCDCDC", command=lambda:self.move_event(-1)
    )
    button_prev.pack(side=tk.LEFT)
    button_prev["font"] = font
    tk_root.bind("<Left>", lambda event: self.move_event(-1))
    # Button next
    button_next = tk.Button(
      buttons_frame, text="Next", width=6, bg="#DCDCDC", command=lambda:self.move_event(1)
    )
    button_next.pack()
    button_next["font"] = font
    tk_root.bind("<Right>", lambda event: self.move_event(1))
    # Button
    self.confirm = False
    self.button_confirm = tk.Button(
      bottom_frame, text="Confirm", bg="red", command=self.confirm_event
    )
    self.button_confirm.pack(side=tk.RIGHT, padx=100)
    self.button_confirm["font"] = font

    # Plt figure
    self.fig, self.ax = plt.subplots(1, 2)
    self.fig.set_size_inches(15, 15)
    self.old_image = self.ax[0].imshow(mediaLoading, animated=True)
    self.new_image = self.ax[1].imshow(mediaLoading, animated=True)

    # Tkinter
    fig_canvas = FigureCanvasTkAgg(self.fig, master=self.tk_root)
    fig_canvas.get_tk_widget().pack(side=tk.TOP)

    # Start checks for images
    self.check_for_images()

  def check_for_images(self):
    # Check if current image have been loaded by the background process
    if self.current_showed_i != self.i.value:
      for image_i in self.image_dict.keys():
        if image_i != self.i.value:
          continue
        old_image, old_title, new_image, new_title = self.image_dict[image_i]
        self.current_showed_i = self.i.value
        # Update plots
        self.old_image.set_data(old_image)
        self.new_image.set_data(new_image)
        self.ax[0].set_title(old_title, fontsize=10)
        self.ax[1].set_title(new_title, fontsize=10)
        plt.suptitle(f"Duplicates {self.i.value + 1}/{self.duplicates_len}", y=0.9)
        # Flush
        plt.draw()
    # Schedule the next check
    self.tk_root.after(100, self.check_for_images)

  def check_old_image_event(self):
    self.duplicates[self.i.value].remove_old = self.remove_old.get()

  def check_new_image_event(self):
    self.duplicates[self.i.value].remove_new = self.remove_new.get()

  def check_old_image_keybind_event(self, event):
    self.remove_old.set(not self.remove_old.get())
    self.duplicates[self.i.value].remove_old = self.remove_old.get()

  def check_new_image_keybind_event(self, event):
    self.remove_new.set(not self.remove_new.get())
    self.duplicates[self.i.value].remove_new = self.remove_new.get()

  def move_event(self, i):
    with self.i.get_lock():  # Ensure safe access to the shared value
      self.i.value = (self.i.value + i) % self.duplicates_len
    self.remove_old.set(self.duplicates[self.i.value][4])
    self.remove_new.set(self.duplicates[self.i.value][5])
    if self.confirm:
      self.confirm = False
      self.button_confirm.configure(bg="red")

  def confirm_event(self):
    if self.confirm:
      self.tk_root.destroy()
      self.tk_root.quit()
    else:
      self.confirm = True
      self.button_confirm.configure(bg="lime green")

  @staticmethod
  def delete_window_event():
    logs("Window closed; program exiting 0")
    sys.exit(0)

  def move_images(self):
    to_remove = [files.new for files in self.duplicates if files.remove_new] + [
      files.old for files in self.duplicates if files.remove_old
    ]
    logs(f"Registered {len(to_remove)} files to move")
    if self.BIN_DIR:
      logs(f"Moving them to bin folder: {self.BIN_DIR}")
      for duplicate_path in to_remove:
        if os.path.exists(duplicate_path):
          target_path = f"{self.BIN_DIR}/{duplicate_path.split('/')[-1]}"
          if os.path.exists(target_path):
            logs(
              "Warning:",
              target_path,
              "already exists and will be erased.",
            )
            os.remove(target_path)
          os.rename(duplicate_path, target_path)
    else:
      logs("No BIN_DIR defined; duplicates will not be moved")

  def window_loop(self):
    # Start tkinter loop
    logs(f"Detected {self.duplicates_len} potentially duplicated files. ")
    self.tk_root.mainloop()
    # Move images
    self.move_images()
