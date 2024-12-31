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
        logs(f"{e}\nSomething wrong happened with this file : '{fpath}'; this file will be ignored", level="WARN")
    elif ext in VIDEO_EXTENSIONS:
      try:
        size = os.stat(fpath).st_size
        if size not in videos[ext]:
          videos[ext][size] = []
        videos[ext][size].append(fpath)
      except Exception as e:
        logs(f"{e}\nSomething wrong happened with this file : '{fpath}'; this file will be ignored", level="WARN")

# Count number of images per extension and shape
def count_files():
  global nb_images, nb_videos, total_images, total_videos
  print()
  logs("EXT\tSHAPE\tNB_IMAGES", level="INFO")
  for ext in IMAGE_EXTENSIONS:
    if not images[ext]:
      continue
    logs(f"[ {ext} ]", level="INFO")
    one_or_less = []
    for shape in images[ext]:
      if not images[ext][shape]:
        continue
      count = len(images[ext][shape])
      if count <= 1:
        one_or_less.append(shape)
      else:
        logs(f"\t  {shape}:   \t{count}", level="INFO")
        nb_images[ext][shape] = count
        total_images += count
    for shape in one_or_less:
      images[ext].pop(shape)
  print()
  logs("EXT\tSIZE\tNB_VIDEOS", level="INFO")
  for ext in VIDEO_EXTENSIONS:
    if not videos[ext]:
      continue
    logs(f"[ {ext} ]", level="INFO")
    one_or_less = []
    for size in videos[ext]:
      if not videos[ext][size]:
        continue
      count = len(videos[ext][size])
      if count <= 1:
        one_or_less.append(size)
      else:
        logs(f"\t  {size}:   \t{count}", level="INFO")
        nb_videos[ext][size] = count
        total_videos += count
    for size in one_or_less:
      videos[ext].pop(size)
  print()
  logs(total_images, "potentially duplicated images.", level="INFO")
  logs(total_videos, "potentially duplicated videos.\n", level="INFO")

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
def get_image_pixels(im_path, draft_shape, listLocations, pixels_cache, im_index):
  if pixels_cache[im_index] is None:
    # Cache image pixels
    im = Image.open(im_path)
    im.draft("RGB", draft_shape)
    pixel_data = im.load()
    pixels_cache[im_index] = tuple(
      pixel_data[coordinates] for coordinates in listLocations
    )
  return pixels_cache[im_index]

