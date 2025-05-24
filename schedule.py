import streamlit as st
import datetime
import os
import json
from openai import OpenAI

# --- Streamlit Page Config & Branding ---
st.set_page_config(
    page_title="🏠 Paint & Drywall Automator",
    page_icon="🏠",
    layout="wide"
)
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Sidebar logo
logo_path = "logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_column_width=True)
else:
    st.sidebar.markdown("## 🏠 Paint & Drywall Automator Demo")

# --- OpenAI Client Setup ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Data Persistence Utilities ---
DATA_FILE = "demo_data.json"
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"epo_log": [], "notes": []}
    return {"epo_log": [], "notes": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)

# Initialize or load session state
data = load_data()
if 'epo_log' not in st.session_state:
    st.session_state.epo_log = data.get('epo_log', [])
if 'notes' not in st.session_state:
    st.session_state.notes = data.get('notes', [])

# --- Business Constants & Logic ---
TASKS = ['Hang', 'Scrap', 'Tape', 'Bed', 'Skim', 'Sand']
COMMUNITIES = {
    'Galloway': {t: 'America Drywall' for t in TASKS},
    'Huntersville Town Center': {t: 'America Drywall' for t in TASKS},
    'Claremont': {
        'Hang': 'Ricardo', 'Scrap': 'Scrap Brothers',
        'Tape': 'Juan Trejo', 'Bed': 'Juan Trejo',
        'Skim': 'Juan Trejo', 'Sand': 'Juan Trejo'
    },
    'Context': {t: 'America Drywall' for t in TASKS},
    'Greenway Overlook': {t: 'America Drywall' for t in TASKS},
    'Camden': {t: 'America Drywall' for t in TASKS},
    'Olmstead': {
        'Hang': 'Ricardo', 'Scrap': 'Scrap Brothers',
        'Tape': 'Juan Trejo', 'Bed': 'Juan Trejo',
        'Skim': 'Juan Trejo', 'Sand': 'Juan Trejo'
    },
    'Maxwell': {t: 'America Drywall' for t in TASKS},
}
DUR = {'Hang': 1, 'Scrap': 1, 'Sand': 1, 'Tape': 2, 'Bed': 2, 'Skim': 2}
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
PAINT_SUBS = [
    'GP Painting Services', 'Jorge Gomez',
    'Christian Painting', 'Carlos Gabriel', 'Juan Ulloa'
]

def generate_schedule(comm, start_date):
    schedule = []
    cur = start_date
    for t in TASKS:
        days = DUR[t]
        skip_sun = (t != 'Scrap')
        skip_wk = (t == 'Scrap')
        added = 0
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday() >= 5: continue
            if skip_sun and cur.weekday() == 6: continue
            added += 1
        schedule.append((t, COMMUNITIES[comm].get(t, '—'), cur))
    return schedule

# --- LLM-Powered Note Classification ---
def classify_note_with_llm(lot, community, text):
    functions = [{
        "name": "classifyNote",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["EPO","MonitorHang","FinalPaint","Other"]},
                "dueDate": {"type": "string", "format": "date-time"},
                "priority": {"type": "string", "enum": ["High","Medium","Low"]},
                "emailDraft": {"type": "string"}
            },
            "required": ["category","emailDraft"]
        }
    }]
    messages = [
        {"role": "system", "content": "You’re an assistant that turns construction walk-through notes into action items."},
        {"role": "user", "content": f"Lot {lot} in {community}: {text}"}
    ]
    # Use the new OpenAI client interface
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=functions,
        function_call={"name": "classifyNote"}
    )
    fc = resp.choices[0].message.function_call
    args = json.loads(fc.arguments)
    return {
        "Lot": lot,
        "Community": community,
        "Note": text,
        "Category": args.get("category","Other"),
        "Due Date": args.get("dueDate",""),
        "Priority": args.get("priority",""),
        "Email Draft": args.get("emailDraft","")
    }

# --- Sidebar Navigation ---
st.sidebar.markdown("---")
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
    with st.form("schedule_form"):
        lot = st.text_input("Lot number", help="e.g. 89")
        comm = st.selectbox("Community", list(COMMUNITIES.keys()), help="Select a community")
        start = st.date_input("Start date", help="Project start date")
        go = st.form_submit_button("Generate Schedule")
    if go:
        sched = generate_schedule(comm, start)
        st.subheader(f"Schedule for Lot {lot} in {comm}")
        df = {
            'Task': [t for t,_,_ in sched],
            'Sub': [s for _,s,_ in sched],
            'Date': [d.strftime('%m/%d/%Y') for *_,d in sched]
        }
        st.table(df)
        if st.button("Order Mud for Scrap Date"):
            scrap_date = sched[1][2].strftime('%m/%d/%Y')
            st.success(f"📧 Mud order email queued for {scrap_date}")

