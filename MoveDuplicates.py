import os
import sys
import time
import traceback
import datetime as dt
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
import get_image_size
from Utils import logs
from tkinter import messagebox
from recordclass import recordclass
from SettingsManager import SettingsManager
from DuplicatesMover import DuplicatesMover


# Load settings
ROOT_DIR = None  # The directory where your images are stored
BIN_DIR = None  # The directory where you want to put your duplicated files
IMAGE_EXTENSIONS = None  # The images format
VIDEO_EXTENSIONS = None  # The videos format
PERCENTAGE = 0.05  # How frequently the program should show its progression


# Return a queue with all images in root_dir
images, nb_images, total_images = {}, {}, 0
videos, nb_videos, total_videos = {}, {}, 0


def list_files(directory=ROOT_DIR):
  global images, videos
  D = os.listdir(directory)
  for fpath in D:
    fpath = f"{directory}/{fpath}"
    ext = fpath.split(".")[-1]
    if os.path.isdir(fpath):
      list_files(fpath)
    elif ext in IMAGE_EXTENSIONS:
      try:
        shape = get_image_size.get_image_size(fpath)
        if shape not in images[ext]:
          images[ext][get_image_size.get_image_size(fpath)] = []
        images[ext][get_image_size.get_image_size(fpath)].append(fpath)
      except Exception as e:
        logs(f"{e}\nWARNING : something wrong happened with this file : '{fpath}' ; this file will be ignored")
    elif ext in VIDEO_EXTENSIONS:
      try:
        size = os.stat(fpath).st_size
        if size not in videos[ext]:
          videos[ext][size] = []
        videos[ext][size].append(fpath)
      except Exception as e:
        logs(f"{e}\nWARNING : something wrong happened with this file : '{fpath}' ; this file will be ignored")


# Count number of images per extension and shape
def count_files():
  global nb_images, nb_videos, total_images, total_videos
  logs("  EXT          SHAPE         NB_IMAGES")
  for ext in IMAGE_EXTENSIONS:
    if not images[ext]:
      continue
    logs(f"[ {ext} ]")
    one_or_less = []
    for shape in images[ext]:
      if not images[ext][shape]:
        continue
      count = len(images[ext][shape])
      if count <= 1:
        one_or_less.append(shape)
      else:
        logs(f"\t  {shape}:   \t{count}")
        nb_images[ext][shape] = count
        total_images += count
    for shape in one_or_less:
      images[ext].pop(shape)
  logs("\n  EXT      SIZE      NB_VIDEOS")
  for ext in VIDEO_EXTENSIONS:
    if not videos[ext]:
      continue
    logs(f"[ {ext} ]")
    one_or_less = []
    for size in videos[ext]:
      if not videos[ext][size]:
        continue
      count = len(videos[ext][size])
      if count <= 1:
        one_or_less.append(size)
      else:
        logs(f"\t  {size}:   \t{count}")
        nb_videos[ext][size] = count
        total_videos += count
    for size in one_or_less:
      videos[ext].pop(size)
  logs()
  logs(total_images, "potential duplicated images.")
  logs(total_videos, "potential duplicated videos.\n")

# Compare 2 images dates
def compare_dates(p1, p2):
  old, new = p1, p2
  old_date = round(os.path.getmtime(old))
  new_date = round(os.path.getmtime(new))
  if new_date < old_date:
    old, new = p1, p2
    old_date, new_date = new_date, old_date
  return (
    old,
    new,
    dt.datetime.fromtimestamp(old_date),
    dt.datetime.fromtimestamp(new_date),
  )

# Load image
def load_image_pixels(im_path, draft_shape, listLocations, queue_cache, im_index):
  if not queue_cache[im_index]:
    # Load image for the first time
    im = Image.open(im_path)
    im.draft("RGB", draft_shape)
    pixel_data = im.load()
    queue_cache[im_index] = tuple(
      tuple(
        pixel_data[coordinates] for coordinates in locations
      )
      for locations in listLocations
    )
  return queue_cache[im_index]

# Main loop; iterate on every images
DuplicatesInfo = recordclass(
  "DuplicatesInfo", ["old", "new", "old_date", "new_date", "remove_old", "remove_new"]
)
duplicates = list()