# Detect potential duplicates images for given extension and shape
positionsFactors = [0, .25, .5, .75, 1]
def iterate_queue(queue, pixels_cache, nb_indexes, shape, mp_progression_queue, duplicates):
  global positionsFactors
  # Compute pixels positions to use for comparison
  draft_shape = (shape[0] // 16, shape[1] // 16)
  listLocations = tuple(
    (int(draft_shape[0] * i), int(draft_shape[1] * j))
    for i in positionsFactors
    for j in positionsFactors
  )
  # Iterate queue
  im1_index = nb_indexes
  potential_duplicates = []
  while queue:
    # Compute new image hash and cache it
    im1_path = queue.pop()
    im1_pixels = get_image_pixels(im1_path, draft_shape, listLocations, pixels_cache, im1_index)
    # Compare with other images
    for im2_index in range(im1_index):
      im2_path = queue[im2_index]
      if im1_pixels == get_image_pixels(im2_path, draft_shape, listLocations, pixels_cache, im2_index):
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
        potential_duplicates.append((old, new))
        break
    # Iterate and report progression
    im1_index -= 1
    if (nb_indexes - im1_index) % 100 == 0:
      mp_progression_queue.put((100, potential_duplicates))
      potential_duplicates = []
  mp_progression_queue.put((nb_indexes % 100, potential_duplicates))

# Report multiprocess scan progression
def report_progression(progression, percentage, mp_progression_queue):
  while not mp_progression_queue.empty():
    nb_images_processed, list_duplicates = mp_progression_queue.get_nowait()
    progression += nb_images_processed
    for old_path, new_path in list_duplicates:
      logs(f"Potential duplicated images: {old_path} {new_path}", level="OK")
  if progression / total_images > percentage + PERCENTAGE:
    percentage = progression / total_images
    logs(f"{round(100 * percentage)} %", level="INFO")
  return progression, percentage

# Return batches of images eligible for multiprocessing computing
def get_mp_shapes(image_shapes, image_counts):
  # Step 1: Flatten the dictionary and filter small batches
  filtered_list = [
      (ext, shape, value)
      for ext, shapes in image_counts.items()
      for shape, value in shapes.items()
      if value > 150
  ]
  # Step 2: Sort the filtered list by value in descending order
  filtered_list.sort(key=lambda x: x[2], reverse=True)
  # Step 3: Take up to the top 8 entries
  top_shapes = filtered_list[:multiprocessing.cpu_count()-1]
  # Step 4: Extract (extension, shape) tuples
  result = [(ext, shape) for ext, shape, value in top_shapes]
  return [(image_shapes[ext].pop(shape), ext, shape, image_counts[ext][shape]) for ext, shape in result]

# Find potential duplicates in registered paths, create subprocesses for biggest batches
def iterate_paths():
  global images, nb_images
  logs("Iterating over all images...", level="INFO")
  processes = []
  progression, percentage = 0, 0
  mp_progression_queue = multiprocessing.Queue()
  # Spawn subprocesses for big batches
  mp_shapes = get_mp_shapes(images, nb_images)
  if mp_shapes:
    logs(f"Spawning {len(mp_shapes)} subprocesses for the following shapes :", level="INFO")
    for image_batch, ext, shape, images_nb in mp_shapes:
      pixels_cache = np.full((len(image_batch),), None, dtype=object)
      process = multiprocessing.Process(
        target=iterate_queue,
        args=(image_batch, pixels_cache, images_nb-1, shape, mp_progression_queue, duplicates)
      )
      processes.append(process)
      process.start()
      logs(f" • {ext} {shape} -> {images_nb} elements to scan", level="OK")
  # Scan rest of duplicates
  logs("Starting main scan...", level="INFO")
  for ext in images:
    for shape in images[ext]:
      queue = images[ext][shape]
      pixels_cache = np.full((nb_images[ext][shape],), None, dtype=object)
      iterate_queue(queue, pixels_cache, nb_images[ext][shape]-1, shape, mp_progression_queue, duplicates)
      progression, percentage = report_progression(progression, percentage, mp_progression_queue)
  # Wait for subprocesses to end
  while any(p.is_alive() for p in processes):
    progression, percentage = report_progression(progression, percentage, mp_progression_queue)
    time.sleep(1)
  logs("100 %. Done.", level="SUCCESS")
  logs("Iterating over videos...", level="INFO")
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
          logs("Potential duplicated videos:", v1, v2, level="OK")
  logs("100 %. Done.", level="SUCCESS")

if __name__ == "__main__":
  multiprocessing.freeze_support()
  try:
    while True:
      # Clear variables
      total_images = 0
      total_videos = 0
      duplicates = multiprocessing.Manager().list()
      # Load settings
      settings_manager = SettingsManager()
      ROOT_DIR, BIN_DIR, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, PERCENTAGE = settings_manager.get_settings()
      if not os.path.isdir(ROOT_DIR):
        raise Exception(f"Error: '{ROOT_DIR}' is not a directory, please provide a valid path")
      # List files
      images = {ext: {} for ext in IMAGE_EXTENSIONS}
      nb_images = {ext: {} for ext in IMAGE_EXTENSIONS}
      videos = {ext: {} for ext in VIDEO_EXTENSIONS}
      nb_videos = {ext: {} for ext in VIDEO_EXTENSIONS}
      logs("Listing images and videos...", level="INFO")
      t_start = time.time()
      list_files(directory=ROOT_DIR)
      # Count files
      count_files()
      # Start duplicates detection
      iterate_paths()
      logs(f"Computing time : {round(time.time() - t_start, 2)} seconds.", level="INFO")
      # Show and move images
      if duplicates:
        duplicates_mover = DuplicatesMover(
          ROOT_DIR, BIN_DIR, VIDEO_EXTENSIONS, duplicates
        )
        duplicates_mover.window_loop()
      else:
        logs("No duplicate found. Back to settings.", level="INFO")
      print()
  except Exception as e:
    error_traceback = traceback.format_exc()
    logs(error_traceback, level="ERROR")
    messagebox.showerror("Something went wrong :(", error_traceback)
    logs("Something went wrong :(", level="ERROR")
    logs("Press enter to exit.", level="INFO")
    input()
    sys.exit(1)
