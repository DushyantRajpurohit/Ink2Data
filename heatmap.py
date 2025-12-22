import cv2
import numpy as np

def draw_confidence_heatmap(image_path, elements):
    img = cv2.imread(image_path)

    for el in elements:
        box = el["box"]
        conf = el["confidence"]

        # color mapping
        if conf > 0.85:
            color = (0, 255, 0)
        elif conf > 0.7:
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)

        pts = [
            (int(box[0]), int(box[1])),
            (int(box[2]), int(box[3])),
            (int(box[4]), int(box[5])),
            (int(box[6]), int(box[7])),
        ]

        for i in range(4):
            cv2.line(img, pts[i], pts[(i + 1) % 4], color, 2)

    return img
