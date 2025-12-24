
import math
import os
import random
import re
import shutil
import sys
import time

try:
    from colorama import just_fix_windows_console

    just_fix_windows_console()
except Exception:
    # Totally fine on non-Windows
    pass

# ---------------- basic config ---------------- #

FPS = 10

# Where to draw the scene (tree + house) in the terminal
SCENE_TOP = 2
SCENE_LEFT = 2

# Lyrics start column (no snow over here)
LYRICS_OFFSET_X = 54

# If your audio has ~11s of intro before the vocals start,
# shift the lyrics by that much so they land on-beat.
LYRIC_OFFSET = 0  # seconds

# Audio file to play.
# Change this to point at your own .wav/.mp3 if needed.
AUDIO_PATH = os.path.join(os.path.dirname(__file__), "1761712885_Wham! - Last Christmas (Official Video)_E8gmARGvPlI_default.wav")

# Colours
RESET = "\x1b[0m"
DIM = "\x1b[2m"
LYRICS_COLOR = "\x1b[92m"
PULSE_STAR_BRIGHT = "\x1b[93m"
PULSE_STAR_DIM = "\x1b[33m"
HOUSE_COLOR = "\x1b[38;5;223m"
SNOW_COLOR = "\x1b[97m"

LIGHT_COLORS = ["\x1b[91m", "\x1b[93m", "\x1b[95m", "\x1b[94m", "\x1b[96m", "\x1b[97m"]
ORN_COLORS = ["\x1b[33m", "\x1b[35m", "\x1b[36m", "\x1b[37m"]

GARLAND_ROWS = [3, 5, 7]
GARLAND_COLOR = "\x1b[38;5;214m"
GARLAND_CHAR = "="

STAR_CHAR = "★"

# ---------------- ASCII art ---------------- #

TREE = [
    "          *          ",
    "         ***         ",
    "        **.**        ",
    "       *******.      ",
    "      .*******..     ",
    "     ***********     ",
    "    **.*********.    ",
    "   ***************   ",
    "  .****************  ",
    " ******************* ",
    "        |||          ",
    "        |||          ",
]

HOUSE = [
    "        ________         ",
    "       /  ____  \\        ",
    "      /__/____\\__\\       ",
    "     /  /    \\  \\ \\      ",
    "    /__/      \\__\\_\\     ",
    "    |  ┌──┐  ┌──┐  |     ",
    "    |  │  │  │  │  |     ",
    "    |  └──┘  └──┘  |     ",
    "    |      ___     |     ",
    "    |     |   |    |     ",
    "    |_____|___|____|     ",
    "       /________\\        ",
]

# ---------------- helpers ---------------- #


def clear():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def move(y: int, x: int) -> None:
    sys.stdout.write(f"\x1b[{y};{x}H")


def term_size():
    try:
        s = shutil.get_terminal_size((100, 28))
        return s.columns, s.lines
    except Exception:
        return 100, 28


# ---------------- lyrics / LRC ---------------- #

LRC_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,2}))?\](.*)")


def parse_lrc(path: str):
    """Return a sorted list of (timestamp_seconds, text) from a .lrc file."""
    lines = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue

            m = LRC_RE.match(raw)
            if not m:
                continue

            mm, ss, cs, text = m.groups()
            base = int(mm) * 60 + int(ss)
            if cs:
                # [mm:ss.xx] or [mm:ss.x]
                if len(cs) == 1:
                    base += int(cs) / 10
                else:
                    base += int(cs) / 100

            lines.append((base, text.strip()))

    lines.sort(key=lambda x: x[0])
    return lines


def pick_current_next(lyrics, t):
    """Given elapsed 'track time' t, return (current_line, next_line)."""
    current = ""
    nxt = ""

    for i, (ts, line) in enumerate(lyrics):
        if ts <= t:
            current = line
            nxt = lyrics[i + 1][1] if i + 1 < len(lyrics) else ""
        else:
            break

    return current, nxt


# ---------------- audio ---------------- #


