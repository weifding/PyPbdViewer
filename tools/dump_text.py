"""Extract all readable text from a PBL, replacing non-text bytes with newlines."""
import sys, re
p = sys.argv[1]
data = open(p, "rb").read()
out = []
for b in data:
    if 0x20 <= b < 0x7f or b in (0x0a, 0x0d, 0x09):
        out.append(chr(b))
    elif 0x81 <= b <= 0xfe:
        # GBK lead byte — keep as placeholder
        out.append(chr(b))
    else:
        out.append("\n")
text = "".join(out)
# collapse runs of >=3 newlines
text = re.sub(r"\n{3,}", "\n\n", text)
sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
