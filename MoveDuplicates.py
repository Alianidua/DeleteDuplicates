import os
import time
import datetime as dt
from PIL import Image
from recordclass import recordclass
from DuplicatesMover import DuplicatesMover

# Load settings
ROOT_DIR = None  # The directory where your images are stored
BIN_DIR = None  # The directory where you want to put your duplicated files
image_extensions = None  # The images format

def load_settings():
    global ROOT_DIR, BIN_DIR, image_extensions
    with open("./settings.txt", encoding='utf-8') as settings:
        lines = settings.readlines()
    ROOT_DIR = lines[0].split("=")[1]
    print(ROOT_DIR[-1])
    while ROOT_DIR[-1] == "\\" or ROOT_DIR[-1] == " " or ROOT_DIR[-1] == "\n":
        ROOT_DIR = ROOT_DIR[:-1]
    while ROOT_DIR[0] == " ":
        ROOT_DIR = ROOT_DIR[1:]
    BIN_DIR = lines[1].split("=")[1]
    while BIN_DIR and (BIN_DIR[-1] == "\\" or BIN_DIR[-1] == " " or BIN_DIR[-1] == "\n"):
        BIN_DIR = BIN_DIR[:-1]
    while BIN_DIR and BIN_DIR[0] == " ":
        BIN_DIR = BIN_DIR[1:]
    image_extensions = lines[2].split("=")[1].replace(" ", "").split(",")
    print(f"Settings loaded :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {image_extensions}")


# Return a queue with all images in root_dir
queue = list()
nb_images = 0
def list_images(directory=ROOT_DIR):
    global nb_images
    D = os.listdir(directory)
    for fpath in D:
        fpath = f"{directory}/{fpath}"
        if os.path.isdir(fpath):
            list_images(fpath)
        elif fpath.split(".")[-1] in image_extensions:
            nb_images += 1
            queue.append(fpath)


# Compare 2 images
def compare_images(im1_pixels, im2_path, shape, locations):
    im2 = Image.open(im2_path)
    if im2.size != shape:
        return False
    im2_pixels = tuple(im2.getpixel(coordinates) for coordinates in locations)
    return im1_pixels == im2_pixels


# Main loop; iterate on every images
DuplicatesInfo = recordclass("DupliatesInfo", ["old", "new", "old_date", "new_date", "remove"])
duplicates = list()


def iterate_paths():
    print("Iterating over all images...")
    i = 0
    percentage = 0
    while queue:
        # Iterate
        i += 1
        if i / nb_images > percentage:
            print(round(100 * percentage), "%")
            percentage += 0.05
        # Compute new image value
        im1_path = queue.pop()
        image = Image.open(im1_path)
        shape = image.size
        locations = (
            (image.width // 3, image.height // 3),
            (image.width // 5, image.height // 3),
            (image.width // 5, image.height // 5),
            (image.width // 5, image.height // 5),
        )
        im1_pixels = tuple(image.getpixel(coordinates) for coordinates in locations)
        # Compare with other images
        for im2_path in queue:
            if compare_images(im1_pixels, im2_path, shape, locations):
                old, new = im1_path, im2_path
                old_date, new_date = round(os.path.getmtime(old)), round(os.path.getmtime(new))
                if new_date < old_date:
                    old, new = im2_path, im1_path
                    old_date, new_date = new_date, old_date
                duplicates.append(
                    DuplicatesInfo(
                        old=old,
                        new=new,
                        old_date=dt.datetime.fromtimestamp(old_date),
                        new_date=dt.datetime.fromtimestamp(new_date),
                        remove=True,
                    )
                )
                print("Duplicates :", im1_path, im2_path)
                break
    print("100 %. Done.")


if __name__ == "__main__":

    t_start = time.time()
    load_settings()
    if BIN_DIR:
        if not os.path.exists(BIN_DIR):
            os.mkdir(BIN_DIR)
        elif os.listdir(BIN_DIR):
            print("Please, make sure the following directory is empty or does not already exist :", BIN_DIR)
            exit(1)
    print("Listing images...")
    list_images(directory=ROOT_DIR)
    print(nb_images, "images found")
    iterate_paths()
    print(f"Computing time : {round(time.time() - t_start, 2)} seconds.")
    # Show and move images
    if not duplicates:
        print("No duplicate found. Exiting 0...")
        exit(0)
    duplicates_mover = DuplicatesMover(ROOT_DIR, BIN_DIR, duplicates)
    duplicates_mover.window_loop()
