# Delete Duplicates

The aim of this program is to delete all the duplicated images and videos in a directory and its subdirectories.

## Developer manual

This program was coded using `Python3.7.9`.

### Install and run the program

Installation :

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```
Run the program :

```bash
python MoveDuplicates.py
```

### Build executable

```bash
pyinstaller --onefile MoveDuplicates.py && cp settings.txt dist/settings.txt
```

Run executable without closing child process :

```bash
cmd.exe /k cmd /c MoveDuplicates.exe
```

## User manual

### How does it work

The program works in 4 steps :

- First, list all the images in `ROOT_DIRECTORY`
- Second, compare the images and find the potential duplicates
- Then, show every potential duplicate and wait for user confirmation to move the files into `BIN_DIR`
- Last, move all duplicates to `BIN_DIR`

<ins>Note</ins>: for the moment the program is not able to efficiently detect images duplicated 3 or more times.
It must be runned multiple times to detect all duplicates properly.

### How to use this program

Here is the list of parameters yo have to specify in `settings.txt` :

- `ROOT_DIRECTORY` : folder where your potential duplicates are stored
- `BIN_DIRECTORY` : folder where you want to put the duplicates ; the directory should not exist or should be empty
- `IMAGE_FORMATS` : comma-separated list of image extensions you want to detect
- `VIDEO_FORMATS` : comma-separated list of video extensions you want to detect
- `PROGRESSION_FREQUENCY`: how often you want the program to show its progression when it is comparing the files ; *0.01* means it will report its progression every 1%

If `BIN_DIRECTORY` is not specified, the images will not be moved at all.
