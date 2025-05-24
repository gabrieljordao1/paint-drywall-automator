import streamlit as st
import datetime
import re

# --- Business logic ---
TASKS = ['Hang', 'Scrap', 'Tape', 'Bed', 'Skim', 'Sand']
COMMUNITIES = {
    'Galloway':                   {t: 'America Drywall' for t in TASKS},
    'Huntersville Town Center':   {t: 'America Drywall' for t in TASKS},
    'Claremont': {
        'Hang': 'Ricardo', 'Scrap': 'Scrap Brothers', 'Tape': 'Juan Trejo',
        'Bed': 'Juan Trejo', 'Skim': 'Juan Trejo', 'Sand': 'Juan Trejo'
    },
    'Context':                    {t: 'America Drywall' for t in TASKS},
    'Greenway Overlook':          {t: 'America Drywall' for t in TASKS},
    'Camden':                     {t: 'America Drywall' for t in TASKS},
    'Olmstead': {
        'Hang': 'Ricardo', 'Scrap': 'Scrap Brothers', 'Tape': 'Juan Trejo',
        'Bed': 'Juan Trejo', 'Skim': 'Juan Trejo', 'Sand': 'Juan Trejo'
    },
    'Maxwell':                    {t: 'America Drywall' for t in TASKS},
}
# Phase durations
DUR = {'Hang': 1, 'Scrap': 1, 'Sand': 1, 'Tape': 2, 'Bed': 2, 'Skim': 2}

# Point-up subs
POINTUP_SUBS = {
    'Galloway': 'Luis A. Lopez',
    'Huntersville Town Center': 'Luis A. Lopez',
    'Claremont': 'Edwin', 'Context': 'Edwin', 'Greenway Overlook': 'Edwin',
    'Camden': 'Luis A. Lopez', 'Olmstead': 'Luis A. Lopez', 'Maxwell': 'Luis A. Lopez'
}

# Paint subcontractors
PAINT_SUBS = [
    'GP Painting Services', 'Jorge Gomez', 'Christian Painting', 'Carlos Gabriel', 'Juan Ulloa'
]

# Initialize session state
if 'epo_log' not in st.session_state:
    st.session_state.epo_log = []
if 'notes' not in st.session_state:
    st.session_state.notes = []

# App layout
st.title("🏠 Paint & Drywall Automator Demo")
mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule & Order Mud",
    "EPO & Tracker",
    "QC Scheduling",
    "Homeowner Scheduling",
    "Note Taking"
])

# --- Schedule & Order Mud ---
if mode == "Schedule & Order Mud":
    st.header("📆 Schedule & Mud Order")
    lot = st.text_input("Lot number")
    comm = st.selectbox("Community", list(COMMUNITIES.keys()))
    start = st.date_input("Start date")
    schedule = []
    if st.button("Generate Schedule"):
        cur = start
        for t in TASKS:
            days = DUR[t]
            skip_sun = (t != 'Scrap'); skip_wk = (t == 'Scrap')
            d, added = cur, 0
            while added < days:
                d += datetime.timedelta(days=1)
                if skip_wk and d.weekday() >= 5: continue
                if skip_sun and d.weekday() == 6: continue
                added += 1
            schedule.append((t, COMMUNITIES[comm][t], d.strftime('%m/%d/%Y')))
            cur = d
        st.table({"Task": [x[0] for x in schedule],
                  "Subcontractor": [x[1] for x in schedule],
                  "Date": [x[2] for x in schedule]})
    if st.button("Order Mud for Scrap Date"):
        if schedule:
            st.success(f"📧 Mud order for {schedule[1][2]}")

# --- EPO & Tracker ---
elif mode == "EPO & Tracker":
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo"): ...  # see above for full form logic

# --- QC Scheduling ---
elif mode == "QC Scheduling":
    st.header("🔍 QC Scheduling")
    ...  # see above for QC form logic

# --- Homeowner Scheduling ---
elif mode == "Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    ...  # see above for homeowner form logic

# --- Note Taking ---
elif mode == "Note Taking":
    st.header("📝 Note Taking")
    comm = st.selectbox("Community", list(COMMUNITIES.keys()))
    notes_input = st.text_area("Enter notes (Lot### - note)")
    if st.button("Parse Notes"):
        st.session_state.notes = []
        for line in notes_input.splitlines(): ...
    if st.session_state.notes:
        st.table(st.session_state.notes)
    
st.sidebar.write("Demo only—no real emails.")
