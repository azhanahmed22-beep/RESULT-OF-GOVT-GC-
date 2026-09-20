"""
Ghazali College HSC-II 2026 Results Dashboard
------------------------------------------------
Run with:  streamlit run results_dashboard.py

Expects a CSV with columns:
    Group, RollNo, Marks, Grade, Passed_in
    - Grade      -> pass / fail / rwh (result status)
    - Passed_in  -> letter grade (A1 / A / B / C / D) — blank for fails/RWH
"""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="HSC-II 2026 Results Dashboard", layout="wide")

DEFAULT_FILE = "Ghazali_College_HSC_II_2026_results.csv"
LETTER_ORDER = ["A1", "A", "B", "C", "D", "Fail/RWH"]
LETTER_COLORS = {
    "A1": "#1a9850", "A": "#66bd63", "B": "#a6d96a",
    "C": "#fee08b", "D": "#fdae61", "Fail/RWH": "#d73027",
}


# ---------------------------------------------------------------- data load
@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]

    df["Status"] = df["Grade"].astype(str).str.strip().str.lower()
    df["Status"] = df["Status"].apply(lambda x: "Pass" if x == "pass" else "Fail")

    # Unified "Result" bucket used for the EDA counts: A1, A, B, C, D, Fail/RWH
    letter = df["Passed_in"].astype(str).str.strip().str.upper()
    letter = letter.replace({"NAN": ""})
    df["Result"] = letter.where(letter != "", "Fail/RWH")

    df["Rank"] = df["Marks"].rank(method="min", ascending=False).astype(int)
    df = df.sort_values("Rank").reset_index(drop=True)
    return df


st.title("🎓 Ghazali College — HSC-II 2026 Results Dashboard")

uploaded = st.sidebar.file_uploader("Upload results CSV", type="csv")
try:
    data = load_data(uploaded if uploaded is not None else DEFAULT_FILE)
except FileNotFoundError:
    st.error(
        f"Couldn't find `{DEFAULT_FILE}` next to this script, and no file was "
        "uploaded. Use the uploader in the sidebar."
    )
    st.stop()

# ---------------------------------------------------------------- sidebar filters
st.sidebar.header("Filters")
group_options = ["All"] + sorted(data["Group"].dropna().unique().tolist())
group_filter = st.sidebar.selectbox("Group", group_options)

result_options = ["All"] + LETTER_ORDER
result_filter = st.sidebar.selectbox("Result / Grade", result_options)

filtered = data.copy()
if group_filter != "All":
    filtered = filtered[filtered["Group"] == group_filter]
if result_filter != "All":
    filtered = filtered[filtered["Result"] == result_filter]

# ---------------------------------------------------------------- top metrics
total = len(data)
passed = (data["Status"] == "Pass").sum()
failed = (data["Status"] == "Fail").sum()
pass_rate = passed / total * 100 if total else 0
top_scorer = data.loc[data["Marks"].idxmax()]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Students", total)
c2.metric("Passed", passed)
c3.metric("Failed / RWH", failed)
c4.metric("Pass Rate", f"{pass_rate:.1f}%")
c5.metric("Top Score", f"{int(top_scorer['Marks'])}", f"Roll {int(top_scorer['RollNo'])}")

st.divider()

# ---------------------------------------------------------------- roll number search
st.subheader("🔎 Search Student by Roll Number")
roll_input = st.text_input("Enter Roll Number", placeholder="e.g. 87393")

if roll_input:
    try:
        roll_val = int(roll_input.strip())
        match = data[data["RollNo"] == roll_val]
        if match.empty:
            st.warning(f"No student found with Roll Number {roll_val}.")
        else:
            row = match.iloc[0]
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Roll No", int(row["RollNo"]))
            m2.metric("Group", row["Group"])
            m3.metric("Marks", int(row["Marks"]))
            m4.metric("Grade", row["Result"])
            m5.metric("Rank (Overall)", int(row["Rank"]))
            st.dataframe(match, use_container_width=True, hide_index=True)
    except ValueError:
        st.error("Please enter a valid numeric roll number.")

st.divider()

# ---------------------------------------------------------------- EDA: grade distribution
st.subheader("📊 Result Distribution (Fail, D, C, B, A, A1)")

grade_counts = (
    data["Result"].value_counts().reindex(LETTER_ORDER).fillna(0).astype(int)
)

ec1, ec2 = st.columns([2, 1])
with ec1:
    fig = px.bar(
        x=grade_counts.index,
        y=grade_counts.values,
        labels={"x": "Grade / Result", "y": "Number of Students"},
        color=grade_counts.index,
        color_discrete_map=LETTER_COLORS,
        text=grade_counts.values,
        title="Students per Grade",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with ec2:
    fig_pie = px.pie(
        names=grade_counts.index,
        values=grade_counts.values,
        color=grade_counts.index,
        color_discrete_map=LETTER_COLORS,
        title="Grade Share",
        hole=0.4,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.dataframe(
    grade_counts.rename("Count").rename_axis("Grade").reset_index(),
    use_container_width=True,
    hide_index=True,
)

# Group-wise breakdown
st.subheader("📈 Grade Distribution by Group")
group_grade = (
    data.groupby(["Group", "Result"]).size().reset_index(name="Count")
)
fig_group = px.bar(
    group_grade,
    x="Group",
    y="Count",
    color="Result",
    barmode="group",
    color_discrete_map=LETTER_COLORS,
    category_orders={"Result": LETTER_ORDER},
    title="Grades by Group",
)
st.plotly_chart(fig_group, use_container_width=True)

st.divider()

# ---------------------------------------------------------------- full ranking table
st.subheader("🏆 Student Ranking (Sorted by Marks)")
display_cols = ["Rank", "RollNo", "Group", "Marks", "Result", "Status"]
st.dataframe(
    filtered[display_cols].sort_values("Rank"),
    use_container_width=True,
    hide_index=True,
    height=500,
)

st.caption(
    f"Showing {len(filtered)} of {total} students"
    + (f" — Group: {group_filter}" if group_filter != "All" else "")
    + (f" — Result: {result_filter}" if result_filter != "All" else "")
)

csv_data = filtered[display_cols].sort_values("Rank").to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download filtered ranking as CSV", csv_data, "ranking.csv", "text/csv")

st.markdown("<div style='text-align:center; color:gray; margin-top:20px; font-size:14px;'>Made by AzhanDev</div>", unsafe_allow_html=True)