import os, re
candidates = []
for root, dirs, files in os.walk(r"E:\ChatGPT\PyPbdViewer\out\decompiled"):
    for f in files:
        if not f.endswith(".ps.txt"): continue
        p = os.path.join(root, f)
        try: txt = open(p, encoding="utf-8", errors="replace").read()
        except: continue
        # Find all windows
        for m in re.finditer(r"^global\s+type\s+(w_\w+)\s+from\s+window\b", txt, re.I | re.M):
            win = m.group(1)
            # Top-level controls within win
            top = set(re.findall(r"type\s+(\w+)\s+from\s+(\w+)\s+within\s+" + win + r"\b", txt, re.I))
            if not top: continue
            # Find tab/tabpage controls
            tab_names = {n for n, a in top if a.lower() in ("tab",)}
            # Controls within tabpage (level 2)
            l2 = set()
            for tn in tab_names:
                for m2 in re.finditer(r"type\s+(\w+)\s+from\s+(\w+)\s+within\s+" + tn + r"\b", txt, re.I):
                    l2.add((m2.group(1), m2.group(2).lower()))
            # Controls within controls of l2 (level 3)
            l3 = set()
            for n2, a2 in l2:
                for m3 in re.finditer(r"type\s+(\w+)\s+from\s+(\w+)\s+within\s+" + n2 + r"\b", txt, re.I):
                    l3.add((m3.group(1), m3.group(2).lower()))
            total = len(top) + len(l2) + len(l3)
            if total >= 30 and l3:
                # title
                tm = re.search(r"global\s+type\s+" + win + r"\s+from\s+window\b(.*?)^end\s+type",
                               txt, re.I | re.S | re.M)
                title = ""
                if tm:
                    t2 = re.search(r'string\s+title\s*=\s*"([^"]+)"', tm.group(1))
                    if t2: title = t2.group(1)
                candidates.append((total, len(top), len(l2), len(l3), p, win, title))
candidates.sort(reverse=True)
for c in candidates[:10]: print(c)
