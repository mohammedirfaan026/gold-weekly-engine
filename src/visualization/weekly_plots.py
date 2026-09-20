"""
Weekly macro dashboard visualization module.
Plots multi-asset weekly dynamics, COT positioning cycles, and ETF flows alongside Gold.
"""

from __future__ import annotations
import os
from typing import Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class WeeklyPlotter:
    """Produces multi-panel macro and positioning charts."""

    @classmethod
    def plot_macro_overview(
        cls,
        weekly_df: pd.DataFrame,
        output_path: Optional[str] = None,
    ) -> go.Figure:
        """
        Builds a 3-panel dashboard:
        Panel 1: Gold Price & 52-week High
        Panel 2: 10Y TIPS Real Yield & DXY
        Panel 3: COT Net Speculative Positioning & Percentile
        """
        df = weekly_df.copy().sort_values(by="week_ending")
        dates = pd.to_datetime(df["week_ending"])

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            subplot_titles=(
                "Gold Weekly Close (USD/oz)",
                "Macro Drivers: 10Y TIPS Real Yield (%) vs DXY Index",
                "CFTC COMEX Gold Net Speculative Positioning (Contracts)",
            ),
        )

        # Panel 1: Gold Price
        fig.add_trace(
            go.Scatter(x=dates, y=df["close"], name="Gold Close", line=dict(color="#D4AF37", width=2)),
            row=1, col=1,
        )

        # Panel 2: Real Yields (Left) & DXY (Right)
        if "real_yield_10y" in df.columns:
            fig.add_trace(
                go.Scatter(x=dates, y=df["real_yield_10y"], name="10Y Real Yield (%)", line=dict(color="#00CED1")),
                row=2, col=1,
            )
        if "dxy_close" in df.columns:
            fig.add_trace(
                go.Scatter(x=dates, y=df["dxy_close"], name="DXY Index", line=dict(color="#FF8C00")),
                row=2, col=1,
            )

        # Panel 3: COT Positioning
        if "net_spec_position" in df.columns:
            colors = np.where(df["net_spec_position"] >= 0, "rgba(46, 204, 113, 0.6)", "rgba(231, 76, 60, 0.6)")
            fig.add_trace(
                go.Bar(x=dates, y=df["net_spec_position"], name="COT Net Spec", marker_color=colors),
                row=3, col=1,
            )

        fig.update_layout(
            height=850,
            template="plotly_dark",
            title="Gold Weekly Response Engine - Macroeconomic & Positioning Dashboard",
            showlegend=True,
        )

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.write_html(output_path)

        return fig
