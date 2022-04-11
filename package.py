import zlib
from struct import pack, unpack
from pathlib import Path

from pyamf.amf3 import ByteArray



def inflate(data):
    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated

def deflate(data, compresslevel=9):
    compress = zlib.compressobj(
            compresslevel,        # level: 0-9
            zlib.DEFLATED,        # method: must be DEFLATED
            -zlib.MAX_WBITS,      # window size in bits:
                                  #   -15..-8: negate, suppress header
                                  #   8..15: normal
                                  #   16..30: subtract 16, gzip header
            zlib.DEF_MEM_LEVEL,   # mem level: 1..8/9
            0                     # strategy:
                                  #   0 = Z_DEFAULT_STRATEGY
                                  #   1 = Z_FILTERED
                                  #   2 = Z_HUFFMAN_ONLY
                                  #   3 = Z_RLE
                                  #   4 = Z_FIXED
    )
    deflated = compress.compress(data)
    deflated += compress.flush()
    return deflated



def read_package(filename, offs=0):
    with open(filename, 'rb') as f:
        decomp = inflate(f.read()[offs:])
        return decomp


def get_ext(fn: str):
    return fn[fn.rfind('.')+1:]
    

EXT_CATEGORY_DICT = {
    'TXT': 'text',
    'DAT': 'text',
    'WAS': 'text',
    'JPG': 'image',
    'PNG': 'image',
    'GIF': 'image',
    'JPEG': 'image',
    'FLV': 'image',
    'MP4': 'image',
    'MP3': 'sound',
    'SWF': 'swf',
    'WFF': 'font',
}

def get_file_type(filename: str):
    ext = get_ext(filename).upper()
    ftype = EXT_CATEGORY_DICT.get(ext)
    return ftype if ftype != None else 'other'



# This one is directly translated out of the decompiled game
class PackageLoader:
    def __init__(self, filename: str):
        self.packageFile = filename
        self.packageFs = open(filename, 'rb')
        self.__extractKvs()
        pass

    def __extractKvs(self):
        with open(self.packageFile, 'rb') as f:
            offs = unpack('>I', f.read(4))[0]
            f.seek(offs)
            data = inflate(f.read())
            self.kvs: dict = ByteArray(data).readObject()
            # For some reason some values are interpreted as float...
            for val in self.kvs.values():
                val[0] = int(val[0])
                val[1] = int(val[1])
    
    def loadFileBytes(self, filename: str, forceExt: str = None):
        if not filename in self.kvs:
            raise FileNotFoundError(filename)
        kvsDat = self.kvs[filename]
        ext = forceExt if forceExt != None else get_ext(filename)
        ext = ext.upper()

        self.packageFs.seek(kvsDat[0])
        fileBytes = self.packageFs.read(kvsDat[1])

        fileBytes = inflate(fileBytes)
        # Original function does some interpretation here - I will just return the decompressed bytes
        return fileBytes


    def loadFileList(self, fileList: list[str] = None):
        """Loads all files in the given list or the whole archive if None is given"""
        ret = {
            "text":{},
            "image":{},
            "sound":{},
            "xml":{},
            "other":{},
            "swf":{},
            "font":{},
        }
        arr = fileList if fileList != None else self.kvs.keys()
        for filename in arr:
            data = self.loadFileBytes(filename)
            ret[get_file_type(filename)][filename] = data
        return ret
    
    def loadFileCategories(self):
        ret = {
            "text":{},
            "image":{},
            "sound":{},
            "xml":{},
            "other":{},
            "swf":{},
            "font":{},
        }
        for filename in self.kvs.keys():
            ret[get_file_type(filename)][filename] = filename
        return ret
    

    def export(self, export_dir=None, categories=False):
        if export_dir == None:
            p = Path(self.packageFile)
            export_dir = p.parent / p.stem
        root = Path(export_dir)
        root.mkdir(parents=True, exist_ok=True)
        
        if categories:
            cats = self.loadFileCategories()
            for name, files in cats.items():
                if len(files) == 0:
                    continue
                p = root / name
                p.mkdir(exist_ok=True)
                for filename in files:
                    self.export_file(filename, p / filename)
        else:
            for filename in self.kvs.keys():
                self.export_file(filename, root / filename)


    def export_file(self, filename, path):
        with open(path, 'wb') as f:
            f.write(self.loadFileBytes(filename))


    def close(self):
        self.packageFs.close()
    
    def __del__(self):
        self.close()
    


# This one is self made
def create_package(directory, output_file=None):
    dir = Path(directory)
    files = [fn for fn in dir.rglob('*')]
    if output_file == None:
        output_file = dir.with_suffix('.dat')
    kvs = {}
    with open(output_file, 'wb') as fout:
        fout.seek(4)
        for filepath in files:
            if not filepath.is_file():
                continue
            with open(filepath, 'rb') as fin:
                data = deflate(fin.read())
            pos = fout.tell()
            length = len(data)
            name = filepath.name
            fout.write(data)
            kvs[name] = (pos, length)
        
        kvs_pos = fout.tell()
        kvsData = ByteArray()
        kvsData.writeObject(kvs)
        kvsData = deflate(bytes(kvsData))
        fout.write(kvsData)

        fout.seek(0)
        fout.write(pack('>I', kvs_pos))
            




if __name__ == '__main__':
    from argparse import ArgumentParser
    args = ArgumentParser()
    args.add_argument('--dirs', '-d', action='store_true', help='(unpack only) Create directories based on file types (not necessary but makes navigation easier)')
    args.add_argument('mode', choices=['pack', 'unpack'], help='Mode (pack or unpack)')
    args.add_argument('input', help='Input file or directory name')
    args.add_argument('output', nargs='?', default=None, help='Output file or directory name')
    args = args.parse_args()

    if args.mode == 'pack':
        create_package(args.input, args.output)
    else: # unpack
        PackageLoader(args.input).export(args.output, args.dirs)
