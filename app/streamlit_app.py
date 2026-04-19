from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Regional Bank Peer Dashboard",
    page_icon="🏦",
    layout="wide",
)


DATA_PATH = Path("data/processed/fdic_scored.csv")


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.replace("data.", "") for col in df.columns]

    if "REPDTE" in df.columns:
        raw_rep = df["REPDTE"].copy()
        df["REPDTE"] = pd.to_datetime(df["REPDTE"], errors="coerce")
        if df["REPDTE"].isna().all():
            df["REPDTE"] = pd.to_datetime(
                raw_rep.astype(str), format="%Y%m%d", errors="coerce"
            )

    numeric_cols = [
        "ASSET",
        "DEP",
        "LNLSNET",
        "EQ",
        "NETINC",
        "ROA",
        "ROE",
        "loan_to_deposit",
        "equity_to_assets",
        "roa_calc",
        "roe_calc",
        "composite_score",
        "composite_rank",
        "score_rolling_4q",
        "rolling_4q_rank",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["ROA", "ROE", "roa_calc", "roe_calc", "equity_to_assets"]:
        if col in df.columns:
            df[f"{col}_pct_display"] = df[col] * 100

    if "ASSET" in df.columns:
        df["assets_bil"] = df["ASSET"] / 1_000_000

    return df


def latest_available_date(df: pd.DataFrame) -> pd.Timestamp:
    return df["REPDTE"].dropna().max()


def format_billions(series: pd.Series) -> pd.Series:
    return (series / 1_000_000).round(1)


def build_latest_table(df: pd.DataFrame, as_of_date: pd.Timestamp) -> pd.DataFrame:
    latest_df = df[df["REPDTE"] == as_of_date].copy()

    cols = [
        "Ticker",
        "Holding_Company_Name",
        "Primary_Bank_Sub_Name",
        "composite_rank",
        "composite_score",
        "rolling_4q_rank",
        "score_rolling_4q",
        "roa_calc",
        "roe_calc",
        "equity_to_assets",
        "loan_to_deposit",
        "ASSET",
    ]
    cols = [c for c in cols if c in latest_df.columns]
    latest_df = latest_df[cols].sort_values("composite_rank")

    rename_map = {
        "Holding_Company_Name": "Holding Company",
        "Primary_Bank_Sub_Name": "Primary Bank",
        "composite_rank": "Rank",
        "composite_score": "Score",
        "rolling_4q_rank": "Rolling 4Q Rank",
        "score_rolling_4q": "Rolling 4Q Score",
        "roa_calc": "ROA (%)",
        "roe_calc": "ROE (%)",
        "equity_to_assets": "Equity / Assets (%)",
        "loan_to_deposit": "Loan / Deposit",
    }
    latest_df = latest_df.rename(columns=rename_map)

    if "Score" in latest_df.columns:
        latest_df["Score"] = latest_df["Score"].round(3)
    if "Rolling 4Q Score" in latest_df.columns:
        latest_df["Rolling 4Q Score"] = latest_df["Rolling 4Q Score"].round(3)

    for col in ["ROA (%)", "ROE (%)", "Equity / Assets (%)"]:
        if col in latest_df.columns:
            latest_df[col] = (latest_df[col] * 100).round(2)

    if "Loan / Deposit" in latest_df.columns:
        latest_df["Loan / Deposit"] = latest_df["Loan / Deposit"].round(2)

    if "ASSET" in latest_df.columns:
        latest_df["Assets ($bn)"] = format_billions(latest_df["ASSET"])
        latest_df = latest_df.drop(columns=["ASSET"])

    for col in ["Rank", "Rolling 4Q Rank"]:
        if col in latest_df.columns:
            latest_df[col] = latest_df[col].round(0).astype("Int64")

    return latest_df


def build_component_table(bank_snapshot: pd.DataFrame) -> pd.DataFrame:
    component_map = [
        ("ROA percentile", "roa_calc_pct", 0.4),
        ("ROE percentile", "roe_calc_pct", 0.3),
        ("Equity / Assets percentile", "equity_to_assets_pct", 0.2),
        ("Loan / Deposit percentile", "loan_to_deposit_pct", 0.1),
    ]

    rows = []
    for label, col, weight in component_map:
        if col in bank_snapshot.columns:
            raw_value = bank_snapshot.iloc[0][col]
            weighted_value = raw_value * weight if pd.notna(raw_value) else np.nan
            rows.append(
                {
                    "Component": label,
                    "Percentile": round(raw_value, 3) if pd.notna(raw_value) else np.nan,
                    "Weight": weight,
                    "Weighted Contribution": round(weighted_value, 3) if pd.notna(weighted_value) else np.nan,
                }
            )

    return pd.DataFrame(rows)


def main() -> None:
    st.title("Regional Bank Peer Dashboard")
    st.caption("FDIC-based peer comparison dashboard for IAT regional bank constituents")

    if not DATA_PATH.exists():
        st.error(f"Data file not found: {DATA_PATH}")
        st.stop()

    df = load_data(DATA_PATH)

    if df.empty:
        st.error("Dataset is empty.")
        st.stop()

    if "REPDTE" not in df.columns or df["REPDTE"].isna().all():
        st.error("REPDTE column is missing or could not be parsed.")
        st.stop()

    available_dates = sorted(df["REPDTE"].dropna().unique())
    available_tickers = sorted(df["Ticker"].dropna().unique()) if "Ticker" in df.columns else []

    st.sidebar.header("Filters")
    selected_date = st.sidebar.selectbox(
        "Reporting date",
        options=available_dates,
        index=len(available_dates) - 1,
        format_func=lambda x: pd.Timestamp(x).strftime("%Y-%m-%d"),
    )
    selected_tickers = st.sidebar.multiselect(
        "Tickers",
        options=available_tickers,
        default=available_tickers,
    )
    show_n = st.sidebar.slider("Rows in ranking table", min_value=5, max_value=31, value=15)
    sort_view = st.sidebar.radio("Ranking view", options=["Top", "Bottom"], horizontal=True)

    filtered_df = df[df["Ticker"].isin(selected_tickers)].copy() if selected_tickers else df.copy()
    snapshot_df = filtered_df[filtered_df["REPDTE"] == selected_date].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Banks in view", f"{snapshot_df['Ticker'].nunique()}")
    c2.metric("Reporting date", pd.Timestamp(selected_date).strftime("%Y-%m-%d"))
    if "composite_score" in snapshot_df.columns:
        c3.metric("Average score", f"{snapshot_df['composite_score'].mean():.3f}")
    if "score_rolling_4q" in snapshot_df.columns:
        c4.metric("Average rolling 4Q score", f"{snapshot_df['score_rolling_4q'].mean():.3f}")
    elif "roa_calc" in snapshot_df.columns:
        c4.metric("Average ROA", f"{snapshot_df['roa_calc'].mean() * 100:.2f}%")

    st.subheader("Latest peer ranking snapshot")
    score_view = st.radio(
        "Score view",
        options=["Composite score", "Rolling 4Q score"] if "score_rolling_4q" in snapshot_df.columns else ["Composite score"],
        horizontal=True,
    )

    latest_table = build_latest_table(filtered_df, selected_date)
    if sort_view == "Top":
        if score_view == "Rolling 4Q score" and "Rolling 4Q Rank" in latest_table.columns:
            latest_table = latest_table.sort_values("Rolling 4Q Rank", ascending=True).head(show_n)
        else:
            latest_table = latest_table.sort_values("Rank", ascending=True).head(show_n)
    else:
        if score_view == "Rolling 4Q score" and "Rolling 4Q Rank" in latest_table.columns:
            latest_table = latest_table.sort_values("Rolling 4Q Rank", ascending=False).head(show_n)
        else:
            latest_table = latest_table.sort_values("Rank", ascending=False).head(show_n)
    st.dataframe(latest_table, use_container_width=True, hide_index=True)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Score ranking")
        if not snapshot_df.empty and {"Ticker", "composite_score"}.issubset(snapshot_df.columns):
            rank_y = "score_rolling_4q" if score_view == "Rolling 4Q score" and "score_rolling_4q" in snapshot_df.columns else "composite_score"
            rank_chart_df = snapshot_df.sort_values(rank_y, ascending=False)
            fig_rank = px.bar(
                rank_chart_df,
                x="Ticker",
                y=rank_y,
                hover_data=[c for c in ["Holding_Company_Name", "composite_rank", "rolling_4q_rank"] if c in rank_chart_df.columns],
            )
            fig_rank.update_layout(
                xaxis_title="Ticker",
                yaxis_title=score_view,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info("Score columns not available.")

    with chart_col2:
        st.subheader("ROA vs Equity / Assets")
        needed = {"roa_calc_pct_display", "equity_to_assets_pct_display", "Ticker"}
        if not snapshot_df.empty and needed.issubset(snapshot_df.columns):
            scatter_df = snapshot_df.copy()
            scatter_df["asset_size"] = np.sqrt(scatter_df["ASSET"].clip(lower=1)) if "ASSET" in scatter_df.columns else 1
            hover_cols = [c for c in ["Holding_Company_Name", "composite_score", "score_rolling_4q"] if c in scatter_df.columns]
            fig_scatter = px.scatter(
                scatter_df,
                x="equity_to_assets_pct_display",
                y="roa_calc_pct_display",
                text="Ticker",
                size="asset_size",
                hover_data=hover_cols,
            )
            fig_scatter.update_traces(textposition="top center")
            fig_scatter.update_layout(
                xaxis_title="Equity / Assets (%)",
                yaxis_title="ROA (%)",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Required columns for the scatter plot are not available.")

    st.subheader("Score component breakdown")
    score_component_col1, score_component_col2 = st.columns([1, 2])

    with score_component_col1:
        component_bank = st.selectbox(
            "Select bank for score breakdown",
            options=available_tickers,
            key="component_bank",
        )
        component_snapshot = snapshot_df[snapshot_df["Ticker"] == component_bank].copy()

        if not component_snapshot.empty:
            component_table = build_component_table(component_snapshot)
            st.dataframe(component_table, use_container_width=True, hide_index=True)

            if "composite_score" in component_snapshot.columns:
                st.metric(
                    "Composite score",
                    f"{component_snapshot.iloc[0]['composite_score']:.3f}",
                )
            if "score_rolling_4q" in component_snapshot.columns and pd.notna(component_snapshot.iloc[0]["score_rolling_4q"]):
                st.metric(
                    "Rolling 4Q score",
                    f"{component_snapshot.iloc[0]['score_rolling_4q']:.3f}",
                )
        else:
            st.info("No snapshot data available for the selected bank.")

    with score_component_col2:
        if not component_snapshot.empty:
            component_table = build_component_table(component_snapshot)
            if not component_table.empty:
                fig_component = px.bar(
                    component_table,
                    x="Component",
                    y="Weighted Contribution",
                    hover_data=["Percentile", "Weight"],
                    title=f"{component_bank} Score Contribution Breakdown",
                )
                fig_component.update_layout(
                    xaxis_title="Score component",
                    yaxis_title="Weighted contribution",
                    xaxis_tickangle=-20,
                )
                st.plotly_chart(fig_component, use_container_width=True)
            else:
                st.info("Score component columns are not available in the dataset.")
        else:
            st.info("No score component data available.")

    st.subheader("Bank history")
    selected_bank = st.selectbox("Select bank", options=available_tickers)
    bank_df = filtered_df[filtered_df["Ticker"] == selected_bank].sort_values("REPDTE").copy()

    hist_col1, hist_col2 = st.columns(2)

    with hist_col1:
        history_score_options = ["composite_score"]
        if "score_rolling_4q" in bank_df.columns:
            history_score_options.append("score_rolling_4q")

        if {"REPDTE", "composite_score"}.issubset(bank_df.columns):
            score_label_map = {
                "composite_score": "Composite score",
                "score_rolling_4q": "Rolling 4Q score",
            }
            selected_score_series = st.radio(
                "Score history view",
                options=history_score_options,
                format_func=lambda x: score_label_map.get(x, x),
                horizontal=True,
            )
            fig_hist_score = px.line(
                bank_df,
                x="REPDTE",
                y=selected_score_series,
                title=f"{selected_bank} {score_label_map.get(selected_score_series, selected_score_series)} Over Time",
            )
            fig_hist_score.update_layout(
                xaxis_title="Reporting date",
                yaxis_title=score_label_map.get(selected_score_series, selected_score_series),
            )
            st.plotly_chart(fig_hist_score, use_container_width=True)
        else:
            st.info("Composite score history unavailable.")

    with hist_col2:
        if {"REPDTE", "roa_calc", "loan_to_deposit"}.issubset(bank_df.columns):
            metric_labels = {
                "roa_calc_pct_display": "ROA (%)",
                "loan_to_deposit": "Loan / Deposit",
                "equity_to_assets_pct_display": "Equity / Assets (%)",
                "roe_calc_pct_display": "ROE (%)",
            }
            metric_choice = st.radio(
                "Bank history metric",
                options=list(metric_labels.keys()),
                format_func=lambda x: metric_labels[x],
                horizontal=True,
            )
            fig_hist_metric = px.line(
                bank_df,
                x="REPDTE",
                y=metric_choice,
                title=f"{selected_bank} {metric_labels[metric_choice]} Over Time",
            )
            fig_hist_metric.update_layout(
                xaxis_title="Reporting date",
                yaxis_title=metric_labels[metric_choice],
            )
            st.plotly_chart(fig_hist_metric, use_container_width=True)
        else:
            st.info("Selected metric history unavailable.")

    st.subheader("Peer comparison")

    peer_col1, peer_col2 = st.columns(2)

    with peer_col1:
        focus_bank = st.selectbox(
            "Select focus bank",
            options=available_tickers,
            key="focus_bank",
        )

    with peer_col2:
        peer_banks = st.multiselect(
            "Select peers",
            options=[t for t in available_tickers if t != focus_bank],
            default=[t for t in available_tickers if t != focus_bank][:4],
            key="peer_banks",
        )

    compare_tickers = [focus_bank] + peer_banks
    compare_df = snapshot_df[snapshot_df["Ticker"].isin(compare_tickers)].copy()
    compare_df["is_focus"] = compare_df["Ticker"] == focus_bank

    metric_options = {
        "ROA (%)": "roa_calc_pct_display",
        "ROE (%)": "roe_calc_pct_display",
        "Equity / Assets (%)": "equity_to_assets_pct_display",
        "Loan / Deposit": "loan_to_deposit",
        "Composite Score": "composite_score",
        "Rolling 4Q Score": "score_rolling_4q",
    }
    available_metric_options = {
        label: col for label, col in metric_options.items() if col in compare_df.columns
    }

    selected_metric = st.radio(
        "Comparison metric",
        options=list(available_metric_options.keys()),
        horizontal=True,
        key="peer_metric_choice",
    )
    metric_col = available_metric_options[selected_metric]

    if not compare_df.empty:
        compare_df = compare_df.sort_values(metric_col, ascending=False)
        fig_peer = px.bar(
            compare_df,
            x="Ticker",
            y=metric_col,
            color="is_focus",
            hover_data=[c for c in ["Holding_Company_Name"] if c in compare_df.columns],
            color_discrete_map={True: "red", False: "gray"},
            title=f"{selected_metric} comparison",
        )
        fig_peer.update_layout(showlegend=False)
        st.plotly_chart(fig_peer, use_container_width=True)
    else:
        st.info("No peer snapshot data available for the selected date.")

    compare_hist_df = filtered_df[filtered_df["Ticker"].isin(compare_tickers)].copy()
    if not compare_hist_df.empty:
        history_metric = "score_rolling_4q" if "score_rolling_4q" in compare_hist_df.columns else "composite_score"
        history_label = "Rolling 4Q Score" if history_metric == "score_rolling_4q" else "Composite Score"
        fig_ts = px.line(
            compare_hist_df,
            x="REPDTE",
            y=history_metric,
            color="Ticker",
            title=f"{history_label} comparison over time",
        )
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("No peer history data available.")

    with st.expander("Data notes"):
        st.markdown(
            """
            - Source data: FDIC financial history pulled by primary FDIC certificate.
            - Composite score is based on peer-relative percentile scoring.
            - Rolling 4Q score reflects a trailing four-quarter average score.
            - Loan-to-deposit is directionally inverted in scoring so lower values rank better.
            - The latest ranking table reflects the selected reporting date only.
            """
        )


if __name__ == "__main__":
    main()
