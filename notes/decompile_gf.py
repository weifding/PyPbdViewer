"""Decompile gf_applog from dajy.pbd."""
import sys, struct
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb

pbd_path = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
data = open(pbd_path, "rb").read()
print("pbd size:", len(data))

# Walk PBD directory to find entries
# PBD format: header then entry directory
# Skip magic
pos = 0
magic = data[:4]
print("magic:", magic)
