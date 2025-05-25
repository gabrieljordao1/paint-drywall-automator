import streamlit as st
import datetime
import os
import json

# ─── 1) PAGE CONFIG (must be first) ────────────────────────────────────────────
st.set_page_config(
    page_title="Paint & Drywall Automator",
    page_icon="🏠",
    layout="wide"
)

# ─── 2) EMBED BACKGROUND via <body> ────────────────────────────────────────────
# Paste your Base64 string here (no line-breaks):
B64_BG = "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"
st.markdown(f"""
    <style>
      body {{
        background-image: url("data:image/png;base64,{B64_BG}");
        background-repeat: no-repeat;
        background-position: center center;
        background-size: cover;
        background-attachment: fixed;
      }}
      /* Make sure Streamlit containers are transparent so bg shows through */
      .css-1d391kg, .css-1lcbmhc {{
        background-color: transparent !important;
      }}
    </style>
""", unsafe_allow_html=True)

# ─── 3) HIDE STREAMLIT CHROME ──────────────────────────────────────────────────
st.markdown("""
    <style>
      #MainMenu { visibility: hidden; }
      footer     { visibility: hidden; }
      header     { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ─── 4) OPTIONAL SIDEBAR LOGO ──────────────────────────────────────────────────
if os.path.exists("stancillogo.png"):
    st.sidebar.image("stancillogo.png", use_column_width=True)

# ─── 5) DATA PERSISTENCE ──────────────────────────────────────────────────────
DATA_FILE = "demo_data.json"
def load_data():
    try:
        return json.load(open(DATA_FILE))
    except:
        return {"epo_log": [], "notes": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)

st.session_state.setdefault('epo_log', load_data().get('epo_log', []))
st.session_state.setdefault('notes',    load_data().get('notes',    []))

# ─── 6) BUSINESS CONSTANTS & HELPERS ──────────────────────────────────────────
TASKS = ['Hang','Scrap','Tape','Bed','Skim','Sand']
COMMUNITIES = {
    'Galloway': {t:'America Drywall' for t in TASKS},
    'Huntersville Town Center': {t:'America Drywall' for t in TASKS},
    'Claremont': {
        'Hang':'Ricardo','Scrap':'Scrap Brothers',
        'Tape':'Juan Trejo','Bed':'Juan Trejo',
        'Skim':'Juan Trejo','Sand':'Juan Trejo'
    },
    'Context': {t:'America Drywall' for t in TASKS},
    'Greenway Overlook': {t:'America Drywall' for t in TASKS},
    'Camden': {t:'America Drywall' for t in TASKS},
    'Olmstead': {
        'Hang':'Ricardo','Scrap':'Scrap Brothers',
        'Tape':'Juan Trejo','Bed':'Juan Trejo',
        'Skim':'Juan Trejo','Sand':'Juan Trejo'
    },
    'Maxwell': {t:'America Drywall' for t in TASKS},
}
DUR = {'Hang':1,'Scrap':1,'Sand':1,'Tape':2,'Bed':2,'Skim':2}
POINTUP_SUBS = {
    'Galloway':'Luis A. Lopez','Huntersville Town Center':'Luis A. Lopez',
    'Claremont':'Edwin','Context':'Edwin','Greenway Overlook':'Edwin',
    'Camden':'Luis A. Lopez','Olmstead':'Luis A. Lopez','Maxwell':'Luis A. Lopez'
}
PAINT_SUBS = [
    'GP Painting Services','Jorge Gomez',
    'Christian Painting','Carlos Gabriel','Juan Ulloa'
]

def generate_schedule(community, start_date):
    schedule, cur = [], start_date
    for task in TASKS:
        days = DUR[task]; added = 0
        skip_sun, skip_wk = (task!='Scrap'), (task=='Scrap')
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday()>=5: continue
            if skip_sun and cur.weekday()==6: continue
            added += 1
        schedule.append((task, COMMUNITIES[community].get(task,'—'), cur))
    return schedule

def classify_note_locally(lot, community, text):
    txt = text.lower()
    action, sub, due, email_to, email_draft = 'Note Logged','','','',''
    if any(k in txt for k in ['clean-out','clean out','schedule clean']):
        action, sub, due = 'Schedule Clean-Out Materials','Scrap Truck',\
            (datetime.datetime.now()+datetime.timedelta(days=1)).strftime('%m/%d/%Y')
    elif 'drywall' in txt and 'frame' in txt:
        action = 'Monitor Hang'
    elif any(kw in txt for kw in ['ready for final','final paint','final point up']):
        action, email_to = 'Notify Final Point-Up/Paint','office@scheduling.example.com'
        email_draft = (f"Hi team,\n\nLot {lot} in {community} appears ready for final point-up/paint.\n"
                       "Please confirm scheduling.\n\nThanks.")
    elif 'epo' in txt:
        action = 'Request EPO'
    return {
        "Lot": lot, "Community": community, "Note": text,
        "Next Action": action, "Sub": sub, "Due Date": due,
        "Email To": email_to, "Email Draft": email_draft
    }

# ─── 7) SIDEBAR NAVIGATION ─────────────────────────────────────────────────────
st.sidebar.markdown("---")
mode = st.sidebar.selectbox("Mode", [
    "Schedule & Order Mud","EPO & Tracker",
    "QC Scheduling","Homeowner Scheduling","Note Taking"
])

# ─── 8) SCHEDULE & ORDER MUD ──────────────────────────────────────────────────
if mode=="Schedule & Order Mud":
    st.header("📆 Schedule Generator & Mud Order")
    with st.form("sch"):
        lot, comm = st.text_input("Lot number"), st.selectbox("Community", list(COMMUNITIES))
        start, go = st.date_input("Start date"), st.form_submit_button("Generate Schedule")
    if go:
        sched = generate_schedule(comm, start)
        st.table({'Task':[t for t,_,_ in sched],'Sub':[s for _,s,_ in sched],
                  'Date':[d.strftime('%m/%d/%Y') for *_,d in sched]})
        if st.button("Order Mud for Scrap Date"):
            st.success(f"Mud order queued for {sched[1][2].strftime('%m/%d/%Y')}")

# ─── 9) EPO & TRACKER ─────────────────────────────────────────────────────────
elif mode=="EPO & Tracker":
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo", clear_on_submit=True):
        lot     = st.text_input("Lot number")
        comm    = st.selectbox("Community", list(COMMUNITIES))
        to_addr = st.text_input("Builder Email")
        amt     = st.text_input("Amount")
        photos  = st.file_uploader("Attach photos", accept_multiple_files=True)
        send    = st.form_submit_button("Send EPO")
    if send:
        now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
        st.session_state.epo_log.append({'lot':lot,'comm':comm,'to':to_addr,
                                         'amt':amt,'sent':now,'replied':False,'followup':False})
        save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
        st.success(f"EPO for Lot {lot} recorded at {now}")
    st.subheader("📋 EPO Tracker")
    if st.session_state.epo_log:
        for i,e in enumerate(st.session_state.epo_log):
            c = st.columns(6)
            c[0].write(e['lot']); c[1].write(e['comm']); c[2].write(e['sent'])
            status = 'Replied' if e['replied'] else ('Follow-Up Sent' if e['followup'] else 'Pending')
            c[3].write(status)
            if not e['replied'] and c[4].button("Mark Replied", key=f"r{i}"):
                e['replied']=True; save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
            if not e['followup'] and not e['replied'] and c[5].button("Send Follow-Up", key=f"f{i}"):
                e['followup']=True; save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
                st.info(f"🔔 Follow-up queued for Lot {e['lot']}")
    else:
        st.info("No EPOs yet.")

# ─── 10) QC SCHEDULING ─────────────────────────────────────────────────────────
elif mode=="QC Scheduling":
    st.header("🔍 QC Scheduling")
    lot = st.text_input("Lot number", key='qc_lot')
    comm = st.selectbox("Community", list(COMMUNITIES), key='qc_comm')
    pu, pd, ps, sd = (st.date_input("QC Point-Up date", key='qc_pu'),
                      st.date_input("QC Paint date", key='qc_paint'),
                      st.selectbox("QC Paint subcontractor", PAINT_SUBS, key='qc_sub'),
                      st.date_input("QC Stain Touch-Up date", key='qc_stain'))
    if st.button("Schedule QC Tasks"):
        tlist = [{'Task':'QC Point-Up','Sub':POINTUP_SUBS.get(comm,'—'),'Date':pu.strftime('%m/%d/%Y')},
                 {'Task':'QC Paint','Sub':ps,'Date':pd.strftime('%m/%d/%Y')},
                 {'Task':'QC Stain','Sub':'Dorby','Date':sd.strftime('%m/%d/%Y')}]
        st.table(tlist)

# ─── 11) HOMEOWNER SCHEDULING ─────────────────────────────────────────────────
elif mode=="Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    lot = st.text_input("Lot number", key='ho_lot')
    comm = st.selectbox("Community", list(COMMUNITIES), key='ho_comm')
    pu, pd, ps = (st.date_input("HO Point-Up date", key='ho_pu'),
                  st.date_input("HO Paint date", key='ho_paint'),
                  st.selectbox("HO Paint subcontractor", PAINT_SUBS, key='ho_sub'))
    if st.button("Schedule Homeowner Tasks"):
        hlist = [{'Task':'HO Point-Up','Sub':POINTUP_SUBS.get(comm,'—'),'Date':pu.strftime('%m/%d/%Y')},
                 {'Task':'HO Paint','Sub':ps,'Date':pd.strftime('%m/%d/%Y')}]
        st.table(hlist)

# ─── 12) NOTE TAKING ───────────────────────────────────────────────────────────
elif mode=="Note Taking":
    st.header("📝 Smart Note Taking")
    comm = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    raw = st.text_area("Enter notes (e.g. 1234 your note)", height=150)
    if st.button("Parse Notes"):
        st.session_state.notes=[]
        for ln in raw.splitlines():
            if not ln.strip(): continue
            parts = ln.strip().split(" ",1)
            lotc = parts[0]; note = parts[1] if len(parts)>1 else ""
            st.session_state.notes.append(classify_note_locally(lotc, comm, note))
        save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
    if st.session_state.notes:
        cols=["Lot","Community","Note","Next Action","Sub","Due Date","Email To","Email Draft"]
        tbl={c:[n.get(c,"") for n in st.session_state.notes] for c in cols}
        st.table(tbl)
    else:
        st.info("No notes yet.")

# ─── 13) FOOTER ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.write("Demo only — no real emails or reminders.")
