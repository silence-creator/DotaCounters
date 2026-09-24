"""Загрузка небольших иконок по адресам: параллельно и с кэшем на время работы.

Картинки возвращаются как PIL.Image, а не как ImageTk.PhotoImage: PhotoImage
можно создавать только в главном потоке Tk, а качать удобнее в фоновом.
"""

import hashlib
import io
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .config import cache_dir
from .net import create_scraper

#: Адреса с этим префиксом не качаются, а рисуются здесь же — для значков,
#: которых нет на CDN Valve.
LOCAL_ICON_PREFIX = "local:"

#: Рамка иконки героя в списке контрпиков: под строку шрифта Courier New 12.
HERO_ICON_BOX = (26, 15)

#: Цвет кружка для рисованных значков: регенерация здоровья и маны в цветах
#: полосок здоровья и маны из игры.
_LOCAL_COLORS = {
    "health_regen": (86, 180, 60),
    "mana_regen":   (58, 128, 214),
}

#: (адрес, рамка) -> готовая картинка или None, если скачать не удалось.
_cache = {}
_cache_lock = threading.Lock()
_local = threading.local()


def _scraper():
    """Свой HTTP-клиент на поток: сессию между потоками лучше не делить."""
    if not hasattr(_local, "scraper"):
        _local.scraper = create_scraper()
    return _local.scraper


