# -*- coding: utf-8 -*-
"""Classify each parcel as snow or non-snow from smoothed SAR values."""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INPUT_SHP = "smooth.shp"
OUTPUT_SHP = "snowjudge.shp"
OUTPUT_FIGURE = "smooth_judge_snow.jpg"
TIME_SERIES_COLUMNS = ["0119smo", "0131smo", "0212smo", "0224smo", "0308smo", "0320smo"]
SNOW_THRESHOLD = -20.79


def predict():
    """Add an `issnow` label to each parcel."""
    yoshi = gpd.read_file(INPUT_SHP, encoding="cp932")
    del yoshi["level_0"]
    yoshi = yoshi.reset_index()

    yoshi_A = pd.concat([yoshi[column] for column in TIME_SERIES_COLUMNS], axis=1)

    rorn = []
    for i in range(0, len(yoshi_A)):
        series = yoshi_A.loc[i]
        min_A = np.nanmin(series)
        if min_A < SNOW_THRESHOLD:
            rorn += [1.0]
        else:
            rorn += [2.0]

    labels = ["snow" if judge == 1.0 else "nosnow" for judge in rorn]
    yoshi["issnow"] = labels
    yoshi.to_file(OUTPUT_SHP, encoding="utf-8")


def show_graph():
    """Plot the snow classification result."""
    isrice_graph = gpd.read_file(OUTPUT_SHP, encoding="utf-8")
    fig, ax = plt.subplots(1, 1)
    isrice_graph.plot(column="issnow", ax=ax, legend=True)
    fig.savefig(OUTPUT_FIGURE)
    plt.show()
    print("done")


if __name__ == "__main__":
    predict()
    show_graph()