def maybe_play_audio(path: str):
    """
    Try to fire off the audio on Windows via os.startfile or winsound.

    If nothing works it just falls back to "no audio" mode and keeps the visuals.
    """
    if not path or not os.path.exists(path):
        input("Press Enter to start (no audio found)… ")
        return time.perf_counter()

    # Windows: let the OS deal with it
    if os.name == "nt":
        # Try default handler first (VLC, etc.)
        try:
            os.startfile(path)
            return time.perf_counter()
        except Exception:
            pass

        # If it's a .wav, winsound is easy
        if os.path.splitext(path)[1].lower() == ".wav":
            try:
                import winsound

                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return time.perf_counter()
            except Exception:
                pass

    # Fallback: just run visuals
    input("Press Enter to start (audio not supported here)… ")
    return time.perf_counter()


# ---------------- snow ---------------- #


class SnowField:
    """
    Minimal snow particle system confined to a rectangular region.
    """

    def __init__(self, rows, x0, x1, count):
        self.rows = rows
        self.x0 = x0
        self.x1 = x1
        self.width = max(1, x1 - x0)
        self.flakes = []
        self._spawn(count)

    def _spawn(self, count):
        self.flakes = []
        for _ in range(count):
            self.flakes.append(
                {
                    "x": random.uniform(self.x0, self.x1 - 1),
                    "y": random.uniform(0, self.rows - 1),
                    "v": random.uniform(0.12, 0.38),
                    "d": random.uniform(-0.10, 0.10),
                    "phase": random.uniform(0, math.tau),
                    "char": random.choice(".*+"),
                }
            )

    def step(self):
        for flake in self.flakes:
            flake["phase"] += 0.12
            flake["x"] += flake["d"] + 0.30 * math.sin(flake["phase"]) * 0.05
            flake["y"] += flake["v"]

            if flake["x"] < self.x0:
                flake["x"] += self.width
            elif flake["x"] >= self.x1:
                flake["x"] -= self.width

            if flake["y"] >= self.rows:
                flake["y"] = -1

    def draw(self, top_offset=0):
        for flake in self.flakes:
            y = int(flake["y"])
            if 0 <= y < self.rows:
                move(top_offset + 1 + y, 1 + int(flake["x"]))
                sys.stdout.write(DIM + flake["char"] + RESET)


# ---------------- drawing ---------------- #


def draw_house(ground_y, left):
    top = ground_y - len(HOUSE)
    for i, row in enumerate(HOUSE):
        move(top + i, left)
        sys.stdout.write(HOUSE_COLOR + row + RESET)


def draw_chimney_smoke(frame, ground_y, left):
    top = ground_y - len(HOUSE)
    # Manually eyeballed chimney tip
    tip_y = top + 2
    tip_x = left + len(HOUSE[0]) - 5

    phase = frame * 0.18
    for i in range(3):
        y = tip_y - i * 2 - int(phase % 2)
        x = tip_x + int(2 * math.sin(phase + i))
        if y >= 1:
            move(y, x)
            sys.stdout.write(DIM + "~" + RESET)


def draw_tree(frame, top, left, sway=0):
    # Replace the top "*" with a pulsing star
    head = list(TREE[0])
    mid = len(head) // 2
    star_color = PULSE_STAR_BRIGHT if (frame % 8) < 6 else PULSE_STAR_DIM
    head[mid] = star_color + STAR_CHAR + RESET

    rows = ["".join(head)] + TREE[1:]

    for r, row in enumerate(rows):
        move(top + r, left + sway)

        out = []
        for c, ch in enumerate(row):
            if ch == "*":
                # tree lights
                on = ((frame + r * 3 + c * 5) % 14) < 9
                color = random.choice(LIGHT_COLORS) if on else DIM
                out.append(color + "*" + RESET)
            elif ch == ".":
                # ornaments
                out.append(random.choice(ORN_COLORS) + "o" + RESET)
            elif ch == "|":
                # trunk
                out.append("\x1b[38;5;94m|\x1b[0m")
            else:
                out.append(ch)

        sys.stdout.write("".join(out))


def draw_garlands(frame, top, left, sway=0):
    speed = 0.45
    kx = 0.35
    threshold = 0.55

    for row_idx in GARLAND_ROWS:
        row = TREE[row_idx]
        move(top + row_idx, left + sway)

        out = []
        for c, ch in enumerate(row):
            if ch == " ":
                out.append(" ")
                continue

            wave = math.sin((c + frame * speed) * kx)
            if wave > threshold:
                out.append(GARLAND_COLOR + GARLAND_CHAR + RESET)
            else:
                out.append(ch)

        sys.stdout.write("".join(out))


