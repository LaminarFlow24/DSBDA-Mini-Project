import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="COVID Dashboard", layout="wide")

st.title("📊 COVID-19 Vaccination Dashboard")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    usecols = [
        'Updated On', 'State', 'First Dose Administered', 
        'Second Dose Administered', 'Male (Doses Administered)', 
        'Female (Doses Administered)'
    ]
    df = pd.read_csv("covid_vaccine_statewise.csv", usecols=usecols)
    df['Updated On'] = pd.to_datetime(df['Updated On'], dayfirst=True, errors='coerce')
    df = df[df['State'] != 'India']

    # Convert numeric columns
    cols = [
        'First Dose Administered',
        'Second Dose Administered',
        'Male (Doses Administered)',
        'Female (Doses Administered)'
    ]
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

df = load_data()

# ---------------- FILTERS ----------------
st.sidebar.header("🔍 Filters")

min_date = df['Updated On'].min()
max_date = df['Updated On'].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

state_list = sorted(df['State'].dropna().unique())
selected_state = st.sidebar.selectbox("Select State", ["All"] + state_list)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = date_range[0], date_range[0]

# Apply filters
filtered_df = df[
    (df['Updated On'] >= pd.to_datetime(start_date)) &
    (df['Updated On'] <= pd.to_datetime(end_date))
]

if selected_state != "All":
    filtered_df = filtered_df[filtered_df['State'] == selected_state]

# Clean valid rows
clean_df = filtered_df.dropna(subset=['First Dose Administered', 'Second Dose Administered'])

# Latest valid per state (for comparisons)
latest_df = clean_df.sort_values('Updated On').groupby('State').tail(1)

# ---------------- 📈 TREND ----------------
st.subheader("📈 Vaccination Trend Over Time")

trend_df = filtered_df.dropna(subset=['First Dose Administered'])

fig1 = px.line(trend_df, x='Updated On', y='First Dose Administered', 
               title="First Dose Vaccination Trend",
               labels={"Updated On": "Date", "First Dose Administered": "First Dose"})
st.plotly_chart(fig1, use_container_width=True)

# ---------------- 📊 TOP 10 ----------------
st.subheader("📊 Top 10 States (First Dose)")

top10 = latest_df.sort_values(by='First Dose Administered', ascending=False).head(10)

fig2 = px.bar(top10, x='First Dose Administered', y='State', orientation='h',
              title="Top 10 States by First Dose")
fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig2, use_container_width=True)

# ---------------- 🥧 GENDER ----------------
st.subheader("🥧 Gender Distribution")

male_total = filtered_df['Male (Doses Administered)'].sum()
female_total = filtered_df['Female (Doses Administered)'].sum()

gender_data = pd.DataFrame({
    'Gender': ['Male', 'Female'],
    'Total': [male_total, female_total]
})
fig3 = px.pie(gender_data, values='Total', names='Gender', title="Gender Distribution")
st.plotly_chart(fig3, use_container_width=True)

# ---------------- 📉 GAP ANALYZER ----------------
st.subheader("📉 Vaccination Gap Analyzer")

latest_df['Gap'] = latest_df['First Dose Administered'] - latest_df['Second Dose Administered']

gap_df = latest_df.sort_values(by='Gap', ascending=False).head(10)

fig4 = px.bar(gap_df, x='Gap', y='State', orientation='h',
              title="States with Highest Vaccination Gap (First vs Second Dose)")
fig4.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig4, use_container_width=True)

st.info("👉 States with high gap = lagging in full vaccination")

# ---------------- 🧠 SMART RANKING ----------------
st.subheader("🏆 Smart State Ranking")

# Total vaccination
latest_df['Total'] = latest_df['First Dose Administered'] + latest_df['Second Dose Administered']

# Growth rate (last - first value)
growth_list = []

for state in latest_df['State']:
    state_data = filtered_df[filtered_df['State'] == state].dropna(subset=['First Dose Administered'])
    
    if len(state_data) > 1:
        growth = state_data.iloc[-1]['First Dose Administered'] - state_data.iloc[0]['First Dose Administered']
    else:
        growth = 0
    
    growth_list.append(growth)

latest_df['Growth'] = growth_list

# Score (simple weighted)
latest_df['Score'] = 0.7 * latest_df['Total'] + 0.3 * latest_df['Growth']

ranking = latest_df.sort_values(by='Score', ascending=False)[['State', 'Score']]

st.dataframe(ranking.reset_index(drop=True))

st.markdown("### 🥇 Leaderboard")
top_states = ranking.head(3)['State'].tolist()

for i, state in enumerate(top_states, 1):
    st.write(f"{i}. {state}")