"""Convert PNG icon to multi-size ICO for PyInstaller."""
from pathlib import Path
from PIL import Image


def convert_png_to_ico(png_path: str, ico_path: str) -> None:
    img = Image.open(png_path)
    # 多尺寸：16(标题栏/任务栏) 32(桌面/Alt+Tab) 48(资源管理器) 256(高DPI)
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    icons = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    icons[0].save(
        ico_path, format="ICO",
        sizes=[(s.width, s.height) for s in icons],
        append_images=icons[1:],
    )
    print(f"Created {ico_path} with sizes: {sizes}")


if __name__ == "__main__":
    source = r"D:\edge_load\ChatGPT_Image_2026年6月7日_11_17_53.png"
    target = str(Path(__file__).parent / "icon.ico")
    convert_png_to_ico(source, target)
