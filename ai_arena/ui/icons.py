"""Icon loader for AI Arena - loads SVG icons from assets/icons."""

from functools import lru_cache
from pathlib import Path

ICON_DIR = Path(__file__).parent / "assets" / "icons"


@lru_cache(maxsize=512)
def load_svg(name: str) -> str:
    """Load an SVG icon by filename (without .svg extension)."""
    path = ICON_DIR / f"{name}.svg"
    if path.exists():
        svg = path.read_text(encoding="utf-8")
        # Ensure consistent sizing
        if 'width="24"' in svg and 'height="24"' in svg:
            svg = svg.replace('width="24"', 'width="20"').replace('height="24"', 'height="20"')
        return svg
    return ""


# Pre-loaded commonly used icons (kebab-case filenames match asset files)
BOT = load_svg("bot")
CPU = load_svg("cpu")
SPARKLES = load_svg("sparkles")
ZAP = load_svg("zap")
USERS = load_svg("users")
SETTINGS = load_svg("settings")
NETWORK = load_svg("network")
MESSAGE_SQUARE = load_svg("message-square")
PLAY = load_svg("play")
PAUSE = load_svg("pause")
STOP = load_svg("square")
DOWNLOAD = load_svg("download")
FILE_TEXT = load_svg("file-text")
TERMINAL = load_svg("terminal")
CHEVRON_DOWN = load_svg("chevron-down")
CHEVRON_UP = load_svg("chevron-up")
X = load_svg("x")
CHECK = load_svg("check")
ALERT = load_svg("triangle-alert")
INFO = load_svg("info")
GLOBE = load_svg("globe")
REFRESH = load_svg("refresh-cw")
TRASH = load_svg("trash-2")
EDIT = load_svg("pen")
PLUS = load_svg("plus")
MINUS = load_svg("minus")
EYE = load_svg("eye")
EYE_OFF = load_svg("eye-off")
COPY = load_svg("copy")
SAVE = load_svg("save")
HOME = load_svg("house")
ARROW_RIGHT = load_svg("arrow-right")
ARROW_LEFT = load_svg("arrow-left")
EXTERNAL_LINK = load_svg("external-link")
STAR = load_svg("star")
TARGET = load_svg("target")
ACTIVITY = load_svg("activity")
LAYERS = load_svg("layers")
GIT_BRANCH = load_svg("git-branch")
DATABASE = load_svg("database")
SERVER = load_svg("server")
SHIELD = load_svg("shield")
LOCK = load_svg("lock")
KEY = load_svg("key")
MENU = load_svg("menu")
SUN = load_svg("sun")
MOON = load_svg("moon")


def get_icon(name: str) -> str:
    """Get an icon by name, loading on demand."""
    return load_svg(name)


def list_available() -> list[str]:
    """List all available icon names."""
    return [p.stem for p in ICON_DIR.glob("*.svg")]