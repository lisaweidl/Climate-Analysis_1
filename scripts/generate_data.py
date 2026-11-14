"""Generate a synthetic daily weather dataset (temperature + precipitation).

The data is fictional but follows a realistic Central-European seasonal cycle
(roughly modelled on Vienna). Run once to (re)create data/raw/weather_daily.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "weather_daily.csv"


def main() -> None:
    rng = np.random.default_rng(SEED)
    dates = pd.date_range("2015-01-01", "2024-12-31", freq="D")
    doy = dates.dayofyear.to_numpy()
    years = dates.year.to_numpy() - 2015

    # Temperature: seasonal sine + warming trend (~0.05 °C/yr) + AR(1) noise
    seasonal = 10.8 + 10.5 * np.sin(2 * np.pi * (doy - 110) / 365.25)
    noise = np.zeros(len(dates))
    for i in range(1, len(dates)):
        noise[i] = 0.7 * noise[i - 1] + rng.normal(0, 1.8)
    t_mean = seasonal + 0.05 * years + noise
    t_max = t_mean + rng.uniform(3, 7, len(dates))
    t_min = t_mean - rng.uniform(3, 6, len(dates))

    # Precipitation: wet-day probability + gamma amounts, summer peak
    p_wet = 0.33 + 0.05 * np.sin(2 * np.pi * (doy - 100) / 365.25)
    wet = rng.random(len(dates)) < p_wet
    scale = 6.5 + 3.0 * np.sin(2 * np.pi * (doy - 110) / 365.25)
    precip = np.where(wet, rng.gamma(0.8, scale), 0.0)

    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "station": "VIE_SYNTH_01",
        "t_mean_c": t_mean.round(1),
        "t_min_c": t_min.round(1),
        "t_max_c": t_max.round(1),
        "precip_mm": precip.round(1),
    })

    # A few missing values to make cleaning realistic
    for col in ["t_mean_c", "precip_mm"]:
        idx = rng.choice(len(df), size=15, replace=False)
        df.loc[idx, col] = np.nan

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} rows to {OUT}")


if __name__ == "__main__":
    main()
