#!/usr/bin/env python3
"""
Builds the line-layout images used by the dashboard's layout panel.

    python3 tools/make_layout_assets.py      (needs Pillow, numpy, scipy)

Input : assets/layout/line_layout_source.png
Output: assets/layout/base.png            - the layout (compressed)
        assets/layout/point_<A..F>.png    - transparent overlays, same size as base,
                                            with that point's stations highlighted
Then run tools/build_views.py, which embeds these PNGs into the view.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "assets", "layout")

HIGHLIGHT = (255, 183, 51)    # amber fill
TEXT = (90, 40, 0)            # station label colour on the highlight
OUTLINE = (230, 81, 0)        # dark orange outline

# Station centres (x, y) in the source image.
STATIONS = {
    "110A": (1322, 94), "110B": (1250, 265),
    "120A": (1172, 92), "120B": (1026, 80),
    "125A": (1104, 255), "125B": (950, 255),
    "130A": (872, 94), "130B": (802, 265), "130C": (728, 94),
    "140A": (648, 255), "140B": (575, 80), "140C": (501, 252),
    "Q": (280, 142),
}
R = 30   # grey pieces within this distance of the centre belong to the station
YELLOW_Q = (1128, 174, 1183, 227)   # bbox of the yellow "Q" diamond

POINTS = {
    "A": ["110A", "110B"],
    "B": ["120A", "120B"],
    "C": ["130A", "130B", "130C"],
    "D": ["140A", "140B", "140C"],
    "E": ["125A", "125B"],
    "F": ["Q", "YELLOW_Q"],
}


def main():
    src = Image.open(os.path.join(DIR, "line_layout_source.png")).convert("RGB")
    a = np.array(src).astype(int)
    grey = (np.abs(a - [242, 242, 242]).sum(2) <= 12) | (np.abs(a - [217, 217, 217]).sum(2) <= 12)
    lab, _ = ndimage.label(grey)

    masks = {}
    for name, (x, y) in STATIONS.items():
        # the box may be cut into pieces by the dotted lines: merge them all
        ids = set(lab[y - R:y + R, x - R:x + R].ravel()) - {0}
        comp = np.isin(lab, list(ids))
        comp = ndimage.binary_closing(comp, iterations=4)
        masks[name] = ndimage.binary_fill_holes(comp)
    x0, y0, x1, y1 = YELLOW_Q
    yq = np.zeros(grey.shape, bool)
    yq[y0:y1, x0:x1] = (a[y0:y1, x0:x1] < 240).any(2)
    ql, _ = ndimage.label(yq)
    sizes = ndimage.sum(yq, ql, range(1, ql.max() + 1))
    masks["YELLOW_Q"] = ndimage.binary_fill_holes(ql == (int(np.argmax(sizes)) + 1))

    src.quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(
        os.path.join(DIR, "base.png"), optimize=True)

    hl = np.array(HIGHLIGHT)
    for point, names in POINTS.items():
        m = np.zeros(grey.shape, bool)
        for n in names:
            m |= masks[n]
        edge = ndimage.binary_dilation(m, iterations=3) & ~m
        out = np.zeros(a.shape[:2] + (4,), np.uint8)
        out[m, :3] = hl
        out[m, 3] = 255
        # the station text (and dotted lines) inside the box: draw them dark so they read on amber
        inner = ndimage.binary_erosion(m, iterations=4)
        ink = inner & (a.min(2) < 236)
        out[ink, :3] = TEXT
        out[edge, :3] = OUTLINE
        out[edge, 3] = 255
        Image.fromarray(out, "RGBA").save(os.path.join(DIR, "point_%s.png" % point), optimize=True)

    for f in sorted(os.listdir(DIR)):
        print(f, os.path.getsize(os.path.join(DIR, f)))


if __name__ == "__main__":
    main()
