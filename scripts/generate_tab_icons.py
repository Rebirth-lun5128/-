"""Generate WeChat mini program tabBar icons (81x81 PNG)."""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 81
GRAY = (153, 153, 153, 255)


def rgba(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def new_canvas() -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def save_pair(folder: Path, name: str, draw_fn, active_color: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for suffix, color in [("", GRAY), ("-active", rgba(active_color))]:
        img = new_canvas()
        draw_fn(ImageDraw.Draw(img), color)
        img.save(folder / f"{name}{suffix}.png", "PNG")


def draw_home(d: ImageDraw.ImageDraw, c: tuple) -> None:
    d.polygon([(40, 18), (62, 34), (62, 58), (18, 58), (18, 34)], outline=c, width=4)
    d.rectangle([32, 42, 48, 58], fill=c)


def draw_order(d: ImageDraw.ImageDraw, c: tuple) -> None:
    d.rounded_rectangle([22, 16, 58, 64], radius=6, outline=c, width=4)
    for y in (30, 42, 54):
        d.line([(30, y), (50, y)], fill=c, width=3)


def draw_profile(d: ImageDraw.ImageDraw, c: tuple) -> None:
    d.ellipse([30, 16, 50, 36], outline=c, width=4)
    d.arc([20, 34, 60, 68], 20, 160, fill=c, width=4)


def draw_menu(d: ImageDraw.ImageDraw, c: tuple) -> None:
    for y in (26, 40, 54):
        d.line([(22, y), (58, y)], fill=c, width=4)


def draw_wallet(d: ImageDraw.ImageDraw, c: tuple) -> None:
    d.rounded_rectangle([18, 24, 62, 56], radius=8, outline=c, width=4)
    d.ellipse([48, 34, 58, 44], fill=c)


def draw_store(d: ImageDraw.ImageDraw, c: tuple) -> None:
    d.rectangle([20, 30, 60, 62], outline=c, width=4)
    d.polygon([(20, 30), (40, 16), (60, 30)], outline=c, width=4)
    d.rectangle([30, 42, 38, 52], fill=c)
    d.rectangle([46, 42, 54, 52], fill=c)


def draw_rider(d: ImageDraw.ImageDraw, c: tuple) -> None:
    d.ellipse([28, 14, 44, 30], outline=c, width=3)
    d.line([(36, 30), (36, 48)], fill=c, width=3)
    d.line([(36, 36), (24, 52)], fill=c, width=3)
    d.line([(36, 36), (52, 44)], fill=c, width=3)
    d.ellipse([46, 48, 58, 60], outline=c, width=3)


def generate_for_project(root: Path, active_color: str, icons: dict) -> None:
    folder = root / "images"
    for name, draw_fn in icons.items():
        save_pair(folder, f"tab-{name}", draw_fn, active_color)
    print(f"  {root.name}: {len(icons) * 2} icons")


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    projects = [
        (base / "miniprogram-user", "#FF6B35", {
            "home": draw_home,
            "order": draw_order,
            "profile": draw_profile,
        }),
        (base / "miniprogram-merchant", "#07C160", {
            "home": draw_home,
            "order": draw_order,
            "menu": draw_menu,
        }),
        (base / "miniprogram-rider", "#FF9800", {
            "home": draw_home,
            "order": draw_order,
            "wallet": draw_wallet,
        }),
        (base / "miniprogram-admin", "#FF6B35", {
            "home": draw_home,
            "store": draw_store,
            "rider": draw_rider,
            "order": draw_order,
        }),
    ]
    print("Generating tabBar icons...")
    for root, color, icons in projects:
        if root.is_dir():
            generate_for_project(root, color, icons)
    print("Done.")


if __name__ == "__main__":
    main()
