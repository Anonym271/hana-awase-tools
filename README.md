# hana-awase-tools
Package tool for the VN Hana Awase

## Requirements
- [Py3AMF](https://github.com/StdCarrot/Py3AMF)
- zlib (should be installed by default)

```
python -m pip install Py3AMF
```

## Usage
### Unpacking

```
python package.py -d unpack mypackage.dat destination_folder
```

Unpacks all contents of the package "mypackage.dat" into the directory "destination_folder".
`destination_folder` can be omitted and will default to the package name without the file extension.

The optional flag `-d` creates subdirectories for different file types (text, image, ...). This makes navigation easier but does not have any impact when repacking.

### Repacking

```
python package.py pack my_folder my_package.dat
```

Packs the content of the folder "my_folder" into the package "my_package.dat". Subdirectories will be scanned but the directory structure will be lost (since the packages are flat archives).

`my_package.dat` can be omitted and will default to the folder name with the extension ".dat".
