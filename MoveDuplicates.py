import os
import time
import datetime as dt
from PIL import Image
import get_image_size
from recordclass import recordclass
from DuplicatesMover import DuplicatesMover


# Load settings
ROOT_DIR = None  # The directory where your images are stored
BIN_DIR = None  # The directory where you want to put your duplicated files
IMAGE_EXTENSIONS = None  # The images format
PERCENTAGE = 0.05  # How frequently the program should show its progression

def load_settings():
    global ROOT_DIR, BIN_DIR, IMAGE_EXTENSIONS, PERCENTAGE
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
    IMAGE_EXTENSIONS = lines[2].split("=")[1].strip(" ").strip("\n").strip("\t").split(",")
    PERCENTAGE = float(lines[3].split("=")[1].strip(" ").strip("\n").strip("\t").replace(" ", ""))
    print(f"Settings loaded :\n\tROOT_DIR: {ROOT_DIR}\n\tBIN_DIR: {BIN_DIR}\n\tFORMATS: {IMAGE_EXTENSIONS}\n\tPROGRESSION_FREQUENCY: {PERCENTAGE}\n")


# Return a queue with all images in root_dir
images, nb_images = {}, 0
def list_images(directory=ROOT_DIR):
    global images
    D = os.listdir(directory)
    for fpath in D:
        fpath = f"{directory}/{fpath}"
        ext = fpath.split(".")[-1]
        if os.path.isdir(fpath):
            list_images(fpath)
        elif ext in IMAGE_EXTENSIONS:
            shape = get_image_size.get_image_size(fpath)
            if shape not in images[ext]:
                images[ext][get_image_size.get_image_size(fpath)] = []
            images[ext][get_image_size.get_image_size(fpath)].append(fpath)

# Count number of images per extension and shape
def count_images():
    global nb_images
    print("  EXT          SHAPE         NB_IMAGES")
    for ext in IMAGE_EXTENSIONS:
        if not images[ext]:
            continue
        print(f"[ {ext} ]")
        one_or_less = []
        for shape in images[ext]:
            if not images[ext][shape]:
                continue
            count = len(images[ext][shape])
            if count <= 1:
                one_or_less.append(shape)
            else:
                print(f"\t    {shape}:     \t{count}")
                nb_images += count
        for shape in one_or_less:
            images[ext].pop(shape)
    print()


# Compare 2 images
def compare_images(im1_pixels, im2_path, draft_shape, locations):
    im2 = Image.open(im2_path)
    im2.draft("RGB", draft_shape)
    im2_pixels = tuple(im2.getpixel(coordinates) for coordinates in locations)
    return im1_pixels == im2_pixels


# Main loop; iterate on every images
DuplicatesInfo = recordclass("DuplicatesInfo", ["old", "new", "old_date", "new_date", "remove"])
duplicates = list()

def iterate_queue(queue, shape, i, percentage):

    # Compute pixels positions to use for comparison
    draft_shape = (shape[0] // 50, shape[0] // 50)
    locations = [
        (draft_shape[0] // i, draft_shape[0] // j) for i in [1.25, 2, 2.75] for j in [1.25, 2, 2.75]
    ]

    while queue:
        # Iterate
        i += 1
        if i / nb_images > percentage:
            print(round(100 * percentage), "%")
            percentage += PERCENTAGE
        # Compute new image values
        im1_path = queue.pop()
        image = Image.open(im1_path)
        image.draft("RGB", draft_shape)
        im1_pixels = tuple(image.getpixel(coordinates) for coordinates in locations)
        # Compare with other images
        for im2_path in queue:
            if compare_images(im1_pixels, im2_path, draft_shape, locations):
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
    return i, percentage

def iterate_paths():
    print("Iterating over all images...")
    i = 0
    percentage = 0
    for ext in images:
        for shape in images[ext]:
            queue = images[ext][shape]
            i, percentage = iterate_queue(queue, shape, i, percentage)
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
    images = {ext: {} for ext in IMAGE_EXTENSIONS}
    list_images(directory=ROOT_DIR)
    count_images()
    print(nb_images, "potential duplicated images.")
    iterate_paths()
    print(f"Computing time : {round(time.time() - t_start, 2)} seconds.")
    # Show and move images
    if not duplicates:
        print("No duplicate found. Exiting 0...")
        exit(0)
    duplicates_mover = DuplicatesMover(ROOT_DIR, BIN_DIR, duplicates)
    duplicates_mover.window_loop()
