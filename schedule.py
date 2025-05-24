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

# Session state initialization
if 'epo_log' not in st.session_state:
    st.session_state.epo_log = []
if 'paint_assignments' not in st.session_state:
    st.session_state.paint_assignments = {}

st.title("🏠 Paint & Drywall Automator Demo")
mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule",
    "Order Mud & EPO",
    "QC Scheduling",
    "Homeowner Scheduling",
    "Paint Assignment"
])

# --- Schedule Tab ---
if mode == "Schedule":
    st.header("📆 Schedule Generator")
    lot   = st.text_input("Lot number")
    comm  = st.selectbox("Community", list(COMMUNITIES.keys()))
    start = st.date_input("Start date")
    if st.button("Generate Schedule"):
        sched = []
        cur = start
        for t in TASKS:
            days = DUR[t]
            # skip Sundays for all except Scrap, skip weekends for Scrap
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
            sched.append((t, COMMUNITIES[comm].get(t, '—'), d.strftime('%m/%d/%Y')))
            cur = d
        st.table({
            "Task": [t for t,_,_ in sched],
            "Subcontractor": [s for _,s,_ in sched],
            "Date": [d for *_,d in sched]
        })
    st.subheader("🚚 Order Mud")
    if st.button("Order Mud for Scrap Date"):
        if sched:
            scrap_date = sched[1][2]
            st.success(f"📧 Mud order email queued for {scrap_date}")
        else:
            st.info("Generate schedule first to order mud.")

# --- EPO Tab ---
elif mode == "Order Mud & EPO":
    st.header("✉️ EPO Automation")
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
    log = st.session_state.epo_log
    if log:
        for idx, entry in enumerate(log):
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

# --- QC Scheduling Tab ---
elif mode == "QC Scheduling":
    st.header("🔍 QC Scheduling")
    lot   = st.text_input("Lot number", key="qc_lot")
    comm  = st.selectbox("Community", list(COMMUNITIES.keys()), key="qc_comm")
    pu    = st.date_input("QC Point-Up date", key="qc_pu")
    paint_sub = st.selectbox("QC Paint subcontractor", PAINT_SUBS, key="qc_paint_sub")
    stain  = st.date_input("QC Stain Touch-Up date", key="qc_stain")
    if st.button("Schedule QC Tasks"):
        tasks = [
            {"task": "QC Point-Up",      "sub": POINTUP_SUBS.get(comm, "—"),   "date": pu.strftime('%m/%d/%Y')},
            {"task": "QC Paint",         "sub": paint_sub,                      "date": pu.strftime('%m/%d/%Y')},
            {"task": "QC Stain Touch-Up","sub": 'Dorby',                       "date": stain.strftime('%m/%d/%Y')},
        ]
        st.success("QC tasks scheduled:")
        st.table(tasks)
        st.json({"lot": lot, "community": comm, "qc_tasks": tasks})

# --- Homeowner Scheduling Tab ---
elif mode == "Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    lot   = st.text_input("Lot number", key="ho_lot")
    comm  = st.selectbox("Community", list(COMMUNITIES.keys()), key="ho_comm")
    pu    = st.date_input("HO Point-Up date", key="ho_pu")
    paint_sub = st.selectbox("HO Paint subcontractor", PAINT_SUBS, key="ho_paint_sub")
    if st.button("Schedule Homeowner Tasks"):
        tasks = [
            {"task": "HO Point-Up", "sub": POINTUP_SUBS.get(comm, "—"), "date": pu.strftime('%m/%d/%Y')},
            {"task": "HO Paint",    "sub": paint_sub,                 "date": pu.strftime('%m/%d/%Y')},
        ]
        st.success("Homeowner tasks scheduled:")
        st.table(tasks)
        st.json({"lot": lot, "community": comm, "homeowner_tasks": tasks})

# --- Paint Assignment Tab ---
elif mode == "Paint Assignment":
    st.header("🎨 Paint Subcontractor Assignment")
    lot       = st.text_input("Lot number", key="pa_lot")
    comm      = st.selectbox("Community", list(COMMUNITIES.keys()), key="pa_comm")
    paint_sub = st.selectbox("Assign Paint subcontractor", PAINT_SUBS, key="pa_assign")
    if st.button("Assign Paint Subcontractor"):
        st.session_state.paint_assignments[f"{lot}_{comm}"] = paint_sub
        st.success(f"Assigned '{paint_sub}' for Lot {lot}, {comm}")
    if st.session_state.paint_assignments:
        st.subheader("Current Paint Assignments")
        df = []
        for k, v in st.session_state.paint_assignments.items():
            l, c = k.split('_', 1)
            df.append({"lot": l, "community": c, "paint_sub": v})
        st.table(df)

st.sidebar.markdown("---")
st.sidebar.write("This is a **demo only**—no actual emails go out.")
