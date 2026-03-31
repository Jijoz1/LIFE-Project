# ─────────────────────────────────────────────────────────────
#  LIFE Project M&E — Streamlit Dashboard
#  streamlit_app.py
#
#  HOW TO RUN:
#  1. pip install streamlit plotly pandas
#  2. Edit SHEET_ID in config.py
#  3. Publish your Google Sheet to web (File → Share → Publish to web)
#  4. streamlit run streamlit_app.py
#  5. Opens at http://localhost:8501
#
#  TO DEPLOY ONLINE (free):
#  1. Push to GitHub
#  2. Go to share.streamlit.io
#  3. Connect your repo → deploy
# ─────────────────────────────────────────────────────────────

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import (
    load_data, TARGETS, INDICATOR_LABELS, COLOURS, CLUSTER_LABELS,
    pct_achieved, scorecard_colour, aggregate_quarterly
)

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="LIFE Project — M&E Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F5F5F5; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #e0e0e0;
        margin-bottom: 8px;
    }
    .metric-label { font-size: 11px; color: #888; margin-bottom: 2px; }
    .metric-value { font-size: 26px; font-weight: 600; line-height: 1.1; }
    .metric-target { font-size: 11px; color: #aaa; margin-top: 2px; }
    .badge-green  { background:#D8EFD9; color:#1F5C2E; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:600; }
    .badge-amber  { background:#FFF3E0; color:#E65100; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:600; }
    .badge-red    { background:#FFEBEE; color:#C62828; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:600; }
    h1 { color: #1F5C2E !important; }
    h2 { color: #2E7D32 !important; }
    h3 { color: #333 !important; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; }
    .stTabs [aria-selected="true"] { color: #1F5C2E !important; border-bottom-color: #1F5C2E !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1F5C2E/FFFFFF?text=AIM+LIFE+Project",
             use_container_width=True)
    st.markdown("### Filters")

    cluster_options = ["All clusters"] + list(CLUSTER_LABELS.values())
    selected_cluster = st.selectbox("Cluster", cluster_options)

    year_options = ["All years", "Year 1", "Year 2", "Year 3"]
    selected_year = st.selectbox("Project year", year_options)

    quarter_options = ["All quarters", "Q1 Nov–Jan", "Q2 Feb–Apr", "Q3 May–Jul", "Q4 Aug–Oct"]
    selected_quarter = st.selectbox("Quarter", quarter_options)

    st.divider()
    st.markdown("**Data source**")
    st.markdown("LIFE Project – M&E Data Hub")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("**Key contacts**")
    st.markdown("M&E Officer: George Sembereka")
    st.markdown("gsembereka@agriimpactmalawi.org")

# ── Load data ─────────────────────────────────────────────────
@st.cache_data(ttl=300)  # cache for 5 minutes
def get_data():
    return load_data()

with st.spinner("Loading data from Google Sheets..."):
    data = get_data()

q_df = data.get("quarterly", pd.DataFrame())
w_df = data.get("weekly", pd.DataFrame())
m_df = data.get("monthly", pd.DataFrame())

# ── Apply filters ─────────────────────────────────────────────
def apply_filters(df):
    if df.empty:
        return df
    filtered = df.copy()
    if selected_cluster != "All clusters" and "cluster_label" in filtered.columns:
        filtered = filtered[filtered["cluster_label"] == selected_cluster]
    if selected_year != "All years" and "project_year" in filtered.columns:
        yr_map = {"Year 1":"y1","Year 2":"y2","Year 3":"y3"}
        filtered = filtered[filtered["project_year"] == yr_map[selected_year]]
    if selected_quarter != "All quarters" and "report_quarter" in filtered.columns:
        q_map = {"Q1 Nov–Jan":"q1","Q2 Feb–Apr":"q2","Q3 May–Jul":"q3","Q4 Aug–Oct":"q4"}
        filtered = filtered[filtered["report_quarter"] == q_map[selected_quarter]]
    return filtered

q_filtered = apply_filters(q_df)
w_filtered = apply_filters(w_df)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style='background:#1F5C2E;padding:14px 20px;border-radius:8px;margin-bottom:16px'>
  <span style='color:white;font-size:20px;font-weight:600'>LIFE Project — M&E Dashboard</span>
  <span style='color:#9FE1CB;font-size:13px;margin-left:16px'>Agri-Impact Malawi  |  Egmont Trust  |  T/A Chadza, Lilongwe Rural</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Project Overview",
    "🌾 Obj 1: Market Production",
    "🏡 Obj 2: HH Resilience",
    "💰 Obj 3: Financial Inclusion",
    "📋 Weekly Activity Feed",
])

# ══════════════════════════════════════════════════════════════
# TAB 1: PROJECT OVERVIEW
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Key indicator scorecards")

    def make_scorecard(label, value, target, unit="", fmt=None):
        pct = pct_achieved(value, target)
        colour = scorecard_colour(pct)
        if fmt == "millions":
            disp = f"MWK {value/1_000_000:.1f}M"
            tgt_disp = f"MWK {target/1_000_000:.0f}M"
        elif unit == "%":
            disp = f"{value:.1f}%"
            tgt_disp = f"{target}%"
        else:
            disp = f"{int(value):,}"
            tgt_disp = f"{target:,}{' '+unit if unit else ''}"

        badge_cls = "badge-green" if pct >= 100 else ("badge-amber" if pct >= 70 else "badge-red")
        badge_txt = "On target" if pct >= 100 else ("In progress" if pct >= 70 else "Behind")

        bar_w = min(100, pct)
        bar_col = COLOURS["green_dark"] if pct >= 100 else (COLOURS["amber"] if pct >= 70 else COLOURS["red"])

        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>{label}</div>
          <div class='metric-value' style='color:{colour}'>{disp}</div>
          <div class='metric-target'>Target: {tgt_disp} &nbsp;<span class='{badge_cls}'>{badge_txt} {pct:.0f}%</span></div>
          <div style='height:4px;background:#eee;border-radius:2px;margin-top:6px'>
            <div style='width:{bar_w}%;height:100%;background:{bar_col};border-radius:2px'></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    cols = st.columns(6)
    scorecards = [
        ("Producer groups",        "pg_registered",          50,          ""),
        ("HH soybean seed",         "hh_seed_cum",            200,         "HH"),
        ("Ha irrigated",            "ha_irrigated",           10,          "ha"),
        ("Off-taker agreements",    "offtaker_agreements",    5,           ""),
        ("% structured sales",      "pct_produce_structured", 70,          "%"),
        ("Revenue",                 "revenue_cum_mwk",        200_000_000, ""),
        ("Functional gardens",      "hh_functional_gardens",  500,         "HH"),
        ("HH seed saving",          "hh_seed_saving",         150,         "HH"),
        ("Goat beneficiary HH",     "hh_goat_beneficiaries",  444,         "HH"),
        ("Active VSLAs",            "vsla_groups_active",     10,          ""),
        ("VSLAs linked MFI",        "vsla_linked_mfi",        5,           ""),
        ("HH accessing credit",     "hh_accessing_credit",    300,         "HH"),
    ]
    for idx, (label, field, target, unit) in enumerate(scorecards):
        val = aggregate_quarterly(q_filtered, field)
        fmt = "millions" if field == "revenue_cum_mwk" else None
        with cols[idx % 6]:
            make_scorecard(label, val, target, unit, fmt)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Progress by objective (%)")
        obj_data = {
            "Objective": ["Obj 1: Market Production", "Obj 2: HH Resilience", "Obj 3: Financial Inclusion"],
            "Progress": [
                pct_achieved(aggregate_quarterly(q_filtered,"offtaker_agreements"), 5),
                pct_achieved(aggregate_quarterly(q_filtered,"hh_functional_gardens"), 500),
                pct_achieved(aggregate_quarterly(q_filtered,"hh_accessing_credit"), 300),
            ]
        }
        fig = px.bar(obj_data, x="Objective", y="Progress",
                     color="Progress",
                     color_continuous_scale=[[0,"#C62828"],[0.7,"#EF9F27"],[1,"#1F5C2E"]],
                     range_color=[0,100],
                     text="Progress")
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig.add_hline(y=100, line_dash="dash", line_color="#EF9F27",
                      annotation_text="Target 100%")
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          yaxis=dict(range=[0,120], title="% achieved"),
                          xaxis_title="", height=300, margin=dict(t=20,b=40))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Producer groups by cluster")
        if not q_filtered.empty and "cluster_label" in q_filtered.columns:
            cdf = q_filtered.groupby("cluster_label")["pg_registered"].sum().reset_index()
            cdf.columns = ["Cluster","Groups"]
            target_per_cluster = 50 / 4
            fig2 = px.bar(cdf, x="Cluster", y="Groups",
                          color="Groups",
                          color_continuous_scale=[[0,"#C62828"],[0.5,"#EF9F27"],[1,"#1F5C2E"]],
                          range_color=[0,15],
                          text="Groups")
            fig2.update_traces(texttemplate="%{text}", textposition="outside")
            fig2.add_hline(y=target_per_cluster, line_dash="dash", line_color="#EF9F27",
                           annotation_text=f"Target ({target_per_cluster:.0f})")
            fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                                yaxis=dict(title="Groups"), height=300, margin=dict(t=20,b=40))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No quarterly data available for the selected filters.")

# ══════════════════════════════════════════════════════════════
# TAB 2: OBJECTIVE 1
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Objective 1 — Market-Oriented Production")
    st.markdown("*Outputs 1.1–1.4: producer groups, certified seed, irrigation, market linkages*")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        v = aggregate_quarterly(q_filtered, "offtaker_agreements")
        st.metric("Off-taker agreements", int(v), delta=f"{pct_achieved(v,5):.0f}% of target 5")
    with m2:
        v = aggregate_quarterly(q_filtered, "pct_produce_structured")
        st.metric("% produce structured", f"{v:.1f}%", delta=f"Target: 70%")
    with m3:
        v = aggregate_quarterly(q_filtered, "revenue_cum_mwk")
        st.metric("Revenue (MWK M)", f"{v/1_000_000:.1f}M", delta=f"Target: 200M")
    with m4:
        v = aggregate_quarterly(q_filtered, "farmers_sms_alerts")
        st.metric("Farmers SMS alerts", int(v), delta=f"Target: 200")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Irrigated hectares by cluster")
        if not q_filtered.empty and "cluster_label" in q_filtered.columns:
            idf = q_filtered.groupby("cluster_label")["ha_irrigated"].sum().reset_index()
            idf.columns = ["Cluster", "Ha"]
            fig = px.bar(idf, x="Cluster", y="Ha", text="Ha",
                         color_discrete_sequence=[COLOURS["teal"]])
            fig.update_traces(texttemplate="%{text:.1f} ha", textposition="outside")
            fig.add_hline(y=10/4, line_dash="dash", line_color=COLOURS["amber"],
                          annotation_text="Target per cluster (2.5 ha)")
            fig.update_layout(yaxis=dict(title="Hectares", range=[0,4]),
                               xaxis_title="", height=320, margin=dict(t=20,b=40))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Revenue trend (MWK millions)")
        if not q_filtered.empty and "report_date" in q_filtered.columns:
            rdf = q_filtered.dropna(subset=["report_date"]).sort_values("report_date")
            rdf["Rev M"] = rdf["revenue_cum_mwk"] / 1_000_000
            fig = px.line(rdf, x="report_date", y="Rev M",
                          markers=True, color_discrete_sequence=[COLOURS["green_dark"]])
            fig.add_hline(y=200, line_dash="dash", line_color=COLOURS["amber"],
                          annotation_text="Target: MWK 200M")
            fig.update_layout(xaxis_title="Quarter", yaxis_title="MWK (millions)",
                               height=320, margin=dict(t=20,b=40))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Soybean seed access by cluster")
    if not q_filtered.empty and "cluster_label" in q_filtered.columns:
        sdf = q_filtered.groupby("cluster_label")["hh_seed_cum"].sum().reset_index()
        sdf.columns = ["Cluster","HH"]
        fig = px.bar(sdf, x="Cluster", y="HH", text="HH",
                     color_discrete_sequence=[COLOURS["green_mid"]])
        fig.update_traces(texttemplate="%{text}", textposition="outside")
        fig.add_hline(y=200/4, line_dash="dash", line_color=COLOURS["amber"],
                      annotation_text="Target per cluster (50 HH)")
        fig.update_layout(yaxis_title="Households", height=280, margin=dict(t=20,b=40))
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 3: OBJECTIVE 2
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Objective 2 — Household Resilience & Diversification")
    st.markdown("*Outputs 2.1–2.3: home gardens, seed saving, post-harvest management, goat pass-on*")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        v = aggregate_quarterly(q_filtered, "hh_functional_gardens")
        st.metric("Functional gardens", int(v), delta=f"{pct_achieved(v,500):.0f}% of 500 target")
    with m2:
        v = aggregate_quarterly(q_filtered, "hh_seed_saving")
        st.metric("HH seed saving", int(v), delta=f"Target: 150 HH")
    with m3:
        v = aggregate_quarterly(q_filtered, "pct_loss_reduction")
        nrow = max(1, len(q_filtered[q_filtered["pct_loss_reduction"]>0]))
        avg_v = q_filtered["pct_loss_reduction"].sum() / nrow if not q_filtered.empty else 0
        st.metric("Post-harvest loss red.", f"{avg_v:.1f}%", delta="Target: 35%")
    with m4:
        v = aggregate_quarterly(q_filtered, "hh_goat_beneficiaries")
        st.metric("Goat beneficiary HH", int(v), delta=f"Target: 444 HH")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Home garden adoption by cluster (% of 125 target per cluster)")
        if not q_filtered.empty and "cluster_label" in q_filtered.columns:
            gdf = q_filtered.groupby("cluster_label")["hh_functional_gardens"].sum().reset_index()
            gdf["pct"] = gdf["hh_functional_gardens"] / 125 * 100
            gdf.columns = ["Cluster","Gardens","Pct"]
            colours = [COLOURS["green_dark"] if p >= 100 else
                       (COLOURS["amber"] if p >= 70 else COLOURS["red"]) for p in gdf["Pct"]]
            fig = px.bar(gdf, x="Cluster", y="Pct", text="Pct",
                         color="Cluster", color_discrete_sequence=colours)
            fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
            fig.add_hline(y=100, line_dash="dash", line_color=COLOURS["amber"],
                          annotation_text="100% target")
            fig.update_layout(showlegend=False, yaxis=dict(title="%", range=[0,120]),
                               height=320, margin=dict(t=20,b=40))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Goat pass-on — cumulative HH trend")
        if not q_filtered.empty and "report_date" in q_filtered.columns:
            goat_df = q_filtered.dropna(subset=["report_date"]).sort_values("report_date")
            fig = px.line(goat_df, x="report_date", y="hh_goat_beneficiaries",
                          markers=True, color_discrete_sequence=[COLOURS["green_dark"]])
            fig.add_hline(y=444, line_dash="dash", line_color=COLOURS["amber"],
                          annotation_text="Target: 444 HH")
            fig.update_layout(xaxis_title="Quarter", yaxis_title="HH beneficiaries",
                               height=320, margin=dict(t=20,b=40))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Post-harvest loss reduction by cluster (target: 35%)")
    if not q_filtered.empty and "cluster_label" in q_filtered.columns:
        phdf = q_filtered.groupby("cluster_label")["pct_loss_reduction"].mean().reset_index()
        phdf.columns = ["Cluster","Loss Reduction %"]
        colours_ph = [COLOURS["green_dark"] if p >= 35 else
                      (COLOURS["amber"] if p >= 20 else COLOURS["red"])
                      for p in phdf["Loss Reduction %"]]
        fig = px.bar(phdf, x="Cluster", y="Loss Reduction %", text="Loss Reduction %",
                     color="Cluster", color_discrete_sequence=colours_ph)
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.add_hline(y=35, line_dash="dash", line_color=COLOURS["amber"],
                      annotation_text="Target: 35% reduction")
        fig.update_layout(showlegend=False, yaxis=dict(title="% reduction", range=[0,50]),
                           height=280, margin=dict(t=20,b=40))
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 4: OBJECTIVE 3
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Objective 3 — Financial Inclusion & Sustainability")
    st.markdown("*Output 3.1: VSLA groups, savings, credit access, microfinance linkages*")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        v = aggregate_quarterly(q_filtered, "vsla_groups_active")
        st.metric("Active VSLA groups", int(v), delta=f"Target: 10")
    with m2:
        v = aggregate_quarterly(q_filtered, "vsla_linked_mfi")
        st.metric("VSLAs linked to MFI", int(v), delta=f"Target: 5")
    with m3:
        v = aggregate_quarterly(q_filtered, "hh_accessing_credit")
        st.metric("HH accessing credit", int(v), delta=f"Target: 300 HH")
    with m4:
        v = aggregate_quarterly(q_filtered, "hh_finlit_trained")
        st.metric("HH finlit trained", int(v))

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### VSLA savings by cluster (MWK thousands)")
        if not q_filtered.empty and "cluster_label" in q_filtered.columns:
            vdf = q_filtered.groupby("cluster_label")["vsla_savings_k"].sum().reset_index()
            vdf.columns = ["Cluster","Savings (K MWK)"]
            fig = px.bar(vdf, x="Cluster", y="Savings (K MWK)", text="Savings (K MWK)",
                         color_discrete_sequence=["#4A148C"])
            fig.update_traces(texttemplate="%{text:.0f}K", textposition="outside")
            fig.update_layout(yaxis_title="MWK (thousands)", height=320, margin=dict(t=20,b=40))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### HH accessing credit — quarterly trend")
        if not q_filtered.empty and "report_date" in q_filtered.columns:
            cdf = q_filtered.dropna(subset=["report_date"]).sort_values("report_date")
            fig = px.line(cdf, x="report_date", y="hh_accessing_credit",
                          markers=True, color_discrete_sequence=[COLOURS["blue"]])
            fig.add_hline(y=300, line_dash="dash", line_color=COLOURS["amber"],
                          annotation_text="Target: 300 HH")
            fig.update_layout(xaxis_title="Quarter", yaxis_title="HH", height=320,
                               margin=dict(t=20,b=40))
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 5: WEEKLY FEED
# ══════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### Weekly Activity Feed")
    st.markdown("*Live submissions from field enumerators — updates automatically when KoboToolbox receives new entries*")

    m1, m2, m3 = st.columns(3)
    with m1:
        v = w_filtered["hh_reached_total"].sum() if not w_filtered.empty else 0
        st.metric("HH reached (total)", int(v))
    with m2:
        v = w_filtered["meetings_held"].sum() if not w_filtered.empty else 0
        st.metric("Meetings held", int(v))
    with m3:
        v = w_filtered["revenue_mwk"].sum() if not w_filtered.empty else 0
        st.metric("Revenue (MWK)", f"{v:,.0f}")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### HH reached per week (male / female)")
        if not w_filtered.empty and "report_week" in w_filtered.columns:
            wdf = w_filtered.groupby("report_week")[["hh_reached_male","hh_reached_female"]].sum().reset_index()
            wdf = wdf.rename(columns={"report_week":"Week","hh_reached_male":"Male","hh_reached_female":"Female"})
            fig = go.Figure()
            fig.add_trace(go.Bar(x=wdf["Week"], y=wdf["Male"], name="Male",
                                 marker_color=COLOURS["green_dark"]))
            fig.add_trace(go.Bar(x=wdf["Week"], y=wdf["Female"], name="Female",
                                 marker_color=COLOURS["teal_light"]))
            fig.update_layout(barmode="group", xaxis_title="Week", yaxis_title="HH reached",
                               legend=dict(orientation="h", y=-0.2),
                               height=320, margin=dict(t=20,b=60))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Activities conducted — distribution")
        if not w_filtered.empty and "activities_conducted" in w_filtered.columns:
            acts = w_filtered["activities_conducted"].dropna().str.split().explode()
            act_counts = acts.value_counts().reset_index()
            act_counts.columns = ["Activity","Count"]
            act_labels = {
                "seeds":"Seeds","irrigation":"Irrigation","market":"Market",
                "vsla":"VSLA","home_garden":"Home garden","postharvest":"Post-harvest"
            }
            act_counts["Activity"] = act_counts["Activity"].map(act_labels).fillna(act_counts["Activity"])
            fig = px.pie(act_counts.head(6), values="Count", names="Activity",
                         color_discrete_sequence=[COLOURS["green_dark"],COLOURS["teal"],
                                                   COLOURS["amber"],COLOURS["blue"],
                                                   "#97C459","#B4B2A9"],
                         hole=0.4)
            fig.update_layout(height=320, margin=dict(t=20,b=20))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Latest submissions")
    if not w_filtered.empty:
        display_cols = [c for c in ["date_of_report","club_name","cluster_label",
                                     "activities_conducted","hh_reached_male",
                                     "hh_reached_female","hh_reached_total",
                                     "any_challenges","challenges_desc"] if c in w_filtered.columns]
        display_df = w_filtered[display_cols].sort_values(
            "date_of_report", ascending=False).head(15).reset_index(drop=True)
        display_df.columns = [c.replace("_"," ").title() for c in display_df.columns]

        def highlight_challenges(row):
            if "Any Challenges" in row.index and str(row["Any Challenges"]).lower() == "yes":
                return ["background-color: #FFEBEE"] * len(row)
            return [""] * len(row)

        st.dataframe(display_df.style.apply(highlight_challenges, axis=1),
                     use_container_width=True, height=400)
    else:
        st.info("No weekly data available for the selected filters.")

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;color:#aaa;font-size:11px'>
LIFE Project M&E Dashboard  •  Agri-Impact Malawi  •  Egmont Trust  •
Data source: LIFE Project – M&E Data Hub (Google Sheets)  •
Auto-refreshes every 5 minutes
</div>
""", unsafe_allow_html=True)

streamlit run streamlit_app.py
