import os, sys
from PIL import Image


path = "c:\\Coding\\PyPrograms\\ChessProject\\images"
images_names = os.listdir(path)
for image_name in images_names:
    if not "png" in image_name: continue
    img = Image.open(f"{path}\\{image_name}")
    # img.thumbnail((480, 480))
    # img.thumbnail((60, 60))
    img.save(f"{path}\\{image_name}")
    print(image_name)
