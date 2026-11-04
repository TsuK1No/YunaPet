import os
from PIL import Image, ImageDraw

os.makedirs("assets", exist_ok=True)

def create_chibi(filename, mood="idle", leg_offset=0):
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(48, 70), (80, 70), (92, 110), (36, 110)], fill="#301934")
    d.polygon([(56, 70), (72, 70), (64, 110)], fill="#e91e63")
    d.rectangle([50 + leg_offset, 108, 58 + leg_offset, 122], fill="#fce4ec")
    d.rectangle([70 - leg_offset, 108, 78 - leg_offset, 122], fill="#fce4ec")
    d.ellipse([48 + leg_offset, 118, 60 + leg_offset, 124], fill="#111111")
    d.ellipse([68 - leg_offset, 118, 80 - leg_offset, 124], fill="#111111")
    d.ellipse([26, 20, 102, 95], fill="#ff80ab")
    d.polygon([(24, 50), (14, 110), (38, 80)], fill="#ff80ab")
    d.polygon([(104, 50), (114, 110), (90, 80)], fill="#ff80ab")
    d.ellipse([34, 24, 94, 78], fill="#ffe0bd")
    if mood == "love":
        d.arc([46, 42, 58, 54], 0, 180, fill="#c2185b", width=3)
        d.arc([70, 42, 82, 54], 0, 180, fill="#c2185b", width=3)
        d.ellipse([40, 52, 52, 60], fill="#ff4081")
        d.ellipse([76, 52, 88, 60], fill="#ff4081")
    elif mood == "sit":
        d.line([46, 48, 58, 48], fill="#333333", width=3)
        d.line([70, 48, 82, 48], fill="#333333", width=3)
    else:
        d.ellipse([46, 42, 58, 56], fill="#d81b60")
        d.ellipse([70, 42, 82, 56], fill="#d81b60")
        d.ellipse([50, 44, 55, 49], fill="white")
        d.ellipse([74, 44, 79, 49], fill="white")
    d.polygon([(34, 30), (52, 50), (64, 32), (76, 50), (94, 30)], fill="#ff80ab")
    d.arc([58, 58, 70, 68], 0, 180, fill="#ad1457", width=2)
    img.save(os.path.join("assets", filename))

for name, mood, offset in [
    ("idle.png", "idle", 0), ("walk1.png", "idle", -4),
    ("walk2.png", "idle", 4), ("sit.png", "sit", 0), ("love.png", "love", 0),
]:
    create_chibi(name, mood, offset)
print("Спрайты созданы в папке assets/")
