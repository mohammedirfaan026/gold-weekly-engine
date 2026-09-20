"""
Report generation pipeline script.
Assembles all statistical tables, regime matrices, and visual charts into comprehensive
Markdown and styled HTML quantitative research reports.
Usage:
    python generate_report.py
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.reporting.generator import ResearchReportGenerator


def convert_markdown_to_html(md_content: str, output_html_path: str):
    """
    Renders clean, styled dark-theme HTML report with embedded responsive tables and typography.
    """
    # Simple HTML generator wrapping the report
    import html
    
    # Process basic markdown headers and tables into HTML
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "<title>Gold Weekly Response Engine - Quantitative Research Report</title>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; "
        "background-color: #121212; color: #E0E0E0; line-height: 1.6; margin: 0; padding: 40px; }",
        ".container { max-width: 1200px; margin: 0 auto; background: #1E1E1E; padding: 40px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }",
        "h1 { color: #D4AF37; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; }",
        "h2 { color: #F0E68C; margin-top: 30px; border-bottom: 1px solid #333; padding-bottom: 8px; }",
        "h3 { color: #00CED1; }",
        "table { width: 100%; border-collapse: collapse; margin: 20px 0; background: #252525; border-radius: 4px; overflow: hidden; }",
        "th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #333; }",
        "th { background-color: #2D2D2D; color: #D4AF37; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }",
        "tr:hover { background-color: #2A2A2A; }",
        "code { background: #333; color: #00FF7F; padding: 2px 6px; border-radius: 3px; font-family: 'Consolas', monospace; font-size: 13px; }",
        ".chart-link { display: inline-block; margin: 10px 10px 10px 0; padding: 8px 16px; background: #D4AF37; color: #000; text-decoration: none; border-radius: 4px; font-weight: bold; }",
        ".chart-link:hover { background: #FFD700; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class='container'>",
    ]

    # Parse markdown blocks
    in_table = False
    table_rows = []

    for line in md_content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("|") and trimmed.endswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(trimmed)
            continue
        else:
            if in_table:
                # Render table
                html_lines.append("<table>")
                # First row header
                headers = [h.strip() for h in table_rows[0].split("|")[1:-1]]
                html_lines.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>")
                html_lines.append("<tbody>")
                for r in table_rows[2:]:  # Skip delimiter row
                    cols = [c.strip() for c in r.split("|")[1:-1]]
                    html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cols) + "</tr>")
                html_lines.append("</tbody></table>")
                in_table = False

        if trimmed.startswith("# "):
            html_lines.append(f"<h1>{trimmed[2:]}</h1>")
        elif trimmed.startswith("## "):
            html_lines.append(f"<h2>{trimmed[3:]}</h2>")
        elif trimmed.startswith("### "):
            html_lines.append(f"<h3>{trimmed[4:]}</h3>")
        elif trimmed.startswith("---"):
            html_lines.append("<hr style='border: 0; height: 1px; background: #333; margin: 30px 0;'>")
        elif trimmed:
            html_lines.append(f"<p>{trimmed}</p>")

    # Add interactive charts gallery link section
    html_lines.append("<h2>Interactive Charts & Visual Explorations</h2>")
    html_lines.append("<p>Access standalone interactive Plotly visualizations generated during analysis:</p>")
    html_lines.append("<a class='chart-link' href='figures/weekly_macro_dashboard.html' target='_blank'>Weekly Macro Dashboard</a>")
    html_lines.append("<a class='chart-link' href='figures/trajectory_cpi.html' target='_blank'>CPI Response Trajectory</a>")
    html_lines.append("<a class='chart-link' href='figures/heatmap_real_yield_cpi.html' target='_blank'>CPI x Real Yield Matrix</a>")
    html_lines.append("<a class='chart-link' href='figures/trajectory_fomc_rate_decision.html' target='_blank'>FOMC Response Path</a>")

    html_lines.append("</div>")
    html_lines.append("</body></html>")

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))


def main():
    print("=== Generating Quantitative Research Reports ===")
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    # Load summary CSVs with fallback handling
    def safe_load(path):
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

    study_df = safe_load("reports/event_study_summary.csv")
    surprise_df = safe_load("reports/surprise_bucket_study.csv")
    asym_df = safe_load("reports/directional_asymmetry_study.csv")
    speed_df = safe_load("reports/speed_study.csv")
    reversal_df = safe_load("reports/reversal_study.csv")
    shock_df = safe_load("reports/market_shocks_study.csv")
    pos_df = safe_load("reports/positioning_study.csv")
    etf_df = safe_load("reports/etf_flows_study.csv")

    weekly_file = "data/weekly/gold_weekly_master.parquet"
    weekly_master_df = pd.read_parquet(weekly_file) if os.path.exists(weekly_file) else pd.DataFrame()

    report_gen = ResearchReportGenerator(reports_dir=reports_dir)
    md_content = report_gen.generate_full_report(
        event_study_df=study_df,
        surprise_df=surprise_df,
        asymmetry_df=asym_df,
        speed_df=speed_df,
        reversal_df=reversal_df,
        shock_df=shock_df,
        positioning_df=pos_df,
        etf_df=etf_df,
        weekly_master_df=weekly_master_df,
    )

    # Generate styled HTML
    html_path = os.path.join(reports_dir, "gold_weekly_research_report.html")
    convert_markdown_to_html(md_content, html_path)

    print(f"  [OK] Markdown report generated: reports/gold_weekly_research_report.md")
    print(f"  [OK] Styled HTML report generated: {html_path}")
    print("\n=== Report Generation Complete! ===")


if __name__ == "__main__":
    main()
