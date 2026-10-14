"""Run pcode_vm on a PBD function and show output."""
import sys, glob
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_entry import PbdFile

# pick a small pbd
pbd = sorted(glob.glob(r"D:\ynsoft\**\*.pbd", recursive=True))[0]
print("pbd:", pbd)
f = PbdFile(pbd)
entries = f.list_entries()
print("entries:", len(entries))
# find first function entry
for e in entries[:50]:
    if e.get("EntryType") == "FUN":
        print("---", e.get("Name"), e.get("Size"))
        try:
            f.load_entry(e)
            from pcode_vm import VM
            vm = VM(e.get("PCode", b""), variables=e.get("Variables", []))
            out = vm.run()
            print(out[:2000])
        except Exception as ex:
            print("err", ex)
        break
