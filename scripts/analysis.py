"""Precipitation & temperature analysis.

Reads data/raw/weather_daily.csv, cleans it, computes monthly/annual
statistics and writes figures to figures/ and a summary table to data/processed/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "weather_daily.csv"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"

BLUE, RED, GREY = "#2b6cb0", "#c53030", "#718096"


def load() -> pd.DataFrame:
    df = pd.read_csv(RAW, parse_dates=["date"]).set_index("date")
    # Fill short gaps: temperature by interpolation, precipitation as 0
    df["t_mean_c"] = df["t_mean_c"].interpolate(limit=3)
    df["precip_mm"] = df["precip_mm"].fillna(0)
    return df


def climatogram(df: pd.DataFrame) -> pd.DataFrame:
    """Long-term monthly mean temperature and mean monthly precipitation sum."""
    monthly = df.resample("MS").agg({"t_mean_c": "mean", "precip_mm": "sum"})
    clim = monthly.groupby(monthly.index.month).mean()
    clim.index.name = "month"

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    ax1.bar(clim.index, clim["precip_mm"], color=BLUE, alpha=0.75, label="Precipitation")
    ax1.set_ylabel("Precipitation (mm/month)", color=BLUE)
    ax1.set_xticks(range(1, 13), months)
    ax2 = ax1.twinx()
    ax2.plot(clim.index, clim["t_mean_c"], color=RED, marker="o", lw=2, label="Temperature")
    ax2.set_ylabel("Mean temperature (°C)", color=RED)
    ax1.set_title("Climatogram 2015–2024 (synthetic station VIE_SYNTH_01)")
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "climatogram.png", dpi=150)
    plt.close(fig)
    return clim.round(1)


def annual_trends(df: pd.DataFrame) -> pd.DataFrame:
    annual = df.resample("YS").agg({"t_mean_c": "mean", "precip_mm": "sum"})
    annual.index = annual.index.year
    annual.index.name = "year"

    x = annual.index.to_numpy()
    slope_t, icpt_t = np.polyfit(x, annual["t_mean_c"], 1)
    slope_p, _ = np.polyfit(x, annual["precip_mm"], 1)

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    axes[0].plot(x, annual["t_mean_c"], color=RED, marker="o")
    axes[0].plot(x, slope_t * x + icpt_t, color=GREY, ls="--",
                 label=f"Trend: {slope_t * 10:+.2f} °C/decade")
    axes[0].set_ylabel("Mean temp. (°C)")
    axes[0].legend(frameon=False)
    axes[1].bar(x, annual["precip_mm"], color=BLUE, alpha=0.75)
    axes[1].set_ylabel("Precipitation (mm/yr)")
    axes[1].set_title(f"Trend: {slope_p * 10:+.0f} mm/decade", fontsize=9, loc="left")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Annual mean temperature and precipitation")
    fig.tight_layout()
    fig.savefig(FIG / "annual_trends.png", dpi=150)
    plt.close(fig)
    return annual.round(1)


def temp_vs_precip(df: pd.DataFrame) -> float:
    """Relationship between monthly temperature and monthly precipitation."""
    monthly = df.resample("MS").agg({"t_mean_c": "mean", "precip_mm": "sum"}).dropna()
    r = monthly["t_mean_c"].corr(monthly["precip_mm"], method="spearman")

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(monthly["t_mean_c"], monthly["precip_mm"], s=18, color=BLUE, alpha=0.6)
    ax.set_xlabel("Monthly mean temperature (°C)")
    ax.set_ylabel("Monthly precipitation (mm)")
    ax.set_title(f"Temperature vs. precipitation (Spearman ρ = {r:.2f})")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "temp_vs_precip.png", dpi=150)
    plt.close(fig)
    return r


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    df = load()

    clim = climatogram(df)
    annual = annual_trends(df)
    r = temp_vs_precip(df)

    clim.to_csv(PROC / "monthly_climatology.csv")
    annual.to_csv(PROC / "annual_summary.csv")

    wet_days = (df["precip_mm"] >= 1).resample("YS").sum().mean()
    print("=== Summary ===")
    print(f"Period:                 {df.index.min():%Y-%m-%d} – {df.index.max():%Y-%m-%d}")
    print(f"Mean annual temp.:      {annual['t_mean_c'].mean():.1f} °C")
    print(f"Mean annual precip.:    {annual['precip_mm'].mean():.0f} mm")
    print(f"Wet days (≥1 mm)/year:  {wet_days:.0f}")
    print(f"Wettest month (clim.):  {clim['precip_mm'].idxmax()}")
    print(f"Spearman ρ (T vs P):    {r:.2f}")


if __name__ == "__main__":
    main()
