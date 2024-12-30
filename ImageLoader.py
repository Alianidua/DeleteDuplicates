import time
import cv2 as cv
from PIL import Image


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

def is_out_of_range(maxVal, radius, a, b):
  if a >= b:
    return min(a - b, abs(a - maxVal - b)) > radius
  return min(b - a, a + maxVal - b) > radius

class ImageLoader:
  def __init__(self, VIDEO_EXT, ROOT_DIR, duplicates, image_dict, index, r=2):

    # Multiprocessing components
    self.image_dict = image_dict
    self.ROOT_DIR = ROOT_DIR
    self.VIDEO_EXT = VIDEO_EXT
    self.duplicates = duplicates
    self.duplicates_len = len(duplicates)
    self.root_dir_len = len(ROOT_DIR) + 1
    self.index = index
    self.last_index = -1
    self.r = r

    with open("output.txt", "w") as f:
      f.write("Starting subprocess\n")
      while True:
        index = self.index.value
        if index != self.last_index:
          f.write(f"New Loop\n")
          for out_of_range in [x for x in self.image_dict.keys() if is_out_of_range(self.duplicates_len, self.r, index, x)]:
            f.write(f"Removing {out_of_range} because current index is {index}\n")
            self.image_dict.pop(out_of_range)
          for i in range(index - self.r, index + self.r + 1):
            i = i % self.duplicates_len
            if i not in self.image_dict:
              f.write(f"Adding {i}\n")
              files = self.duplicates[index]
              old, new, old_date, new_date, remove_old, remove_new = (
                files.old,
                files.new,
                files.old_date,
                files.new_date,
                files.remove_old,
                files.remove_new,
              )
              old_image, old_title, new_image, new_title = self.load_images(old, new, old_date, new_date)
              self.image_dict[i] = (old_image, old_title, new_image, new_title)
              f.write(f"{(old_image, old_title, new_image, new_title)}\n")
          f.write(f"Current state: {self.image_dict.keys()}\n")
          self.last_index = index
        time.sleep(0.5)
        f.flush()

  def load_images(self, old, new, old_date, new_date):
    old_image, new_image = mediaCouldNotBeLoaded, mediaCouldNotBeLoaded
    if old.split(".")[-1] in self.VIDEO_EXT:
      old_title = f"Oldest video\n{old[self.root_dir_len:]}\n{old_date}"
      new_title = f"Newest video\n{new[self.root_dir_len:]}\n{new_date}"
      videos = (cv.VideoCapture(old), cv.VideoCapture(new))
      try:
        old_image = cv.cvtColor(videos[0].read()[1], cv.COLOR_BGR2RGB)
      except:
        pass
      try:
        new_image = cv.cvtColor(videos[1].read()[1], cv.COLOR_BGR2RGB)
      except:
        pass
      videos[0].release(), videos[1].release()
    else:
      old_title = f"Oldest image\n{old[self.root_dir_len:]}\n{old_date}"
      new_title = f"Newest image\n{new[self.root_dir_len:]}\n{new_date}"
      try:
        old_image = Image.open(old)
        old_image.draft("RGB", (old_image.size[0] // 64, old_image.size[1] // 64))
      except:
        pass
      try:
        new_image = Image.open(new)
        new_image.draft("RGB", (new_image.size[0] // 64, new_image.size[1] // 64))
      except:
        pass
    return old_image, old_title, new_image, new_title