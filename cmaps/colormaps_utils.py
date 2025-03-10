import numpy as np
import cv2

frame = np.load('frame.npy')

frame -= frame.min()
frame /= frame.max()
frame = (np.clip(frame, 0, 1)*255).astype(np.uint8)
colormaps = [
            ('JET', cv2.COLORMAP_JET),
            ('HOT', cv2.COLORMAP_HOT),
            ('INFERNO', cv2.COLORMAP_INFERNO),
            ('PLASMA', cv2.COLORMAP_PLASMA),
            ('VIRIDIS', cv2.COLORMAP_VIRIDIS),
            ('MAGMA', cv2.COLORMAP_MAGMA),
            ('RAINBOW', cv2.COLORMAP_RAINBOW),
            ('BONE', cv2.COLORMAP_BONE),
        ]

cv2.imwrite("NO_MAP.png", frame)

for cmap_name, thermal_colormap in colormaps:
    _frame = cv2.applyColorMap(frame, thermal_colormap)
    filename = cmap_name + ".png"
    cv2.imwrite(filename, _frame)