def draw_ground_snow(scene_left, scene_right, ground_y):
    span = max(0, scene_right - scene_left - 1)
    if span <= 0:
        return

    drift = []
    for i in range(span):
        drift.append("_" if i % 2 else "~")

    move(ground_y, scene_left + 1)
    sys.stdout.write(SNOW_COLOR + "".join(drift) + RESET)


def draw_lyrics(cur, nxt, top, left, cols):
    max_width = max(20, cols - left - 2)

    move(top + 1, left)
    sys.stdout.write(LYRICS_COLOR + cur[:max_width] + RESET + " " * 5)

    move(top + 3, left)
    sys.stdout.write(DIM + nxt[:max_width] + RESET + " " * 5)


def progress_bar(t, total, width=44):
    if total <= 0:
        return ""
    p = max(0.0, min(1.0, t / total))
    filled = int(p * width)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {int(p * 100):3d}%"


# ---------------- main loop ---------------- #


def main():
    # lyrics file path
    lrc_path = sys.argv[1] if len(sys.argv) > 1 else "lyrics.lrc"
    if not os.path.exists(lrc_path):
        print("Usage: python tree_karaoke.py <lyrics.lrc>")
        sys.exit(1)

    lyrics = parse_lrc(lrc_path)
    if not lyrics:
        print("No timed lines found in the LRC.")
        sys.exit(1)

    clear()
    print("Starting in 3…")
    time.sleep(1)
    print("2…")
    time.sleep(1)
    print("1…")
    time.sleep(1)
    clear()

    start_t = maybe_play_audio(AUDIO_PATH)

    cols, lines = term_size()

    # Use a single ground line for house + tree
    scene_height = max(len(TREE), len(HOUSE))
    ground_y = SCENE_TOP + scene_height
    tree_top = ground_y - len(TREE)

    scene_left = SCENE_LEFT
    scene_right = max(scene_left + 30, min(LYRICS_OFFSET_X - 2, cols - 2))
    sky_rows = max(0, ground_y - 1)

    # Snow only over the scene (left side)
    back_snow = SnowField(
        rows=sky_rows,
        x0=scene_left,
        x1=scene_right,
        count=max(120, (scene_right - scene_left) * sky_rows // 60),
    )
    fore_snow = SnowField(
        rows=sky_rows,
        x0=scene_left,
        x1=scene_right,
        count=max(50, (scene_right - scene_left) * sky_rows // 110),
    )

    house_left = scene_left
    tree_left = house_left + 22

    total_track_time = lyrics[-1][0] + LYRIC_OFFSET

    frame = 0
    try:
        while True:
            now = time.perf_counter()
            elapsed = now - start_t

            # Apply lyric offset so lines match the audio
            lyric_time = max(0.0, elapsed - LYRIC_OFFSET)
            cur, nxt = pick_current_next(lyrics, lyric_time)

            # background snow
            back_snow.step()
            back_snow.draw(top_offset=0)

            # house
            draw_house(ground_y, house_left)
            draw_chimney_smoke(frame, ground_y, house_left)

            # tree
            sway = int(round(math.sin(frame * 0.18)))
            draw_tree(frame, tree_top, tree_left, sway=sway)
            draw_garlands(frame, tree_top, tree_left, sway=sway)

            # foreground snow in front of the scene
            fore_snow.step()
            fore_snow.draw(top_offset=0)

            # ground line
            draw_ground_snow(scene_left, scene_right, ground_y)

            # lyrics (clean area, no snow)
            draw_lyrics(cur, nxt, SCENE_TOP, LYRICS_OFFSET_X, cols)

            # simple progress bar, one row below ground
            move(ground_y + 1, scene_left)
            sys.stdout.write(DIM + progress_bar(elapsed, total_track_time) + RESET)

            sys.stdout.flush()
            time.sleep(1.0 / FPS)
            frame += 1

    except KeyboardInterrupt:
        move(lines, 1)
        print(RESET + "\nBye!")


if __name__ == "__main__":
    main()