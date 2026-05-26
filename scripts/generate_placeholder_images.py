"""Generate default placeholder images for mini programs."""
from pathlib import Path

from PIL import Image, ImageDraw

SQUARE = 200
BG = (245, 245, 245, 255)
ICON = (200, 200, 200, 255)
ORANGE = (255, 107, 53, 255)


def draw_food(d: ImageDraw.ImageDraw) -> None:
    d.ellipse([60, 70, 140, 150], outline=ICON, width=4)
    d.line([(100, 50), (70, 75)], fill=ICON, width=4)
    d.line([(100, 50), (130, 75)], fill=ICON, width=4)


def draw_logo(d: ImageDraw.ImageDraw) -> None:
    d.rounded_rectangle([55, 50, 145, 150], radius=12, outline=ICON, width=4)
    d.ellipse([85, 75, 115, 105], outline=ICON, width=3)
    d.arc([70, 100, 130, 140], 10, 170, fill=ICON, width=3)


def draw_avatar(d: ImageDraw.ImageDraw) -> None:
    d.ellipse([70, 45, 130, 105], outline=ICON, width=4)
    d.arc([50, 95, 150, 175], 15, 165, fill=ICON, width=4)


def draw_banner(d: ImageDraw.ImageDraw) -> None:
    d.rounded_rectangle([40, 80, 710, 200], radius=16, outline=ICON, width=3)
    d.line([(120, 140), (300, 140)], fill=ICON, width=3)
    d.line([(120, 165), (500, 165)], fill=ICON, width=3)


def draw_app_logo(d: ImageDraw.ImageDraw) -> None:
    d.ellipse([40, 40, 160, 160], fill=(255, 255, 255, 230))
    d.ellipse([70, 55, 130, 115], outline=ORANGE, width=4)
    d.line([(100, 35), (75, 60)], fill=ORANGE, width=4)
    d.line([(100, 35), (125, 60)], fill=ORANGE, width=4)


def save_square(folder: Path, name: str, draw_fn, bg=BG) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (SQUARE, SQUARE), bg)
    draw_fn(ImageDraw.Draw(img))
    img.save(folder / name, "PNG")


def save_banner_file(folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (750, 280), BG)
    draw_banner(ImageDraw.Draw(img))
    img.save(folder / name, "PNG")


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    common = [
        base / "miniprogram-merchant" / "images",
        base / "miniprogram-user" / "images",
        base / "miniprogram-rider" / "images",
        base / "miniprogram-admin" / "images",
    ]
    for folder in common:
        if not folder.parent.is_dir():
            continue
        save_square(folder, "default-food.png", draw_food)
        save_square(folder, "default-logo.png", draw_logo)
        print(f"  {folder.parent.name}: default-food.png, default-logo.png")

    user_images = base / "miniprogram-user" / "images"
    if user_images.parent.is_dir():
        save_square(user_images, "default-avatar.png", draw_avatar)
        save_banner_file(user_images, "default-banner.png")
        save_square(user_images, "logo.png", draw_app_logo, bg=ORANGE)
        print("  miniprogram-user: default-avatar.png, default-banner.png, logo.png")


if __name__ == "__main__":
    print("Generating placeholder images...")
    main()
    print("Done.")
