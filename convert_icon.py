from PIL import Image
import os

source_img = "8b9b75141a0a66b3de8357a550e77775.jpg"
target_ico = "icon.ico"

if os.path.exists(source_img):
    try:
        img = Image.open(source_img)
        img.save(target_ico, format='ICO', sizes=[(256, 256)])
        print(f"Successfully converted {source_img} to {target_ico}")
    except Exception as e:
        print(f"Failed to convert image: {e}")
else:
    print(f"Source image {source_img} not found.")
