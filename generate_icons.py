"""Generate simple placeholder icons for the Stream Deck plugin."""
import struct
import zlib
import os

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "com.streamdeckscripts.sdPlugin")


def create_png(width, height, r, g, b):
    """Create a minimal solid-color PNG with a centered circle."""
    # Build raw RGBA pixel data
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


def save_icon(path, size, r, g, b):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(create_png(size, size, r, g, b))
    print(f"  Created {path} ({size}x{size})")


if __name__ == '__main__':
    icons = PLUGIN_DIR + "/imgs"

    # Plugin category icon
    save_icon(f"{icons}/plugin/icon.png", 256, 100, 120, 200)
    save_icon(f"{icons}/plugin/icon@2x.png", 512, 100, 120, 200)

    # Mic unmuted (green)
    save_icon(f"{icons}/actions/mic-mute/unmuted.png", 72, 100, 200, 100)
    save_icon(f"{icons}/actions/mic-mute/unmuted@2x.png", 144, 100, 200, 100)

    # Mic muted (red)
    save_icon(f"{icons}/actions/mic-mute/muted.png", 72, 220, 80, 80)
    save_icon(f"{icons}/actions/mic-mute/muted@2x.png", 144, 220, 80, 80)

    # Script runner (blue)
    save_icon(f"{icons}/actions/script-runner/icon.png", 72, 80, 140, 220)
    save_icon(f"{icons}/actions/script-runner/icon@2x.png", 144, 80, 140, 220)

    print("Done!")
