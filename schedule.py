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
DUR = {'Hang': 1, 'Scrap': 1, 'Sand': 1, 'Tape': 2, 'Bed': 2, 'Skim': 2}

def add_days(start, days, skip_sunday=False, skip_weekend=False):
    d, added = start, 0
    while added < days:
        d += datetime.timedelta(days=1)
        if skip_weekend and d.weekday() >= 5:   # Sat=5, Sun=6
            continue
        if skip_sunday and d.weekday() == 6:
            continue
        added += 1
    return d

def build_schedule(comm, start):
    subs = COMMUNITIES.get(comm, {})
    out, cur = [], start
    for t in TASKS:
        sched = add_days(cur, DUR[t],
                         skip_sunday=(t != 'Scrap'),
                         skip_weekend=(t == 'Scrap'))
        out.append((t, subs.get(t, '—'), sched.strftime('%m/%d/%Y')))
        cur = sched
    return out

# --- EPO tracker stored in session ---
if 'epo_log' not in st.session_state:
    st.session_state.epo_log = []

st.title("🏠 Paint & Drywall Automator Demo")

mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule",
    "Order Mud & EPO",
    "QC Scheduling",
    "Homeowner Scheduling"
])

if mode == "Schedule":
    st.header("📆 Schedule Generator")
    lot  = st.text_input("Lot number")
    comm = st.selectbox("Community", list(COMMUNITIES.keys()))
    start = st.date_input("Start date")
    if st.button("Generate Schedule"):
        sched = build_schedule(comm, start)
        st.table({
            "Task": [t for t, _, _ in sched],
            "Subcontractor": [s for _, s, _ in sched],
            "Date": [d for *_, d in sched],
        })
    st.subheader("🚚 Order Mud")
    if st.button("Order Mud for Scrap Date"):
        sched = build_schedule(comm, start)
        scrap_date = sched[1][2] if len(sched) > 1 else ""
        st.success(f"📧 Mud order email queued for {scrap_date}")

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
            now = datetime.datetime.now().strftime("%m/%d/%Y %H:%M")
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
            status = (
                "Replied" if entry['replied']
                else ("Follow-Up Sent" if entry['followup'] else "Pending")
            )
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

elif mode == "QC Scheduling":
    st.header("🔍 QC Scheduling")
    lot   = st.text_input("Lot number", key="qc_lot")
    comm  = st.selectbox("Community", list(COMMUNITIES.keys()), key="qc_comm")
    pu    = st.date_input("QC Point-Up date", key="qc_pu")
    paint = st.date_input("QC Paint date", key="qc_paint")
    touch = st.date_input("QC Touch-Up date", key="qc_touch")
    if st.button("Schedule QC Tasks"):
        subs = COMMUNITIES.get(comm, {})
        tasks = [
            {"task": "QC Point-Up", "sub": subs.get("Hang", "—"), "date": pu.strftime("%m/%d/%Y")},
            {"task": "QC Paint",    "sub": subs.get("Tape", "—"), "date": paint.strftime("%m/%d/%Y")},
            {"task": "QC Touch-Up", "sub": subs.get("Bed",  "—"), "date": touch.strftime("%m/%d/%Y")},
        ]
        st.success("QC tasks scheduled:")
        st.table(tasks)
        st.json({"lot": lot, "community": comm, "qc_tasks": tasks})

elif mode == "Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    lot   = st.text_input("Lot number", key="ho_lot")
    comm  = st.selectbox("Community", list(COMMUNITIES.keys()), key="ho_comm")
    pu    = st.date_input("HO Point-Up date", key="ho_pu")
    paint = st.date_input("HO Paint date", key="ho_paint")
    if st.button("Schedule Homeowner Tasks"):
        subs = COMMUNITIES.get(comm, {})
        tasks = [
            {"task": "HO Point-Up", "sub": subs.get("Skim", "—"), "date": pu.strftime("%m/%d/%Y")},
            {"task": "HO Paint",    "sub": subs.get("Hang", "—"), "date": paint.strftime("%m/%d/%Y")},
        ]
        st.success("Homeowner tasks scheduled:")
        st.table(tasks)
        st.json({"lot": lot, "community": comm, "homeowner_tasks": tasks})

st.sidebar.markdown("---")
st.sidebar.write("This is a **demo only**—no actual emails go out.")