positionsFactors = [0, .25, .5, .75, 1]
def iterate_queue(queue, queue_cache, ext, shape, i, percentage):
  # Compute pixels positions to use for comparison
  draft_shape = (shape[0] // 16, shape[1] // 16)
  listLocations = [
    tuple(
      (int(draft_shape[0] * i), int(draft_shape[1] * j))
      for i in positionsFactors
      for j in positionsFactors
    )
  ]

  im1_index = nb_images[ext][shape] - 1
  while queue:
    # Compute new image values
    im1_path = queue.pop()
    if queue_cache[im1_index]:
      im1_pixels = queue_cache[im1_index][0]
    else:
      im1_pixels = load_image_pixels(
        im1_path, draft_shape, listLocations, queue_cache, im1_index
      )[0]
    # Compare with other images
    for im2_index in range(im1_index):
      im2_path = queue[im2_index]
      if im1_pixels in load_image_pixels(
        im2_path, draft_shape, listLocations, queue_cache, im2_index
      ):
        old, new, old_date, new_date = compare_dates(im1_path, im2_path)
        duplicates.append(
          DuplicatesInfo(
            old=old,
            new=new,
            old_date=old_date,
            new_date=new_date,
            remove_old=False,
            remove_new=True,
          )
        )
        logs("Duplicates :", im1_path, im2_path)
        break
    # Iterate
    im1_index -= 1
    i += 1
    if i / total_images > percentage:
      logs(round(100 * percentage), "%")
      percentage += PERCENTAGE
  return i, percentage


def iterate_paths():
  logs("Iterating over all images...")
  i = 0
  percentage = 0
  for ext in images:
    for shape in images[ext]:
      queue = images[ext][shape]
      queue_cache = [None for _ in queue]
      i, percentage = iterate_queue(queue, queue_cache, ext, shape, i, percentage)
  logs("100 %. Done.")
  logs("Iterating over videos...")
  for ext in videos:
    for size in videos[ext]:
      n = nb_videos[ext][size]
      for i in range(n - 1):
        v1 = videos[ext][size][i]
        for j in range(i + 1, n):
          v2 = videos[ext][size][j]
          old, new, old_date, new_date = compare_dates(v1, v2)
          duplicates.append(
            DuplicatesInfo(
              old=old,
              new=new,
              old_date=old_date,
              new_date=new_date,
              remove_old=False,
              remove_new=True,
            )
          )
  logs("100 %. Done.")


if __name__ == "__main__":

  try:
    while True:
      # Clear variables
      total_images = 0
      total_videos = 0
      duplicates = list()
      # Load settings
      settings_manager = SettingsManager()
      (
        ROOT_DIR,
        BIN_DIR,
        IMAGE_EXTENSIONS,
        VIDEO_EXTENSIONS,
        PERCENTAGE,
      ) = settings_manager.get_settings()
      # List files
      images = {ext: {} for ext in IMAGE_EXTENSIONS}
      nb_images = {ext: {} for ext in IMAGE_EXTENSIONS}
      videos = {ext: {} for ext in VIDEO_EXTENSIONS}
      nb_videos = {ext: {} for ext in VIDEO_EXTENSIONS}
      logs("Listing images and videos...")
      t_start = time.time()
      list_files(directory=ROOT_DIR)
      # Count files
      count_files()
      # Start duplicates detection
      iterate_paths()
      logs(f"Computing time : {round(time.time() - t_start, 2)} seconds.")
      # Show and move images
      if duplicates:
        duplicates_mover = DuplicatesMover(
          ROOT_DIR, BIN_DIR, VIDEO_EXTENSIONS, duplicates
        )
        duplicates_mover.window_loop()
      else:
        logs("No duplicate found. Back to settings.")
  except Exception as e:
    error_traceback = traceback.format_exc()
    logs(error_traceback)
    messagebox.showerror(
      "Something went wrong :( check the logs or message me", error_traceback
    )
    logs("Something went wrong :( check the logs or message me.")
    logs("Press enter twice to close terminal.")
    input()
    sys.exit(1)
