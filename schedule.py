import streamlit as st
import datetime
import os
import json
from openai import OpenAI

# --- Streamlit Config & Branding ---
st.set_page_config(
    page_title="🏠 Paint & Drywall Automator",
    page_icon="🏠",
    layout="wide"
)
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer     {visibility: hidden;}
        header     {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Sidebar logo
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 🏠 Paint & Drywall Automator Demo")

# --- Load & Mask API Key ---
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
if api_key:
    st.sidebar.write("🔑 Key loaded:", api_key[:5] + "…" + api_key[-5:])
else:
    st.sidebar.error("❌ No OpenAI key found in env or secrets!")
    st.stop()

# Instantiate OpenAI client
client = OpenAI(api_key=api_key)

# --- Data Persistence Utilities ---
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
        days = DUR[task]
        skip_sun = (task != 'Scrap')
        skip_wk  = (task == 'Scrap')
        added = 0
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday() >= 5:    continue
            if skip_sun and cur.weekday() == 6:   continue
            added += 1
        schedule.append((task, COMMUNITIES[community].get(task, '—'), cur))
    return schedule

def classify_note_with_llm(lot, community, text):
    functions = [{
        "name": "classifyNote",
        "parameters": {
            "type": "object",
            "properties": {
                "category":   {"type": "string","enum":["EPO","MonitorHang","FinalPaint","Other"]},
                "dueDate":    {"type": "string","format":"date-time"},
                "priority":   {"type": "string","enum":["High","Medium","Low"]},
                "emailDraft": {"type": "string"}
            },
            "required": ["category","emailDraft"]
        }
    }]
    messages = [
        {"role":"system","content":"You’re an assistant that turns walk-through notes into actionable tasks."},
        {"role":"user","content":f"Lot {lot} in {community}: {text}"}
    ]
    # switch to the supported gpt-3.5-turbo model
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call={"name":"classifyNote"}
    )
    call = res.choices[0].message.function_call
    args = json.loads(call.arguments)
    return {
        "Lot": lot,
        "Community": community,
        "Note": text,
        "Category": args["category"],
        "Due Date": args.get("dueDate",""),
        "Priority": args.get("priority",""),
        "Email Draft": args["emailDraft"]
    }

# --- Sidebar Navigation & Debug ---
st.sidebar.markdown("---")
mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule & Order Mud","EPO & Tracker","QC Scheduling",
    "Homeowner Scheduling","Note Taking"
])
st.sidebar.write(f"🐛 MODE: {mode}")

# --- Schedule & Order Mud ---
if mode == "Schedule & Order Mud":
    st.sidebar.write("🐛 BRANCH: Schedule")
    st.header("📆 Schedule Generator & Mud Order")
    with st.form("schedule_form"):
        lot       = st.text_input("Lot number")
        community = st.selectbox("Community", list(COMMUNITIES))
        start     = st.date_input("Start date")
        go        = st.form_submit_button("Generate Schedule")
    if go:
        sched = generate_schedule(community, start)
        st.table({
            'Task':[t for t,_,_ in sched],
            'Sub': [s for _,s,_ in sched],
            'Date':[d.strftime('%m/%d/%Y') for *_,d in sched]
        })
        if st.button("Order Mud for Scrap Date"):
            scrap_date = sched[1][2].strftime('%m/%d/%Y')
            st.success(f"📧 Mud order email queued for {scrap_date}")

