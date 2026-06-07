"""Convert PNG icon to multi-size ICO for PyInstaller."""
from pathlib import Path
from PIL import Image


def convert_png_to_ico(png_path: str, ico_path: str) -> None:
    img = Image.open(png_path)
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)
    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(icon.width, icon.height) for icon in icons],
        append_images=icons[1:],
    )
    print(f"Created {ico_path} with sizes: {sizes}")


if __name__ == "__main__":
    source = r"D:\edge_load\ChatGPT_Image_2026年6月7日_11_17_53.png"
    target = str(Path(__file__).parent / "icon.ico")
    convert_png_to_ico(source, target)
