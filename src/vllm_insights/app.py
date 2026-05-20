"""Streamlit dashboard. Run: streamlit run src/vllm_insights/app.py"""
import streamlit as st
import pandas as pd
import plotly.express as px

from .config import load_settings
from .analyzer.queries import (
    releases_df,
    release_sections_df,
    prs_df,
    commits_df,
    pr_tech_distribution,
    merge_time_stats,
)

st.set_page_config(page_title="vLLM Insights", layout="wide")

settings = load_settings(require_token=False)
db = settings.db_path

st.title("vLLM GitHub Insights")
st.caption(f"Repo: `{settings.repo}` · DB: `{db}`")

tab_rel, tab_pr, tab_tech, tab_commit = st.tabs(
    ["Releases", "PR flow", "Tech areas", "Commits"]
)

# ---------- Releases ----------
with tab_rel:
    rel = releases_df(db)
    if rel.empty:
        st.info("No releases synced yet. Run `vllm-insights sync --releases` first.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total releases", len(rel))
        median_interval = rel["interval_days"].dropna().median()
        c2.metric("Median interval (days)", f"{median_interval:.1f}" if pd.notna(median_interval) else "—")
        c3.metric("Latest", rel.iloc[-1]["tag"])

        fig = px.scatter(
            rel.dropna(subset=["interval_days"]),
            x="published_at", y="interval_days", hover_data=["tag"],
            title="Release cadence (days between releases)",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Release notes — sections")
        sec = release_sections_df(db)
        if not sec.empty:
            tag = st.selectbox("Pick a release", rel["tag"].iloc[::-1].tolist())
            sub = sec[sec["tag"] == tag]
            for s in sub["section"].unique():
                with st.expander(s, expanded=False):
                    for item in sub[sub["section"] == s]["item"]:
                        st.markdown(f"- {item}")

            # PRs attributed to this release
            all_prs = prs_df(db)
            if not all_prs.empty and "release_tag" in all_prs.columns:
                rel_prs = all_prs[all_prs["release_tag"] == tag]
                with st.expander(f"PRs in {tag} ({len(rel_prs)})", expanded=False):
                    st.dataframe(
                        rel_prs[["number", "title", "author", "merged_at", "url"]]
                        .sort_values("merged_at"),
                        use_container_width=True, height=400,
                    )

# ---------- PR ----------
with tab_pr:
    prs = prs_df(db)
    if prs.empty:
        st.info("No PRs synced yet.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total PRs", len(prs))
        c2.metric("Merged", int((prs["state"] == "MERGED").sum()))
        c3.metric("Open", int((prs["state"] == "OPEN").sum()))
        med = prs["merge_hours"].dropna().median()
        c4.metric("Median merge time (h)", f"{med:.1f}" if pd.notna(med) else "—")

        st.subheader("Monthly merge time")
        stats = merge_time_stats(prs)
        if not stats.empty:
            fig = px.line(stats, x="month", y="median", markers=True,
                          title="Median PR merge time per month (hours)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("PR volume by month")
        v = prs.copy()
        v["month"] = v["created_at"].dt.to_period("M").astype(str)
        vol = v.groupby(["month", "state"]).size().reset_index(name="count")
        fig2 = px.bar(vol, x="month", y="count", color="state", title="PRs created per month")
        st.plotly_chart(fig2, use_container_width=True)

# ---------- Tech ----------
with tab_tech:
    df = pr_tech_distribution(db)
    if df.empty:
        st.info("No PR data.")
    else:
        since = st.date_input("Since", value=pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=180))
        d = df[df["created_at"] >= pd.Timestamp(since, tz="UTC")]
        dist = d.groupby("tech").size().reset_index(name="count").sort_values("count", ascending=False)
        st.plotly_chart(
            px.bar(dist, x="tech", y="count", title=f"PR distribution by tech area (since {since})"),
            use_container_width=True,
        )
        st.dataframe(
            d[["number", "title", "tech", "state", "author", "merge_hours", "url"]]
            .sort_values("number", ascending=False),
            use_container_width=True, height=400,
        )

# ---------- Commits ----------
with tab_commit:
    cm = commits_df(db)
    if cm.empty:
        st.info("No commits synced yet.")
    else:
        cm["week"] = cm["committed_at"].dt.to_period("W").astype(str)
        weekly = cm.groupby("week").size().reset_index(name="commits")
        st.plotly_chart(px.line(weekly, x="week", y="commits", title="Commits per week"),
                        use_container_width=True)

        top = cm.groupby("author").size().reset_index(name="commits").sort_values("commits", ascending=False).head(20)
        st.plotly_chart(px.bar(top, x="author", y="commits", title="Top 20 committers"),
                        use_container_width=True)
