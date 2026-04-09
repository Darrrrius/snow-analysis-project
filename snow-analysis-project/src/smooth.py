# -*- coding: utf-8 -*-
"""Smooth parcel-level SAR backscatter features for downstream snow analysis."""

import math
import re
from statistics import stdev

import geopandas as gpd
import numpy as np
import pandas as pd

INPUT_SHP = "hiroshima.shp"
INTERMEDIATE_SHP = "smooth2021.shp"
OUTPUT_SHP = "smooth.shp"

RAW_TIME_COLUMNS = [
    "0107_media",
    "0119_media",
    "0131_media",
    "0212_media",
    "0224_media",
    "0308_media",
    "0320_media",
    "0401_media",
    "0413_media",
    "0425_media",
    "0507_media",
    "0519_media",
    "0531_media",
    "0612_media",
    "0624_media",
    "0706_media",
    "0718_media",
    "0730_media",
    "0811_media",
    "0823_media",
    "0904_media",
    "0916_media",
    "0928_media",
    "1010_media",
]

SMOOTHED_TIME_COLUMNS = [
    "0119smo",
    "0131smo",
    "0212smo",
    "0224smo",
    "0308smo",
    "0320smo",
    "0401smo",
    "0413smo",
    "0425smo",
    "0507smo",
    "0519smo",
    "0531smo",
    "0612smo",
    "0624smo",
    "0706smo",
    "0718smo",
    "0730smo",
    "0811smo",
    "0823smo",
    "0904smo",
    "0916smo",
    "0928smo",
]

RAW_TIME_INDEX = pd.Series(
    [
        20210107,
        20210119,
        20210131,
        20210212,
        20210224,
        20210308,
        20210320,
        20210401,
        20210413,
        20210425,
        20210507,
        20210519,
        20210531,
        20210612,
        20210624,
        20210706,
        20210718,
        20210730,
        20210811,
        20210823,
        20210904,
        20210916,
        20210928,
        20211010,
    ]
)

CONVERTED_RAW_TIME_INDEX = pd.to_datetime(RAW_TIME_INDEX, format="%Y%m%d")


def convert_coordinates(geometry, index):
    """Convert WKT polygon coordinates into a numeric point list."""
    print(index)
    print(geometry.wkt)
    try:
        stripped = re.sub(r"(^[^(]*\(*\)*|\(*\)*)", "", geometry.wkt)
    except Exception:
        print(geometry.wkt)
        return None
    print(stripped)
    return [[float(value) for value in pair.strip().split(" ")] for pair in stripped.split(",")]


def main():
    """Run the original smoothing workflow with clearer configuration."""
    yoshi = gpd.read_file(INPUT_SHP, encoding="utf-8")
    yoshi = yoshi.dropna(axis=0, how="any")
    yoshi = yoshi.reset_index()

    yoshi_points = yoshi["geometry"]
    print(yoshi_points)

    max_angles = []
    min_angles = []

    for i in range(0, len(yoshi_points)):
        coordinates = convert_coordinates(yoshi_points[i], i)
        try:
            point = len(coordinates)
        except Exception:
            continue

        if not point:
            continue

        stdev_x1 = []
        stdev_y1 = []

        for k in range(0, 13):
            angle = k * 15
            rot = np.array(
                [
                    [math.cos(math.radians(angle)), math.sin(math.radians(angle))],
                    [(-1) * math.sin(math.radians(angle)), math.cos(math.radians(angle))],
                ]
            )
            x_values = []
            y_values = []

            for j in range(0, point):
                coordinates_c = coordinates[j]
                coordinates_xy = coordinates_c[0:2]
                coord_array = np.array(coordinates_xy)
                rotated = np.dot(rot, coord_array).tolist()
                x_values += [rotated[0]]
                y_values += [rotated[1]]

                if j == point - 1:
                    stdev_x1 += [stdev(x_values)]
                    max_x1 = max(stdev_x1)
                    min_x1 = min(stdev_x1)
                    stdev_y1 += [stdev(y_values)]
                    max_y1 = max(stdev_y1)
                    min_y1 = min(stdev_y1)
                else:
                    pass

            if k == 12:
                max_angle = 15 * (stdev_x1.index(max_x1))
                max_angles += [max_angle]
                min_angle = 15 * (stdev_x1.index(min_x1))
                min_angles += [min_angle]
                _ = max_y1, min_y1
            else:
                pass

    yoshi["max_angle"] = max_angles
    yoshi["min_angle"] = min_angles
    print(yoshi)
    yoshi.to_file(INTERMEDIATE_SHP, encoding="utf-8")

    yoshi = gpd.read_file(INTERMEDIATE_SHP, encoding="utf-8")
    yoshi = yoshi.dropna(axis=0, how="any")
    yoshi = yoshi.reset_index()

    kari_A = pd.concat([yoshi[column] for column in RAW_TIME_COLUMNS], axis=1)
    kari_A = kari_A.reset_index()
    kari_A = kari_A.drop("index", axis=1)
    print(kari_A)

    smoothed_values = [[] for _ in range(len(SMOOTHED_TIME_COLUMNS))]

    for i in range(0, len(kari_A)):
        row = kari_A.loc[i]
        row.index = CONVERTED_RAW_TIME_INDEX
        row_values = row.values.tolist()

        # Keep the original weighted moving-average logic unchanged.
        for j in range(0, 23):
            if j == 0 or j == 23:
                pass
            else:
                prev_value = row_values[j - 1]
                current_value = row_values[j]
                next_value = row_values[j + 1]
                smoothed = (prev_value / 4) + (current_value / 2) + (next_value / 4)
                smoothed_values[j - 1] += [smoothed]

    for column_name, values in zip(SMOOTHED_TIME_COLUMNS, smoothed_values):
        yoshi[column_name] = values

    print(yoshi)
    yoshi.to_file(OUTPUT_SHP, encoding="utf-8")


if __name__ == "__main__":
    main()
