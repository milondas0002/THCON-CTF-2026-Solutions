from pathlib import Path

inp = Path("weird_file.thc")
out = Path("extracted.png")

text = inp.read_text(encoding="utf-8", errors="ignore")

data = bytearray()
value = 0
count = 0

for ch in text:
    if ch == "👍":
        bit = 1
    elif ch == "👎":
        bit = 0
    else:
        continue

    value = (value << 1) | bit
    count += 1

    if count == 8:
        data.append(value)
        value = 0
        count = 0

out.write_bytes(data)

print("Done. Extracted:", out)
