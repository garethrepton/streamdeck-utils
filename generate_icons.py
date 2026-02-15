"""Generate icons for the Stream Deck plugin."""

import os
import struct
import zlib

from PIL import Image, ImageDraw, ImageFilter

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
    """Draw a speaker cone shape with gently rounded edges."""
    s = size
    ox, oy = offset_x, offset_y
    cy = s // 2 + oy

    # Speaker body (well-rounded rectangle)
    body_l = int(s * 0.14) + ox
    body_r = int(s * 0.28) + ox
    body_t = int(s * 0.30) + oy
    body_b = int(s * 0.70) + oy
    body_h = body_b - body_t
    r = body_h // 3
    draw.rounded_rectangle([body_l, body_t, body_r, body_b], radius=r, fill=color)

    # Speaker cone (curved pieslice — tall but compact)
    cone_reach = int(s * 0.40) + ox
    cone_r = cone_reach - body_r
    draw.pieslice(
        [body_r - cone_r, cy - cone_r, body_r + cone_r, cy + cone_r],
        start=-48, end=48, fill=color,
    )


def draw_sound_waves(draw, size, color, offset_x=0, offset_y=0):
    """Draw two sound wave arcs to the right of the speaker."""
    s = size
    w = max(2, int(s * 0.035))
    cx = int(s * 0.48) + offset_x
    cy = s // 2 + offset_y

    r1 = int(s * 0.10)
    draw.arc([cx - r1, cy - r1, cx + r1, cy + r1], start=-40, end=40, fill=color, width=w)

    r2 = int(s * 0.17)
    draw.arc([cx - r2, cy - r2, cx + r2, cy + r2], start=-40, end=40, fill=color, width=w)

    r3 = int(s * 0.24)
    draw.arc([cx - r3, cy - r3, cx + r3, cy + r3], start=-40, end=40, fill=color, width=w)


def draw_reset_arrow(draw, size, color):
    """Draw a small circular reset arrow in the bottom-right corner."""
    s = size
    w = max(2, int(s * 0.03))
    cx = int(s * 0.78)
    cy = int(s * 0.78)
    r = int(s * 0.13)

    # Circular arc (270 degrees, leaving a gap at top-right for the arrowhead)
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=-30, end=280, fill=color, width=w)

    # Arrowhead at the gap (pointing clockwise, at the ~-30 degree position)
    import math
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

    # Draw speaker + waves on a separate layer, then blur for soft edges
    speaker = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    sd = ImageDraw.Draw(speaker)

    if status == "ok":
        color = (255, 255, 255, 255)
        draw_speaker(sd, ss, color, ox, oy)
        draw_sound_waves(sd, ss, color, ox, oy)
    else:
        color = (240, 80, 80, 255)
        draw_speaker(sd, ss, color, ox, oy)

    # Gentle blur softens all edges
    speaker = speaker.filter(ImageFilter.GaussianBlur(radius=ss * 0.008))
    img = Image.alpha_composite(img, speaker)

    # Reset arrow drawn after blur so it stays crisp
    arrow_draw = ImageDraw.Draw(img)
    if status == "ok":
        draw_reset_arrow(arrow_draw, ss, (200, 210, 255, 180))
    else:
        draw_reset_arrow(arrow_draw, ss, (255, 180, 180, 200))

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

    # Audio status OK (speaker + checkmark, green)
    save_speaker_icon(f"{icons}/actions/audio-status/ok.png", 72, "ok")
    save_speaker_icon(f"{icons}/actions/audio-status/ok@2x.png", 144, "ok")

    # Audio status error (speaker + cross, red)
    save_speaker_icon(f"{icons}/actions/audio-status/error.png", 72, "error")
    save_speaker_icon(f"{icons}/actions/audio-status/error@2x.png", 144, "error")

    print("Done!")
