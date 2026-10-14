import os, re
candidates = []
for root, dirs, files in os.walk(r"E:\ChatGPT\PyPbdViewer\out\decompiled"):
    for f in files:
        if not f.endswith(".ps.txt"): continue
        p = os.path.join(root, f)
        try: txt = open(p, encoding="utf-8", errors="replace").read()
        except: continue
        for m in re.finditer(r"^global\s+type\s+(w_\w+)\s+from\s+window\b", txt, re.I | re.M):
            win = m.group(1)
            n_ctrl = len(set(re.findall(r"type\s+\w+\s+from\s+\w+\s+within\s+" + win, txt, re.I)))
            if 20 <= n_ctrl <= 60:
                tm = re.search(r"global\s+type\s+" + win + r"\s+from\s+window\b(.*?)^end\s+type",
                               txt, re.I | re.S | re.M)
                title = ""
                if tm:
                    t2 = re.search(r'string\s+title\s*=\s*"([^"]+)"', tm.group(1))
                    if t2: title = t2.group(1)
                candidates.append((n_ctrl, p, win, title))
candidates.sort(reverse=True)
seen = set()
for c in candidates:
    key = (c[2], c[3])
    if key in seen: continue
    seen.add(key)
    print(c)
    if len(seen) >= 10: break