# --- EPO & Tracker ---
elif mode == "EPO & Tracker":
    st.sidebar.write("🐛 BRANCH: EPO")
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo_form", clear_on_submit=True):
        lot      = st.text_input("Lot number")
        community= st.selectbox("Community", list(COMMUNITIES))
        email_to = st.text_input("Builder Email")
        amount   = st.text_input("Amount")
        photos   = st.file_uploader("Attach photos", accept_multiple_files=True)
        send     = st.form_submit_button("Send EPO")
    if send:
        now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
        entry = {'lot':lot,'comm':community,'to':email_to,
                 'amt':amount,'sent':now,'replied':False,'followup':False}
        st.session_state.epo_log.append(entry)
        save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
        st.success(f"EPO for Lot {lot} recorded at {now}")
    st.subheader("📋 EPO Tracker")
    if st.session_state.epo_log:
        for i,e in enumerate(st.session_state.epo_log):
            cols = st.columns(6)
            cols[0].write(e['lot']); cols[1].write(e['comm']); cols[2].write(e['sent'])
            status = 'Replied' if e['replied'] else ('Follow-Up Sent' if e['followup'] else 'Pending')
            cols[3].write(status)
            if not e['replied'] and cols[4].button("Mark Replied", key=f"r{i}"):
                e['replied'] = True
                save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
            if not e['followup'] and not e['replied'] and cols[5].button("Send Follow-Up", key=f"f{i}"):
                e['followup'] = True
                save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
                st.info(f"🔔 Follow-up for Lot {e['lot']} queued.")
    else:
        st.info("No EPOs yet.")

# --- QC Scheduling ---
elif mode == "QC Scheduling":
    st.sidebar.write("🐛 BRANCH: QC")
    st.header("🔍 QC Scheduling")
    lot        = st.text_input("Lot number", key='qc_lot')
    community  = st.selectbox("Community", list(COMMUNITIES), key='qc_comm')
    pu_date    = st.date_input("QC Point-Up date", key='qc_pu')
    paint_date = st.date_input("QC Paint date", key='qc_paint')
    paint_sub  = st.selectbox("QC Paint subcontractor", PAINT_SUBS, key='qc_sub')
    stain_date = st.date_input("QC Stain Touch-Up date", key='qc_stain')
    if st.button("Schedule QC Tasks"):
        tasks = [
            {'Task':'QC Point-Up', 'Sub':POINTUP_SUBS.get(community,'—'), 'Date':pu_date.strftime('%m/%d/%Y')},
            {'Task':'QC Paint',    'Sub':paint_sub,                      'Date':paint_date.strftime('%m/%d/%Y')},
            {'Task':'QC Stain',    'Sub':'Dorby',                        'Date':stain_date.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)
        st.json({'lot':lot,'comm':community,'qc_tasks':tasks})

# --- Homeowner Scheduling ---
elif mode == "Homeowner Scheduling":
    st.sidebar.write("🐛 BRANCH: Homeowner")
    st.header("🏠 Homeowner Scheduling")
    lot        = st.text_input("Lot number", key='ho_lot')
    community  = st.selectbox("Community", list(COMMUNITIES), key='ho_comm')
    pu_date    = st.date_input("HO Point-Up date", key='ho_pu')
    paint_date = st.date_input("HO Paint date", key='ho_paint')
    paint_sub  = st.selectbox("HO Paint subcontractor", PAINT_SUBS, key='ho_sub')
    if st.button("Schedule Homeowner Tasks"):
        tasks = [
            {'Task':'HO Point-Up', 'Sub':POINTUP_SUBS.get(community,'—'), 'Date':pu_date.strftime('%m/%d/%Y')},
            {'Task':'HO Paint',    'Sub':paint_sub,                       'Date':paint_date.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)
        st.json({'lot':lot,'comm':community,'home_tasks':tasks})

# --- Note Taking with Auth Test & Classification ---
elif mode == "Note Taking":
    st.sidebar.write("🐛 BRANCH: Note Taking")
    st.header("📝 Smart Note Taking")
    community = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    raw       = st.text_area("Enter notes (Lot### - your note)", height=150)
    if st.button("Classify & Parse"):
        # clear previous
        st.session_state.notes = []
        # auth test
        try:
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"system","content":"ping"}]
            )
            st.sidebar.success("🛠️ OpenAI auth test: OK")
        except Exception as e:
            st.sidebar.error(f"🛠️ OpenAI auth test failed: {e}")
        # real classification
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = line.split('-', 1)
            lot_code = parts[0].strip()
            note_txt = parts[1].strip() if len(parts)>1 else ""
            item = classify_note_with_llm(lot_code, community, note_txt)
            st.session_state.notes.append(item)
        save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
    if st.session_state.notes:
        st.table(st.session_state.notes)
    else:
        st.info("No notes yet.")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.write("Demo only—no real emails or reminders.")
