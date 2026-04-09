"""Aggregate parcel-level DOY values into municipal averages."""

import geopandas as gpd
import pandas as pd

INPUT_SHP = "doy.shp"
GROUP_COLUMN = "N03_007"
TARGET_COLUMN = "DOY"
OUTPUT_COLUMN = "judge"


def predict():
    """Update the shapefile with municipality-level mean DOY values."""
    doy_data = gpd.read_file(INPUT_SHP, encoding="cp932")
    doy_data[TARGET_COLUMN] = pd.to_numeric(doy_data[TARGET_COLUMN], errors="coerce")

    if doy_data[TARGET_COLUMN].isnull().any():
        raise ValueError("DOY column contains missing values.")

    grouped = doy_data.groupby(GROUP_COLUMN)[TARGET_COLUMN].mean().reset_index()

    if OUTPUT_COLUMN in doy_data.columns:
        doy_data.drop(columns=OUTPUT_COLUMN, inplace=True)

    doy_data = doy_data.merge(grouped, on=GROUP_COLUMN, suffixes=("", "_average"))
    doy_data.rename(columns={f"{TARGET_COLUMN}_average": OUTPUT_COLUMN}, inplace=True)
    doy_data.to_file(INPUT_SHP, encoding="cp932", driver="ESRI Shapefile")


if __name__ == "__main__":
    predict()