def fit_to_box(img: Image.Image, box: tuple) -> Image.Image:
    """Вписать картинку в рамку box=(ширина, высота) по центру, сохранив пропорции.

    Все иконки получаются одного размера, поэтому строки с иконками разной
    формы (квадратные способности, вытянутые предметы) выравниваются по тексту.
    """
    box_w, box_h = box
    img = img.convert("RGBA")
    scale = min(box_w / img.width, box_h / img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", box, (0, 0, 0, 0))
    canvas.paste(img, ((box_w - size[0]) // 2, (box_h - size[1]) // 2), img)
    return canvas


def draw_local_icon(name: str) -> Image.Image | None:
    """Нарисовать значок «регенерации»: цветной кружок с плюсом.

    Рисуется крупно (64x64) и потом ужимается в рамку — так края выходят
    сглаженными. Незнакомое имя -> None.
    """
    color = _LOCAL_COLORS.get(name)
    if color is None:
        return None
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, size - 3, size - 3), fill=color + (255,))
    bar, arm = 10, 20  # толщина и полудлина перекладин плюса
    c = size // 2
    white = (255, 255, 255, 255)
    draw.rectangle((c - arm, c - bar // 2, c + arm, c + bar // 2), fill=white)
    draw.rectangle((c - bar // 2, c - arm, c + bar // 2, c + arm), fill=white)
    return img


# ── Минимальная растеризация SVG ──────────────────────────────────────────────
#
# PIL не умеет SVG, а тащить cairosvg ради одного значка (талантов — он есть на
# CDN только в SVG) не хочется: на Windows ему нужны нативные библиотеки Cairo.
# Здесь поддержано ровно то, из чего состоят простые плоские иконки: элементы
# <path> с командами M L H V C Z (абсолютными и относительными) и сплошной
# заливкой. Контуры заливаются по правилу even-odd — так вложенный контур
# становится дыркой. На чём-то большем функция бросает ValueError, и значок
# просто не показывается.

# Любая буква — команда (кроме e/E: это показатель степени внутри числа). Так
# неподдержанная команда вроде дуги A даёт ошибку, а не пропадает молча.
_SVG_TOKEN = re.compile(r"[A-DF-Za-df-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_SVG_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Z": 0}
_NAMED_COLORS = {"white": (255, 255, 255), "black": (0, 0, 0)}


def _svg_color(value: str | None, opacity: str | None):
    """Цвет заливки в RGBA; None для fill="none"."""
    value = (value or "black").strip().lower()
    if value == "none":
        return None
    if value in _NAMED_COLORS:
        rgb = _NAMED_COLORS[value]
    elif re.fullmatch(r"#[0-9a-f]{6}", value):
        rgb = tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
    elif re.fullmatch(r"#[0-9a-f]{3}", value):
        rgb = tuple(int(c * 2, 16) for c in value[1:])
    else:
        raise ValueError("неподдерживаемый цвет: %r" % value)
    alpha = round(255 * max(0.0, min(1.0, float(opacity)))) if opacity else 255
    return rgb + (alpha,)


def _svg_subpaths(d: str, steps: int = 16) -> list:
    """Разобрать атрибут d в список контуров — списков точек."""
    tokens = _SVG_TOKEN.findall(d)
    subpaths, points = [], []
    x = y = start_x = start_y = 0.0
    cmd, i = None, 0
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if points:
                    subpaths.append(points)
                points, x, y = [], start_x, start_y
                continue
        if cmd is None or cmd.upper() not in _SVG_ARGS:
            raise ValueError("неподдерживаемая команда пути: %r" % cmd)
        n = _SVG_ARGS[cmd.upper()]
        if n == 0:  # числа после Z без новой команды — иначе цикл бы не сдвинулся
            raise ValueError("числа после команды %r" % cmd)
        args = [float(t) for t in tokens[i:i + n]]
        if len(args) < n:
            raise ValueError("не хватает чисел для команды %r" % cmd)
        i += n
        rel = cmd.islower()
        up = cmd.upper()
        if up == "M":
            if points:
                subpaths.append(points)
            x, y = (x + args[0], y + args[1]) if rel else args
            start_x, start_y = x, y
            points = [(x, y)]
            cmd = "l" if rel else "L"  # следующие пары после M — это L
        elif up == "L":
            x, y = (x + args[0], y + args[1]) if rel else args
            points.append((x, y))
        elif up == "H":
            x = x + args[0] if rel else args[0]
            points.append((x, y))
        elif up == "V":
            y = y + args[0] if rel else args[0]
            points.append((x, y))
        else:  # C — кубическая кривая Безье, раскладывается на отрезки
            if rel:
                args = [a + (x if k % 2 == 0 else y) for k, a in enumerate(args)]
            x1, y1, x2, y2, x3, y3 = args
            for s in range(1, steps + 1):
                t = s / steps
                u = 1 - t
                points.append((u ** 3 * x + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3,
                               u ** 3 * y + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3))
            x, y = x3, y3
    if points:
        subpaths.append(points)
    return subpaths


def rasterize_svg(svg: str, height: int = 128) -> Image.Image:
    """Нарисовать простую SVG-иконку в RGBA высотой height пикселей."""
    vb = re.search(r'viewBox="\s*([-\d.eE+]+)[\s,]+([-\d.eE+]+)[\s,]+([-\d.eE+]+)[\s,]+([-\d.eE+]+)', svg)
    if not vb:
        raise ValueError("нет viewBox")
    min_x, min_y, vb_w, vb_h = (float(v) for v in vb.groups())
    scale = height / vb_h
    size = (max(1, round(vb_w * scale)), height)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))

    paths = re.findall(r"<path\b([^>]*)>", svg)
    if not paths:
        raise ValueError("нет элементов path")
    for attrs in paths:
        d = re.search(r'\sd="([^"]*)"', attrs)
        color = _svg_color((re.search(r'\sfill="([^"]*)"', attrs) or [None, None])[1],
                           (re.search(r'\sfill-opacity="([^"]*)"', attrs) or [None, None])[1])
        if not d or color is None:
            continue
        mask = Image.new("L", size, 0)
        for contour in _svg_subpaths(d.group(1)):
            if len(contour) < 3:
                continue
            layer = Image.new("L", size, 0)
            ImageDraw.Draw(layer).polygon(
                [((px - min_x) * scale, (py - min_y) * scale) for px, py in contour], fill=255)
            mask = ImageChops.logical_xor(mask.convert("1"), layer.convert("1")).convert("L")
        fill = Image.new("RGBA", size, color)
        alpha = ImageChops.multiply(mask, Image.new("L", size, color[3]))
        fill.putalpha(alpha)
        canvas = Image.alpha_composite(canvas, fill)
    return canvas


def tint(img: Image.Image, color: str) -> Image.Image:
    """Перекрасить одноцветный значок в color («#rrggbb»), сохранив прозрачность.

    SVG-значки Valve белые — под тёмный сайт. На светлой теме Ghost White белый
    значок таланта сливался с фоном, поэтому интерфейс красит его в цвет текста.
    """
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    out = Image.new("RGBA", img.size, rgb + (255,))
    out.putalpha(img.getchannel("A"))
    return out


def is_glyph(url: str | None) -> bool:
    """Одноцветный значок, который стоит красить под тему: пока это SVG."""
    return bool(url) and url.lower().endswith(".svg")


def thicken(img: Image.Image, ratio: float = 7 / 96) -> Image.Image:
    """Утолщить тонкий контурный значок перед ужатием до размера строки.

    Линии значка таланта толщиной в пару процентов от высоты при 16 px
    превращаются в бледно-серое пятно. Расширение непрозрачной области на
    ratio от высоты подобрано на глаз: заметнее — и форма расплывается.
    """
    size = max(3, round(img.height * ratio) | 1)  # фильтру нужен нечётный размер
    alpha = img.getchannel("A").filter(ImageFilter.MaxFilter(size))
    rgb = img.convert("RGB").filter(ImageFilter.MaxFilter(size))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def _disk_path(url: str) -> str | None:
    """Файл кеша для адреса. Имя — хеш, чтобы не зависеть от длины и символов."""
    folder = cache_dir()
    if folder is None:
        return None
    suffix = ".svg" if url.lower().endswith(".svg") else ".bin"
    return os.path.join(folder, hashlib.sha1(url.encode("utf-8")).hexdigest() + suffix)


def _download(url: str) -> bytes | None:
    """Скачать файл, заглянув сперва в кеш на диске.

    Иконки героев и предметов не меняются годами, а за поиск их набегает
    полтора десятка, поэтому качать их каждый раз незачем.
    """
    path = _disk_path(url)
    if path:
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            pass
    resp = _scraper().get(url, timeout=10)
    if resp.status_code != 200:
        return None
    data = resp.content
    if path:
        try:
            tmp = path + ".part"       # чтобы в кеше не осело полфайла
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        except OSError:
            pass
    return data


def _load(url: str, box: tuple):
    if url.startswith(LOCAL_ICON_PREFIX):
        img = draw_local_icon(url[len(LOCAL_ICON_PREFIX):])
        return fit_to_box(img, box) if img is not None else None
    try:
        data = _download(url)
        if data is None:
            return None
        if url.lower().endswith(".svg"):
            # Рисуем крупно — при ужатии в рамку края выйдут сглаженными.
            big = rasterize_svg(data.decode("utf-8", "replace"), height=box[1] * 6)
            return fit_to_box(thicken(big), box)
        return fit_to_box(Image.open(io.BytesIO(data)), box)
    except Exception:
        return None


def load_icon(url: str, box=(24, 16)):
    """Одна иконка: память, потом диск, потом сеть. None, если не вышло."""
    return fetch_icons([url], box=box).get(url)


def fetch_icons(urls, box=(24, 16), workers=8) -> dict:
    """Скачать иконки. Возвращает {адрес: PIL.Image} только для удавшихся.

    Повторные адреса и уже скачанные ранее не запрашиваются заново.
    """
    unique = [u for u in dict.fromkeys(urls) if u]
    with _cache_lock:
        missing = [u for u in unique if (u, box) not in _cache]

    if missing:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda u: _load(u, box), missing))
        with _cache_lock:
            for url, img in zip(missing, results):
                _cache[(url, box)] = img

    with _cache_lock:
        return {u: _cache[(u, box)] for u in unique if _cache.get((u, box)) is not None}
