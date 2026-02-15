"""Generate icons for the Stream Deck plugin."""

import math
import os
import struct
import zlib

from PIL import Image, ImageDraw

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "com.streamdeckscripts.sdPlugin")


# -- Simple circle icons (stdlib only) --------------------------------------

def create_png(width, height, r, g, b):
    """Create a minimal solid-color PNG with a centered circle."""
    pixels = []
    cx, cy = width // 2, height // 2
    radius = min(width, height) // 2 - 2
    for y in range(height):
        row = b'\x00'  # filter byte
        for x in range(width):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= radius * radius:
                row += struct.pack('BBBB', r, g, b, 255)
            else:
                row += struct.pack('BBBB', 0, 0, 0, 0)
        pixels.append(row)
    raw = b''.join(pixels)

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    compressed = zlib.compress(raw)
    return sig + make_chunk(b'IHDR', ihdr) + make_chunk(b'IDAT', compressed) + make_chunk(b'IEND', b'')


def save_circle(path, size, r, g, b):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(create_png(size, size, r, g, b))
    print(f"  Created {path} ({size}x{size})")


# -- Speaker icons (Pillow, supersampled for smooth edges) -------------------

SUPERSAMPLE = 4
DISCORD_BLUE = (88, 101, 242, 255)  # #5865F2


def draw_speaker(draw, size, color, offset_x=0, offset_y=0):
    """Draw a classic speaker icon."""
    s = size
    ox, oy = offset_x, offset_y

    # Speaker body (rectangle)
    body_l = int(s * 0.18) + ox
    body_r = int(s * 0.28) + ox
    body_t = int(s * 0.38) + oy
    body_b = int(s * 0.62) + oy
    draw.rectangle([body_l, body_t, body_r, body_b], fill=color)

    # Speaker cone (trapezoid)
    cone = [
        (body_r, body_t),
        (int(s * 0.42) + ox, int(s * 0.22) + oy),
        (int(s * 0.42) + ox, int(s * 0.78) + oy),
        (body_r, body_b),
    ]
    draw.polygon(cone, fill=color)


def draw_sound_waves(draw, size, color, offset_x=0, offset_y=0):
    """Draw three sound wave arcs to the right of the speaker."""
    s = size
    w = max(2, int(s * 0.035))
    cx = int(s * 0.46) + offset_x
    cy = s // 2 + offset_y

    for r in [int(s * 0.10), int(s * 0.17), int(s * 0.24)]:
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=-40, end=40, fill=color, width=w)


def draw_reset_arrow(draw, size, color):
    """Draw a small circular reset arrow in the bottom-right corner."""
    s = size
    w = max(2, int(s * 0.03))
    cx = int(s * 0.78)
    cy = int(s * 0.78)
    r = int(s * 0.13)

    draw.arc([cx - r, cy - r, cx + r, cy + r], start=-30, end=280, fill=color, width=w)

    angle = math.radians(-30)
    tip_x = cx + r * math.cos(angle)
    tip_y = cy + r * math.sin(angle)
    arrow_size = int(s * 0.06)
    arrow = [
        (tip_x, tip_y),
        (tip_x - arrow_size * 1.5, tip_y - arrow_size * 0.3),
        (tip_x - arrow_size * 0.3, tip_y + arrow_size * 1.5),
    ]
    draw.polygon(arrow, fill=color)


def create_speaker_icon(size, status):
    """Create a speaker icon on Discord blue background (supersampled)."""
    ss = size * SUPERSAMPLE
    img = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-rect background
    pad = max(1, int(ss * 0.04))
    radius = int(ss * 0.18)
    draw.rounded_rectangle([pad, pad, ss - pad, ss - pad], radius=radius, fill=DISCORD_BLUE)

    # Shift speaker up-left to make room for reset badge
    ox = int(ss * -0.04)
    oy = int(ss * -0.06)

    if status == "ok":
        color = (255, 255, 255, 255)
        draw_speaker(draw, ss, color, ox, oy)
        draw_sound_waves(draw, ss, color, ox, oy)
        draw_reset_arrow(draw, ss, (200, 210, 255, 180))
    else:
        color = (240, 80, 80, 255)
        draw_speaker(draw, ss, color, ox, oy)
        draw_reset_arrow(draw, ss, (255, 180, 180, 200))

    # Downsample with LANCZOS for smooth anti-aliased edges
    return img.resize((size, size), Image.LANCZOS)


def save_speaker_icon(path, size, status):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = create_speaker_icon(size, status)
    img.save(path, "PNG")
    print(f"  Created {path} ({size}x{size})")


# -- Main -------------------------------------------------------------------

if __name__ == '__main__':
    icons = PLUGIN_DIR + "/imgs"

    # Plugin category icon
    save_circle(f"{icons}/plugin/icon.png", 256, 100, 120, 200)
    save_circle(f"{icons}/plugin/icon@2x.png", 512, 100, 120, 200)

    # Mic unmuted (green)
    save_circle(f"{icons}/actions/mic-mute/unmuted.png", 72, 100, 200, 100)
    save_circle(f"{icons}/actions/mic-mute/unmuted@2x.png", 144, 100, 200, 100)

    # Mic muted (red)
    save_circle(f"{icons}/actions/mic-mute/muted.png", 72, 220, 80, 80)
    save_circle(f"{icons}/actions/mic-mute/muted@2x.png", 144, 220, 80, 80)

    # Script runner (blue)
    save_circle(f"{icons}/actions/script-runner/icon.png", 72, 80, 140, 220)
    save_circle(f"{icons}/actions/script-runner/icon@2x.png", 144, 80, 140, 220)

    # Audio status OK (speaker + waves)
    save_speaker_icon(f"{icons}/actions/audio-status/ok.png", 72, "ok")
    save_speaker_icon(f"{icons}/actions/audio-status/ok@2x.png", 144, "ok")

    # Audio status error (speaker, no waves)
    save_speaker_icon(f"{icons}/actions/audio-status/error.png", 72, "error")
    save_speaker_icon(f"{icons}/actions/audio-status/error@2x.png", 144, "error")

    print("Done!")
