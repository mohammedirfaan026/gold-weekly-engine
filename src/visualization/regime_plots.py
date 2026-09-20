"""
Regime and conditional response visualization module using Plotly.
Renders 2D conditional matrix heatmaps and regime-stratified comparison charts.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go


class RegimePlotter:
    """Produces heatmaps and regime breakdown charts for conditional gold behavior."""

    @classmethod
    def plot_conditional_matrix_heatmap(
        cls,
        matrix_dict: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> go.Figure:
        """
        Plots an interactive annotated heatmap for a 2D conditional response matrix.
        """
        median_df = matrix_dict.get("median_matrix", pd.DataFrame())
        count_df = matrix_dict.get("count_matrix", pd.DataFrame())
        event_name = matrix_dict.get("event_type", "Macro Event")
        regime_var = matrix_dict.get("regime_variable", "Regime")

        if median_df.empty:
            return go.Figure()

        # Multiply returns by 100 for display
        z_vals = (median_df * 100.0).values
        x_labels = [str(c).title() for c in median_df.columns]
        y_labels = [str(r).replace("_", " ").title() for r in median_df.index]

        # Annotations text
        text_matrix = []
        for i in range(len(median_df.index)):
            row_text = []
            for j in range(len(median_df.columns)):
                val = z_vals[i, j]
                count = count_df.iloc[i, j] if not count_df.empty else 0
                if pd.notna(val):
                    row_text.append(f"{val:+.2f}%<br>(N={count})")
                else:
                    row_text.append(f"N/A<br>(N=0)")
            text_matrix.append(row_text)

        fig = go.Figure(data=go.Heatmap(
            z=z_vals,
            x=x_labels,
            y=y_labels,
            text=text_matrix,
            texttemplate="%{text}",
            textfont=dict(size=12, color="white"),
            colorscale="RdYlGn",
            zmid=0.0,
            colorbar=dict(title="Median Return (%)"),
        ))

        fig.update_layout(
            title=f"Conditional Weekly Gold Response: {event_name} by {regime_var.replace('regime_', '').title()}",
            xaxis_title=f"{regime_var.replace('regime_', '').title()} Regime",
            yaxis_title="Surprise Size Bucket",
            template="plotly_dark",
            height=450,
        )

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.write_html(output_path)

        return fig
