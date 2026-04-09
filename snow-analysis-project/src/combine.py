"""Estimate snowmelt-related DOY values from classified time-series data."""

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

INPUT_SHP = "snowjudge.shp"
OUTPUT_SHP = "combined.shp"
TIME_SERIES_COLUMNS = [
    "19",
    "31",
    "43",
    "55",
    "67",
    "79",
    "91",
    "103",
    "115",
    "127",
    "139",
    "151",
    "163",
    "175",
    "187",
    "199",
]
SNOW_THRESHOLD = -20.79
DRY_THRESHOLD = -19.41
SECONDARY_THRESHOLD = -20.2


def main():
    """Run the original DOY estimation workflow."""
    yoshi = gpd.read_file(INPUT_SHP, encoding="utf-8")
    del yoshi["level_0"]
    yoshi = yoshi.reset_index()

    doy_list = []
    doy1_list = []

    for _, row in yoshi.iterrows():
        time_series_data = row[TIME_SERIES_COLUMNS].tolist()
        snowjudge = row["issnow"]

        if snowjudge == "snow":
            start_index = next((i for i, val in enumerate(time_series_data) if val < SNOW_THRESHOLD), None)
            end_index = None
            if start_index is not None:
                for i in range(start_index, len(time_series_data)):
                    if time_series_data[i] >= DRY_THRESHOLD:
                        end_index = i
                        break

            if end_index is not None:
                merged_array = np.where(
                    np.array(time_series_data[start_index : end_index + 1]) < SNOW_THRESHOLD, 0, 1
                )
                last_pair_indices = None
                for i in range(len(merged_array) - 1):
                    if merged_array[i] == 0 and merged_array[i + 1] == 1:
                        last_pair_indices = (i, i + 1)

                if last_pair_indices:
                    prev_column_index = start_index + last_pair_indices[0]
                    y_column_index = start_index + last_pair_indices[1]
                    prev_title = TIME_SERIES_COLUMNS[prev_column_index]
                    y_title = TIME_SERIES_COLUMNS[y_column_index]
                    prev_value = pd.to_numeric(time_series_data[prev_column_index], errors="coerce")
                    y_value = pd.to_numeric(time_series_data[y_column_index], errors="coerce")

                    model = LinearRegression()
                    X = np.array([float(prev_title), float(y_title)], dtype=np.float64).reshape(-1, 1)
                    y = np.nan_to_num(np.array([prev_value, y_value], dtype=np.float64))
                    model.fit(X, y)

                    x_for_target_y = (SNOW_THRESHOLD - model.intercept_) / model.coef_[0]
                    doy_list.append(x_for_target_y)
                else:
                    doy_list.append(None)

                for i in range(end_index, len(TIME_SERIES_COLUMNS) - 1):
                    col_0, col_1 = TIME_SERIES_COLUMNS[i], TIME_SERIES_COLUMNS[i + 1]
                    if time_series_data[i] > SECONDARY_THRESHOLD and time_series_data[i + 1] <= SECONDARY_THRESHOLD:
                        prev_value = pd.to_numeric(time_series_data[i], errors="coerce")
                        y_value = pd.to_numeric(time_series_data[i + 1], errors="coerce")

                        model = LinearRegression()
                        X = np.array([float(col_0), float(col_1)], dtype=np.float64).reshape(-1, 1)
                        y = np.nan_to_num(np.array([prev_value, y_value], dtype=np.float64))
                        model.fit(X, y)

                        x_for_target_y = (SECONDARY_THRESHOLD - model.intercept_) / model.coef_[0]
                        doy1_list.append(x_for_target_y)
                        break
                else:
                    doy1_list.append(None)
            else:
                doy_list.append(None)
                doy1_list.append(None)

        elif snowjudge == "nosnow":
            start_index = next((i for i, val in enumerate(time_series_data) if val >= DRY_THRESHOLD), None)

            if start_index is not None:
                merged_array = np.where(np.array(time_series_data[start_index:]) > SECONDARY_THRESHOLD, 0, 1)
                first_pair_indices = None
                for i in range(len(merged_array) - 1):
                    if merged_array[i] == 0 and merged_array[i + 1] == 1:
                        first_pair_indices = (i + start_index, i + 1 + start_index)
                        break

                if first_pair_indices:
                    prev_column_index, y_column_index = first_pair_indices[0], first_pair_indices[1]
                    prev_title = TIME_SERIES_COLUMNS[prev_column_index]
                    y_title = TIME_SERIES_COLUMNS[y_column_index]
                    prev_value = pd.to_numeric(time_series_data[prev_column_index], errors="coerce")
                    y_value = pd.to_numeric(time_series_data[y_column_index], errors="coerce")

                    model = LinearRegression()
                    X = np.array([float(prev_title), float(y_title)], dtype=np.float64).reshape(-1, 1)
                    y = np.nan_to_num(np.array([prev_value, y_value], dtype=np.float64))
                    model.fit(X, y)

                    x_for_target_y = (SECONDARY_THRESHOLD - model.intercept_) / model.coef_[0]
                    doy1_list.append(x_for_target_y)
                    doy_list.append(None)
                else:
                    doy1_list.append(None)
                    doy_list.append(None)
            else:
                doy1_list.append(None)
                doy_list.append(None)

    yoshi["DOY"] = doy_list
    yoshi["DOY1"] = doy1_list
    yoshi.to_file(OUTPUT_SHP, encoding="utf-8")


if __name__ == "__main__":
    main()
