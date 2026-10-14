"""Inspect a PBL (PowerBuilder Library) OLE compound document."""
import sys, olefile, os

def main(path):
    print(f"== {path} size={os.path.getsize(path)}")
    if not olefile.isOleFile(path):
        print("NOT OLE")
        return
    ole = olefile.OleFileIO(path)
    for s in ole.listdir(streams=True, storages=True):
        try:
            size = ole.get_size("/".join(s))
        except Exception:
            size = "?"
        print(f"  {s}  size={size}")
    ole.close()

if __name__ == "__main__":
    main(sys.argv[1])
