import streamlit as st
import datetime
import re

# --- Business logic ---
TASKS = ['Hang', 'Scrap', 'Tape', 'Bed', 'Skim', 'Sand']
COMMUNITIES = {
    'Galloway': {t:'America Drywall' for t in TASKS},
    'Huntersville Town Center': {t:'America Drywall' for t in TASKS},
    'Claremont': {
        'Hang':'Ricardo','Scrap':'Scrap Brothers','Tape':'Juan Trejo',
        'Bed':'Juan Trejo','Skim':'Juan Trejo','Sand':'Juan Trejo'
    },
    'Context': {t:'America Drywall' for t in TASKS},
    'Greenway Overlook': {t:'America Drywall' for t in TASKS},
    'Camden': {t:'America Drywall' for t in TASKS},
    'Olmstead': {
        'Hang':'Ricardo','Scrap':'Scrap Brothers','Tape':'Juan Trejo',
        'Bed':'Juan Trejo','Skim':'Juan Trejo','Sand':'Juan Trejo'
    },
    'Maxwell': {t:'America Drywall' for t in TASKS},
}
# Phase durations
DUR = {'Hang':1,'Scrap':1,'Sand':1,'Tape':2,'Bed':2,'Skim':2}
# Point-up subcontractors
POINTUP_SUBS = {
    'Galloway':'Luis A. Lopez','Huntersville Town Center':'Luis A. Lopez',
    'Claremont':'Edwin','Context':'Edwin','Greenway Overlook':'Edwin',
    'Camden':'Luis A. Lopez','Olmstead':'Luis A. Lopez','Maxwell':'Luis A. Lopez'
}
# Paint subcontractors
PAINT_SUBS = ['GP Painting Services','Jorge Gomez','Christian Painting','Carlos Gabriel','Juan Ulloa']

# Initialize session state
if 'epo_log' not in st.session_state:
    st.session_state.epo_log = []
if 'notes' not in st.session_state:
    st.session_state.notes = []

st.set_page_config(page_title="Paint & Drywall Automator Demo")
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
    st.header("📆 Schedule Generator & Mud Order")
    lot = st.text_input("Lot number")
    comm = st.selectbox("Community", list(COMMUNITIES.keys()))
    start = st.date_input("Start date (MM/DD/YYYY)")
    schedule = []
    if st.button("Generate Schedule"):
        cur = start
        for t in TASKS:
            days = DUR[t]
            skip_sun = (t != 'Scrap')
            skip_wk = (t == 'Scrap')
            d, added = cur, 0
            while added < days:
                d += datetime.timedelta(days=1)
                if skip_wk and d.weekday() >= 5:
                    continue
                if skip_sun and d.weekday() == 6:
                    continue
                added += 1
            schedule.append((t, COMMUNITIES[comm][t], d.strftime('%m/%d/%Y')))
            cur = d
        st.table({
            'Task': [x[0] for x in schedule],
            'Subcontractor': [x[1] for x in schedule],
            'Date': [x[2] for x in schedule]
        })
    if st.button("Order Mud for Scrap Date"):
        if schedule:
            st.success(f"📧 Mud order for {schedule[1][2]}")
        else:
            st.warning("Generate schedule first.")

# --- EPO & Tracker ---
elif mode == "EPO & Tracker":
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo_form"):
        c1, c2 = st.columns(2)
        lot = c1.text_input("Lot")
        comm = c1.selectbox("Community", list(COMMUNITIES.keys()))
        builder = c2.text_input("Builder Email")
        amount = c2.text_input("Amount")
        photos = st.file_uploader("Attach photos", accept_multiple_files=True)
        submit_epo = st.form_submit_button("Send EPO")
    if submit_epo:
        now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
        st.success(f"EPO for Lot {lot} {comm} recorded at {now}")
        st.session_state.epo_log.append({
            'lot': lot, 'comm': comm, 'to': builder,
            'amt': amount, 'sent': now, 'replied': False, 'followup': False
        })
    st.subheader("📋 EPO Tracker")
    if st.session_state.epo_log:
        for i, e in enumerate(st.session_state.epo_log):
            cols = st.columns(6)
            cols[0].write(e['lot']); cols[1].write(e['comm']); cols[2].write(e['sent'])
            status = 'Replied' if e['replied'] else ('Follow-Up Sent' if e['followup'] else 'Pending')
            cols[3].write(status)
            if not e['replied'] and cols[4].button('Mark Replied', key=f'r{i}'):
                e['replied'] = True
            if not e['followup'] and not e['replied'] and cols[5].button('Send Follow-Up', key=f'f{i}'):
                e['followup'] = True; st.info(f"🔔 Follow-up for Lot {e['lot']} queued.")
    else:
        st.write("No EPOs sent yet.")

