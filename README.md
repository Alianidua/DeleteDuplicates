# Delete Duplicates

The aim of this program is to delete all the duplicated images in a directory and its subdirectories.

## Requirements

This program was coded using `Python3.7.9`.

Installation :

```
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

## Usage

You have to specify some parameters in settings.txt :
- ROOT_DIRECTORY : folder where your images are stored.
- BIN_DIRECTORY : folder where you want to put the duplicates. The directory should not exist or should be empty.
If no path is specified, the images are not moved.

To run the program, type :
```
python MoveDuplicates.py
```

The program works in 4 steps :

- First, list all the images in ROOT_DIRECTORY to process
- Second, compare the images and find duplicates
- Then, show every duplicate and wait for user confirmation for removal
- Last, move all duplicates to BIN_DIR

<ins>Note</ins>: for the moment the program is not able to efficiently detect images duplicated 3 or more times.
It must be runned multiple times to detect all duplicates properly.

## Build executable

```
pyinstaller --onefile MoveDuplicates.py && cp settings.txt dist/settings.txt
```

Run executable without closing child :

```
cmd.exe /k cmd /c MoveDuplicates.exe
```
