import os
import time
from PIL import Image
from datetime import datetime
import matplotlib.pyplot as plt


# The directory where your images are stored
root_dir = "C:\\Users\\victi\\Desktop\\Gate\\Trié\\Prépa F1 2017-2019\\Snapchat"
# The directory where you want to put your duplicated files
bin_dir = "C:\\Users\\victi\\Desktop\\DuplicatedImages\\"

# Return a queue with all images in root_dir
nb_images = 0
queue = list()
image_extensions = ("jpg", "JPG", "png", "PNG", "jpeg", "svg")
def list_images(directory=root_dir):
	global nb_images
	print("Listing all images...")
	D = os.listdir(directory)
	for fpath in D:
		fpath = f"{directory}/{fpath}"
		if os.path.isdir(fpath):
			list_images(fpath)
		elif fpath.split(".")[-1] in image_extensions:
			queue.append(fpath)
	nb_images = len(queue)

# Compare 2 images
def compare_images(im1_pixels, im2_path, shape, locations):
	im2 = Image.open(im2_path)
	if im2.size != shape:
		return False
	im2_pixels = tuple(im2.getpixel(coordinates) for coordinates in locations)
	return im1_pixels == im2_pixels

# Main loop; iterate on every images
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
				duplicates.append((im1_path, im2_path))
				print("Duplicates :", im1_path, im2_path)
				break
	print("100 %. Done.")

# Show duplicates and move images to bin
def remove_duplicates():
	to_remove = list()
	print(f"{len(duplicates)} duplicated files. Moving them to bin folder: {bin_dir} ...")
	for files in duplicates:
		# Compare creation dates
		old, new = files[0], files[1]
		new_date, old_date = os.path.getmtime(new), os.path.getmtime(old)
		if new_date < old_date:
			new, old = files[0], files[1]
			old_date, new_date = new_date, old_date
		# Show images
		fig, ax = plt.subplots(1, 2)
		fig.set_size_inches(10, 10)
		plt.suptitle(f"Duplicated images ; the newest one will be placed in the bin folder ({bin_dir})\nOld image | New image")
		ax[0].imshow(Image.open(old))
		ax[0].set_title(f"{old}\n{datetime.fromtimestamp(old_date)}")
		ax[1].imshow(Image.open(new))
		ax[1].set_title(f"{new}\n{datetime.fromtimestamp(new_date)}")
		plt.show()
		# Append file to remove
		to_remove.append(new)
	# Move images
	for duplicate_path in to_remove:
		if os.path.exists(duplicate_path):
			os.rename(duplicate_path, f"{bin_dir}/{duplicate_path.split('/')[-1]}")


if __name__ == "__main__":

	t_start = time.time()
	if os.path.exists(bin_dir) and os.listdir(bin_dir):
		print("Please, make sure the following directory is empty or does not already exist :", bin_dir)
		exit(1)
	if not os.path.exists(bin_dir) or not os.path.isdir(bin_dir):
		os.mkdir(bin_dir)
	list_images(directory=root_dir)
	print(nb_images, "images found")
	iterate_paths()
	print(f"Computing time : {round(time.time() - t_start, 2)} seconds.")

	# Show images
	remove_duplicates()
