import streamlit as st
import datetime
import json

# --- Business logic from your specs ---
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
# Duration (days) for drywall phases
DUR = {'Hang': 1, 'Scrap': 1, 'Sand': 1, 'Tape': 2, 'Bed': 2, 'Skim': 2}

# Point-Up subcontractors for QC & Homeowner
POINTUP_SUBS = {
    'Galloway': 'Luis A. Lopez',
    'Huntersville Town Center': 'Luis A. Lopez',
    'Claremont': 'Edwin',
    'Context': 'Edwin',
    'Greenway Overlook': 'Edwin',
    'Camden': 'Luis A. Lopez',
    'Olmstead': 'Luis A. Lopez',
    'Maxwell': 'Luis A. Lopez'
}

# Paint subcontractor options
PAINT_SUBS = [
    'GP Painting Services',
    'Jorge Gomez',
    'Christian Painting',
    'Carlos Gabriel',
    'Juan Ulloa'
]

# Session state initialization for EPO tracker
if 'epo_log' not in st.session_state:
    st.session_state.epo_log = []

# App Layout
st.title("🏠 Paint & Drywall Automator Demo")
mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule & Order Mud",
    "EPO & Tracker",
    "QC Scheduling",
    "Homeowner Scheduling"
])

# --- Schedule & Order Mud ---
if mode == "Schedule & Order Mud":
    st.header("📆 Schedule Generator & Mud Order")
    lot   = st.text_input("Lot number")
    comm  = st.selectbox("Community", list(COMMUNITIES.keys()))
    start = st.date_input("Start date (MM/DD/YYYY)")
    if st.button("Generate Schedule"):
        schedule = []
        cur = start
        for t in TASKS:
            days = DUR[t]
            skip_sun = (t != 'Scrap')
            skip_wk = (t == 'Scrap')
            d = cur
            added = 0
            while added < days:
                d += datetime.timedelta(days=1)
                if skip_wk and d.weekday() >= 5:
                    continue
                if skip_sun and d.weekday() == 6:
                    continue
                added += 1
            schedule.append((t, COMMUNITIES[comm].get(t,'—'), d.strftime('%m/%d/%Y')))
            cur = d
        st.table({
            "Task": [t for t,_,_ in schedule],
            "Subcontractor": [s for _,s,_ in schedule],
            "Date": [d for *_,d in schedule]
        })
    if st.button("Order Mud for Scrap Date"):
        if schedule:
            scrap_date = schedule[1][2]
            st.success(f"📧 Mud order email queued for {scrap_date}")
        else:
            st.info("Please generate schedule first.")

# --- EPO & Tracker ---
elif mode == "EPO & Tracker":
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo_form"):
        col1, col2 = st.columns(2)
        lot      = col1.text_input("Lot")
        comm     = col1.selectbox("Community", list(COMMUNITIES.keys()))
        email_to = col2.text_input("Builder Email")
        amount   = col2.text_input("Amount")
        photos   = st.file_uploader("Attach photos", accept_multiple_files=True)
        sent     = st.form_submit_button("Send EPO")
    if sent:
        now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
        st.success(f"EPO for Lot {lot} {comm} recorded at {now}")
        st.session_state.epo_log.append({
            "lot": lot, "comm": comm, "to": email_to,
            "amt": amount, "sent": now,
            "replied": False, "followup": False
        })
    st.subheader("📋 EPO Tracker")
    if st.session_state.epo_log:
        for idx, entry in enumerate(st.session_state.epo_log):
            cols = st.columns(6)
            cols[0].write(entry['lot'])
            cols[1].write(entry['comm'])
            cols[2].write(entry['sent'])
            status = ("Replied" if entry['replied']
                      else ("Follow-Up Sent" if entry['followup'] else "Pending"))
            cols[3].write(status)
            if not entry['replied']:
                if cols[4].button("Mark Replied", key=f"r{idx}"):
                    entry['replied'] = True
            if not entry['followup'] and not entry['replied']:
                if cols[5].button("Send Follow-Up", key=f"f{idx}"):
                    entry['followup'] = True
                    st.info(f"🔔 Follow-up for Lot {entry['lot']} queued.")
    else:
        st.write("No EPOs sent yet.")

# --- QC Scheduling ---
elif mode == "QC Scheduling":
    st.header("🔍 QC Scheduling")
    lot        = st.text_input("Lot number", key="qc_lot")
    comm       = st.selectbox("Community", list(COMMUNITIES.keys()), key="qc_comm")
    pu_date    = st.date_input("QC Point-Up date", key="qc_pu")
    paint_date = st.date_input("QC Paint date", key="qc_paint_date")
    paint_sub  = st.selectbox("QC Paint subcontractor", PAINT_SUBS, key="qc_paint_sub")
    stain_date = st.date_input("QC Stain Touch-Up date", key="qc_stain")
    if st.button("Schedule QC Tasks"):
        tasks = [
            {"task": "QC Point-Up",       "sub": POINTUP_SUBS.get(comm,"—"), "date": pu_date.strftime('%m/%d/%Y')},
            {"task": "QC Paint",          "sub": paint_sub,                   "date": paint_date.strftime('%m/%d/%Y')},
            {"task": "QC Stain Touch-Up", "sub": 'Dorby',                      "date": stain_date.strftime('%m/%d/%Y')},
        ]
        st.success("QC tasks scheduled:")
        st.table(tasks)
        st.json({"lot": lot, "community": comm, "qc_tasks": tasks})

# --- Homeowner Scheduling ---
elif mode == "Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    lot        = st.text_input("Lot number", key="ho_lot")
    comm       = st.selectbox("Community", list(COMMUNITIES.keys()), key="ho_comm")
    pu_date    = st.date_input("HO Point-Up date", key="ho_pu")
    paint_date = st.date_input("HO Paint date", key="ho_paint_date")
    paint_sub  = st.selectbox("HO Paint subcontractor", PAINT_SUBS, key="ho_paint_sub")
    if st.button("Schedule Homeowner Tasks"):
        tasks = [
            {"task": "HO Point-Up", "sub": POINTUP_SUBS.get(comm,"—"), "date": pu_date.strftime('%m/%d/%Y')},
            {"task": "HO Paint",    "sub": paint_sub,                 "date": paint_date.strftime('%m/%d/%Y')},
        ]
        st.success("Homeowner tasks scheduled:")
        st.table(tasks)
        st.json({"lot": lot, "community": comm, "homeowner_tasks": tasks})

st.sidebar.markdown("---")
st.sidebar.write("This is a **demo only**—no actual emails go out.")
