"""
Event study visualization module using Plotly.
Generates interactive response curves across time horizons and surprise-vs-return scatter plots.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


class EventPlotter:
    """Produces publication-grade interactive figures for event response dynamics."""

    HORIZON_LABELS = {
        "return_5m": "5 Min",
        "return_15m": "15 Min",
        "return_1h": "1 Hour",
        "return_4h": "4 Hours",
        "return_1d": "1 Day",
        "return_3d": "3 Days",
        "return_5d": "5 Days",
        "event_to_next_fri_return": "Next Friday Close",
    }

    @classmethod
    def plot_response_trajectory(
        cls,
        events_df: pd.DataFrame,
        event_type: str,
        output_path: Optional[str] = None,
    ) -> go.Figure:
        """
        Plots the median response path and interquartile range from event time T to next Friday close.
        """
        sub = events_df[events_df["event_type"] == event_type].copy()
        cols = list(cls.HORIZON_LABELS.keys())
        available_cols = [c for c in cols if c in sub.columns]

        x_vals = [cls.HORIZON_LABELS[c] for c in available_cols]
        medians = [sub[c].median() * 100.0 for c in available_cols]
        q25 = [sub[c].quantile(0.25) * 100.0 for c in available_cols]
        q75 = [sub[c].quantile(0.75) * 100.0 for c in available_cols]

        fig = go.Figure()

        # Shaded IQR band
        fig.add_trace(go.Scatter(
            x=x_vals + x_vals[::-1],
            y=q75 + q25[::-1],
            fill="toself",
            fillcolor="rgba(218, 165, 32, 0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="Interquartile Range (25th-75th %)",
        ))

        # Median path line
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=medians,
            mode="lines+markers",
            line=dict(color="#D4AF37", width=3),
            marker=dict(size=8, color="#B8860B"),
            name="Median Response (%)",
        ))

        fig.add_hline(y=0.0, line_dash="dash", line_color="gray", opacity=0.7)

        fig.update_layout(
            title=f"Gold Response Path Following {event_type} (N={len(sub)})",
            xaxis_title="Time Elapsed Since Release",
            yaxis_title="Cumulative Return (%)",
            template="plotly_dark",
            hovermode="x unified",
            font=dict(family="Arial", size=12),
        )

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.write_html(output_path)

        return fig

    @classmethod
    def plot_surprise_vs_return_scatter(
        cls,
        events_df: pd.DataFrame,
        event_type: str,
        output_path: Optional[str] = None,
    ) -> go.Figure:
        """
        Plots standardized surprise Z-score vs Next Friday Return with OLS trendline.
        """
        sub = events_df[events_df["event_type"] == event_type].dropna(
            subset=["surprise_zscore", "event_to_next_fri_return"]
        ).copy()

        sub["weekly_return_pct"] = sub["event_to_next_fri_return"] * 100.0

        fig = px.scatter(
            sub,
            x="surprise_zscore",
            y="weekly_return_pct",
            color="reversal_classification" if "reversal_classification" in sub.columns else None,
            title=f"{event_type}: Surprise Z-Score vs Following Friday Gold Return",
            labels={
                "surprise_zscore": "Standardized Surprise (Z-Score)",
                "weekly_return_pct": "Gold Return to Next Friday (%)",
                "reversal_classification": "Reaction Type",
            },
            template="plotly_dark",
        )

        # Add OLS regression line via numpy
        if len(sub) > 2:
            x_vals = sub["surprise_zscore"].values
            y_vals = sub["weekly_return_pct"].values
            valid_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
            x_clean = x_vals[valid_mask]
            y_clean = y_vals[valid_mask]
            if len(x_clean) > 2 and np.std(x_clean) > 1e-6:
                try:
                    slope, intercept = np.polyfit(x_clean, y_clean, 1)
                    x_range = np.linspace(x_clean.min(), x_clean.max(), 50)
                    y_fit = slope * x_range + intercept
                    fig.add_trace(go.Scatter(
                        x=x_range,
                        y=y_fit,
                        mode="lines",
                        name=f"OLS Trend (Slope: {slope:+.2f})",
                        line=dict(color="#00CED1", dash="solid", width=2),
                    ))
                except Exception:
                    pass

        fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.write_html(output_path)

        return fig
