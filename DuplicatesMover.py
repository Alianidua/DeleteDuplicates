import os
import sys
import cv2 as cv
import tkinter as tk
from PIL import Image
from Utils import logs
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

bPx, wPx = (0, 0, 0), (255, 255, 255)
mediaCouldNotBeLoaded = (
  tuple(wPx for _ in range(20)),
  (wPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx),
  (wPx, bPx, wPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx),
  (wPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, bPx, bPx, wPx),
  (wPx, bPx, wPx, wPx, bPx, bPx, wPx, wPx, bPx, bPx, wPx, wPx, bPx, wPx, bPx, wPx, bPx, bPx, wPx, wPx),
  (wPx, bPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, wPx, bPx, bPx, bPx, wPx, bPx, wPx, bPx, wPx),
  tuple(wPx for _ in range(20))
)

class DuplicatesMover:
  """Display duplicates, user may choose to move the more recent file/the older one/none/both into BIN_DIR"""

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
    # Button
    self.confirm = False
    self.button_confirm = tk.Button(
      bottom_frame, text="Confirm", bg="red", command=self.confirm_event
    )
    self.button_confirm.pack(side=tk.RIGHT, padx=100)
    self.button_confirm["font"] = font
    # Images to display
    self.ax, self.fig = None, None
    self.ax_old, self.ax_new = None, None

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
    self.load_images(old, new, old_date, new_date)
    # Tkinter
    fig_canvas = FigureCanvasTkAgg(self.fig, master=self.tk_root)
    fig_canvas.get_tk_widget().pack(side=tk.TOP)

  @staticmethod
  def delete_window_event():
    logs("Window closed ; program exiting 0")
    sys.exit(2)
  
  def load_images(self, old, new, old_date, new_date):
    oldOpened, newOpened = False, False
    old_image, new_image = mediaCouldNotBeLoaded, mediaCouldNotBeLoaded
    if old.split(".")[-1] in self.VIDEOS_EXT:
      old_title = f"Oldest video\n{old[self.root_dir_len:]}\n{old_date}"
      new_title = f"Newest video\n{new[self.root_dir_len:]}\n{new_date}"
      videos = (cv.VideoCapture(old), cv.VideoCapture(new))
      try:
        old_image = cv.cvtColor(videos[0].read()[1], cv.COLOR_BGR2RGB)
      except Exception as e:
        logs(e)
        logs(f"Failed to load {old}")
      try:
        new_image = cv.cvtColor(videos[1].read()[1], cv.COLOR_BGR2RGB)
      except Exception as e:
        logs(e)
        logs(f"Failed to load {new}")
      videos[0].release(), videos[1].release()
    else:
      old_title = f"Oldest image\n{old[self.root_dir_len:]}\n{old_date}"
      new_title = f"Newest image\n{new[self.root_dir_len:]}\n{new_date}"
      try:
        old_image = Image.open(old)
        oldOpened = True
        old_image.draft("RGB", (old_image.size[0] // 64, old_image.size[1] // 64))
      except Exception as e:
        logs(e)
        logs(f"Failed to load {old}")
      try:
        new_image = Image.open(new)
        newOpened = True
        new_image.draft("RGB", (new_image.size[0] // 64, new_image.size[1] // 64))
      except Exception as e:
        logs(e)
        logs(f"Failed to load {new}")
    # Update plots
    self.ax_old = self.ax[0].imshow(old_image)
    self.ax_new = self.ax[1].imshow(new_image)
    self.ax[0].set_title(old_title, fontsize=10)
    self.ax[1].set_title(new_title, fontsize=10)
    plt.suptitle(f"Duplicates {self.i + 1}/{self.duplicates_len}", y=0.9)
    # Close Pillow images
    if oldOpened:
      old_image.close()
    if newOpened:
      new_image.close()

  def display_new_images(self):
    files = self.duplicates[self.i]
    # Compare creation dates
    old, new, old_date, new_date, remove_old, remove_new = (
      files.old,
      files.new,
      files.old_date,
      files.new_date,
      files.remove_old,
      files.remove_new,
    )
    # Update buttons value
    self.remove_old.set(remove_old)
    self.remove_new.set(remove_new)
    if self.confirm:
      self.confirm = False
      self.button_confirm.configure(bg="red")
    # Load images
    self.load_images(old, new, old_date, new_date)
    # Flush
    self.fig.canvas.draw()
    self.fig.canvas.flush_events()

  def check_old_image_event(self):
    self.duplicates[self.i].remove_old = self.remove_old.get()

  def check_new_image_event(self):
    self.duplicates[self.i].remove_new = self.remove_new.get()

  def check_old_image_keybind_event(self, event):
    self.remove_old.set(not self.remove_old.get())
    self.duplicates[self.i].remove_old = self.remove_old.get()

  def check_new_image_keybind_event(self, event):
    self.remove_new.set(not self.remove_new.get())
    self.duplicates[self.i].remove_new = self.remove_new.get()

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
    if self.confirm:
      self.tk_root.destroy()
      self.tk_root.quit()
    else:
      self.confirm = True
      self.button_confirm.configure(bg="lime green")

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
      logs("No BIN_DIR defined ; duplicates will not be moved")

  def window_loop(self):
    # Start tkinter loop
    logs(f"Detected {self.duplicates_len} potentially duplicated files. ")
    self.tk_root.mainloop()
    # Move images
    self.move_images()