# --- QC Scheduling ---
elif mode == "QC Scheduling":
    st.header("🔍 QC Scheduling")
    lot = st.text_input("Lot number", key='qc_lot')
    comm = st.selectbox("Community", list(COMMUNITIES.keys()), key='qc_comm')
    pu = st.date_input("QC Point-Up date", key='qc_pu')
    paint_date = st.date_input("QC Paint date", key='qc_paint_date')
    paint_sub = st.selectbox("QC Paint Subcontractor", PAINT_SUBS, key='qc_paint_sub')
    stain_date = st.date_input("QC Stain Touch-Up date", key='qc_stain')
    if st.button("Schedule QC Tasks"):
        tasks = [
            {'task': 'QC Point-Up',           'sub': POINTUP_SUBS.get(comm, '—'), 'date': pu.strftime('%m/%d/%Y')},
            {'task': 'QC Paint',              'sub': paint_sub,                 'date': paint_date.strftime('%m/%d/%Y')},
            {'task': 'QC Stain Touch-Up',     'sub': 'Dorby',                    'date': stain_date.strftime('%m/%d/%Y')}
        ]
        st.table(tasks); st.json({'lot': lot, 'comm': comm, 'qc_tasks': tasks})

# --- Homeowner Scheduling ---
elif mode == "Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    lot = st.text_input("Lot number", key='ho_lot')
    comm = st.selectbox("Community", list(COMMUNITIES.keys()), key='ho_comm')
    pu = st.date_input("HO Point-Up date", key='ho_pu')
    paint_date = st.date_input("HO Paint date", key='ho_paint_date')
    paint_sub = st.selectbox("HO Paint Subcontractor", PAINT_SUBS, key='ho_paint_sub')
    if st.button("Schedule Homeowner Tasks"):
        tasks = [
            {'task': 'HO Point-Up', 'sub': POINTUP_SUBS.get(comm, '—'), 'date': pu.strftime('%m/%d/%Y')},
            {'task': 'HO Paint',    'sub': paint_sub,                     'date': paint_date.strftime('%m/%d/%Y')}
        ]
        st.table(tasks); st.json({'lot': lot, 'comm': comm, 'ho_tasks': tasks})

# --- Note Taking ---
elif mode == "Note Taking":
    st.header("📝 Note Taking")
    comm = st.selectbox("Community Context", list(COMMUNITIES.keys()), key='note_comm')
    notes_input = st.text_area("Enter notes (Lot### - note)")
    if st.button("Parse Notes"):
        st.session_state.notes = []
        for line in notes_input.splitlines():
            line = line.strip()
            if not line: continue
            parts = line.split('-', 1)
            lot_code = parts[0].strip() if len(parts) > 1 else 'Unknown'
            note_txt = parts[1].strip() if len(parts) > 1 else line
            action = 'Note Logged'; follow = ''
            lt = note_txt.lower()
            if 'hung' in lt and 'scrap' in lt:
                action = 'Notify Clean-Out Materials'
            elif 'drywall' in lt and 'frame' in lt:
                action = 'Monitor Hang'; follow = (datetime.datetime.now() + datetime.timedelta(hours=48)).strftime('%m/%d/%Y %H:%M')
            elif 'ready for final' in lt:
                action = 'Notify Schedule Dept for Final Paint'
            st.session_state.notes.append({'Community': comm,'Lot': lot_code,'Note': note_txt,'Next Action': action,'Follow-Up': follow})
    if st.session_state.notes:
        st.table(st.session_state.notes)
    else:
        st.info("No notes parsed yet.")

# Sidebar
st.sidebar.markdown("---")
st.sidebar.write("This is a **demo only**—no actual emails go out.")