# --- EPO & Tracker ---
elif mode == "EPO & Tracker":
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo_form", clear_on_submit=True):
        lot = st.text_input("Lot", help="Lot number e.g. 89")
        comm = st.selectbox("Community", list(COMMUNITIES.keys()))
        email_to = st.text_input("Builder Email", help="Email recipient")
        amt = st.text_input("Amount", help="EPO amount")
        photos = st.file_uploader("Attach photos", accept_multiple_files=True)
        send = st.form_submit_button("Send EPO")
    if send:
        now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
        entry = {'lot': lot, 'comm': comm, 'to': email_to,
                 'amt': amt, 'sent': now, 'replied': False, 'followup': False}
        st.session_state.epo_log.append(entry)
        save_data({'epo_log': st.session_state.epo_log, 'notes': st.session_state.notes})
        st.success(f"EPO for Lot {lot} [{comm}] recorded at {now}")

    st.subheader("📋 EPO Tracker")
    if st.session_state.epo_log:
        for i, e in enumerate(st.session_state.epo_log):
            cols = st.columns([1,1,1,1,1,1])
            cols[0].write(e['lot']); cols[1].write(e['comm']); cols[2].write(e['sent'])
            status = 'Replied' if e['replied'] else ('Follow-Up Sent' if e['followup'] else 'Pending')
            cols[3].write(status)
            if cols[4].button("Mark Replied", key=f"r{i}") and not e['replied']:
                e['replied'] = True
                save_data({'epo_log': st.session_state.epo_log, 'notes': st.session_state.notes})
            if cols[5].button("Send Follow-Up", key=f"f{i}") and not e['followup'] and not e['replied']:
                e['followup'] = True
                save_data({'epo_log': st.session_state.epo_log, 'notes': st.session_state.notes})
                st.info(f"🔔 Follow-up for Lot {e['lot']} queued.")
    else:
        st.info("No EPOs sent yet.")

# --- QC Scheduling ---
elif mode == "QC Scheduling":
    st.header("🔍 QC Scheduling")
    lot = st.text_input("Lot number", key='qc_lot')
    comm = st.selectbox("Community", list(COMMUNITIES.keys()), key='qc_comm')
    pu = st.date_input("QC Point-Up date", key='qc_pu')
    pd = st.date_input("QC Paint date", key='qc_paint')
    ps = st.selectbox("QC Paint subcontractor", PAINT_SUBS, key='qc_sub')
    sd = st.date_input("QC Stain Touch-Up date", key='qc_stain')
    if st.button("Schedule QC Tasks"):
        tasks = [
            {'Task': 'QC Point-Up', 'Sub': POINTUP_SUBS.get(comm,'—'), 'Date': pu.strftime('%m/%d/%Y')},
            {'Task': 'QC Paint', 'Sub': ps, 'Date': pd.strftime('%m/%d/%Y')},
            {'Task': 'QC Stain Touch-Up', 'Sub': 'Dorby', 'Date': sd.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)
        st.json({'lot': lot, 'community': comm, 'qc_tasks': tasks})

# --- Homeowner Scheduling ---
elif mode == "Homeowner Scheduling":
    st.header("🏠 Homeowner Scheduling")
    lot = st.text_input("Lot number", key='ho_lot')
    comm = st.selectbox("Community", list(COMMUNITIES.keys()), key='ho_comm')
    pu = st.date_input("HO Point-Up date", key='ho_pu')
    pd = st.date_input("HO Paint date", key='ho_paint')
    ps = st.selectbox("HO Paint subcontractor", PAINT_SUBS, key='ho_sub')
    if st.button("Schedule Homeowner Tasks"):
        tasks = [
            {'Task': 'HO Point-Up', 'Sub': POINTUP_SUBS.get(comm,'—'), 'Date': pu.strftime('%m/%d/%Y')},
            {'Task': 'HO Paint', 'Sub': ps, 'Date': pd.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)
        st.json({'lot': lot, 'community': comm, 'homeowner_tasks': tasks})

# --- Note Taking with LLM Classification ---
elif mode == "Note Taking":
    st.header("📝 Smart Note Taking")
    comm = st.selectbox("Community Context", list(COMMUNITIES.keys()), key='note_comm')
    raw = st.text_area("Enter notes (format: Lot### - your note)", height=150)
    photos = st.file_uploader("Attach photos (optional)", accept_multiple_files=True)
    if st.button("Classify & Parse Notes"):
        st.session_state.notes = []
        for line in raw.splitlines():
            if not line.strip(): continue
            parts = line.split('-', 1)
            lot_code = parts[0].strip()
            note_txt = parts[1].strip() if len(parts)>1 else parts[0].strip()
            item = classify_note_with_llm(lot_code, comm, note_txt)
            st.session_state.notes.append(item)
        save_data({'epo_log': st.session_state.epo_log, 'notes': st.session_state.notes})

    if st.session_state.notes:
        st.subheader("Action Items")
        st.table(st.session_state.notes)
    else:
        st.info("No notes parsed yet.")

# --- Sidebar Footer ---
st.sidebar.markdown("---")
st.sidebar.write("This is a **demo only** — no actual emails or reminders are sent.")
