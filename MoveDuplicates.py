import os
import sys
import time
import traceback
import numpy as np
import datetime as dt
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import get_image_size
import multiprocessing
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
def list_files(directory=ROOT_DIR):
  global images, videos
  D = os.listdir(directory)
  for fpath in D:
    ext = fpath.split(".")[-1]
    fpath = f"{directory}/{fpath}"
    if os.path.isdir(fpath):
      list_files(fpath)
    elif ext in IMAGE_EXTENSIONS:
      try:
        shape = get_image_size.get_image_size(fpath)
        if shape not in images[ext]:
          images[ext][shape] = []
        images[ext][shape].append(fpath)
      except Exception as e:
        logs(f"{e}\nWARNING : something wrong happened with this file : '{fpath}'; this file will be ignored")
    elif ext in VIDEO_EXTENSIONS:
      try:
        size = os.stat(fpath).st_size
        if size not in videos[ext]:
          videos[ext][size] = []
        videos[ext][size].append(fpath)
      except Exception as e:
        logs(f"{e}\nWARNING : something wrong happened with this file : '{fpath}'; this file will be ignored")

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
  old_date = round(os.path.getctime(old))
  new_date = round(os.path.getctime(new))
  if new_date < old_date:
    old, new = p1, p2
    old_date, new_date = new_date, old_date
  return old, new, dt.datetime.fromtimestamp(old_date), dt.datetime.fromtimestamp(new_date)

# Main loop; iterate on every images
DuplicatesInfo = recordclass(
  "DuplicatesInfo", ["old", "new", "old_date", "new_date", "remove_old", "remove_new"]
)

# Get image pixels from cache or compute it
def get_image_pixels(im_path, draft_shape, listLocations, queue_cache, im_index):
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

# Detect potential duplicates images for given extension and shape
duplicates = list()
positionsFactors = [0, .25, .5, .75, 1]
def iterate_queue(queue, queue_cache, im1_index, shape, progression, percentage):
  global positionsFactors, duplicates

  # Compute pixels positions to use for comparison
  draft_shape = (shape[0] // 16, shape[1] // 16)
  listLocations = [
    tuple(
      (int(draft_shape[0] * i), int(draft_shape[1] * j))
      for i in positionsFactors
      for j in positionsFactors
    )
  ]
  # Iterate queue
  while queue:
    # Compute new image hash and cache it
    im1_path = queue.pop()
    im1_pixels = get_image_pixels(im1_path, draft_shape, listLocations, queue_cache, im1_index)
    # Compare with other images
    for im2_index in range(im1_index):
      im2_path = queue[im2_index]
      if im1_pixels in get_image_pixels(im2_path, draft_shape, listLocations, queue_cache, im2_index):
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
        logs("Potential duplicates:", im1_path, im2_path)
        break
    # Iterate
    im1_index -= 1
    progression += 1
    if progression / total_images > percentage:
      logs(round(100 * percentage), "%")
      percentage += PERCENTAGE
  return progression, percentage

# Compute all images hashes, compatible with multiprocessing
def multiprocess_compute_cache(queue, queue_cache, shape):
  global positionsFactors, duplicates

  # Compute pixels positions to use for comparison
  draft_shape = (shape[0] // 16, shape[1] // 16)
  listLocations = [
    tuple(
      (int(draft_shape[0] * i), int(draft_shape[1] * j))
      for i in positionsFactors
      for j in positionsFactors
    )
  ]
  # Iterate queue
  while not queue.empty():
    try:
      im_index, im_path = queue.get_nowait()
      get_image_pixels(im_path, draft_shape, listLocations, queue_cache, im_index)
    except:
      pass

# Find potential duplicates in registered paths
def iterate_paths():
  global nb_images, images
  logs("Iterating over all images...")
  progression, percentage = 0, 0
  for ext in images:
    for shape in images[ext]:
      queue = images[ext][shape]
      if nb_images[ext][shape] < 50:
        queue_cache = np.full((len(queue),), None, dtype=object)
        progression, percentage = iterate_queue(queue, queue_cache, nb_images[ext][shape]-1, shape, progression, percentage)
      else:
        m_queue = multiprocessing.Queue()
        for i, path in enumerate(queue):
          m_queue.put((i, path))
        m_queue_cache = multiprocessing.Manager().list()
        m_queue_cache.extend([None for _ in range(len(images[ext][shape]))])
        processes = []
        for _ in range(min(len(queue) // 50, 4)):
          process = multiprocessing.Process(
            target=multiprocess_compute_cache,
            args=(m_queue, m_queue_cache, shape)
          )
          processes.append(process)
          process.start()
        multiprocess_compute_cache(m_queue, m_queue_cache, shape)
        for process in processes:
          process.join()
        progression, percentage = iterate_queue(queue, m_queue_cache, nb_images[ext][shape]-1, shape, progression, percentage)

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
          logs("Potential duplicates:", v1, v2)
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
      ROOT_DIR, BIN_DIR, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, PERCENTAGE = settings_manager.get_settings()
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
    messagebox.showerror("Something went wrong :(", error_traceback)
    logs("Something went wrong :(")
    logs("Press enter twice to exit.")
    input()
    input()
    sys.exit(1)
