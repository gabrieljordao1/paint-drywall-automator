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
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 🏠 Paint & Drywall Automator Demo")

# --- Load & Mask API Key ---
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
if api_key:
    st.sidebar.write("🔑 Key loaded:", api_key[:5] + "…" + api_key[-5:])
else:
    st.sidebar.error("❌ No OpenAI key found! Check your Secrets.")
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
    'Galloway':'Luis A. Lopez',
    'Huntersville Town Center':'Luis A. Lopez',
    'Claremont':'Edwin',
    'Context':'Edwin',
    'Greenway Overlook':'Edwin',
    'Camden':'Luis A. Lopez',
    'Olmstead':'Luis A. Lopez',
    'Maxwell':'Luis A. Lopez'
}
PAINT_SUBS = [
    'GP Painting Services',
    'Jorge Gomez',
    'Christian Painting',
    'Carlos Gabriel',
    'Juan Ulloa'
]

def generate_schedule(comm, start_date):
    sched, cur = [], start_date
    for t in TASKS:
        days = DUR[t]
        skip_sun, skip_wk = (t!='Scrap'), (t=='Scrap')
        added = 0
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday() >= 5: continue
            if skip_sun and cur.weekday() == 6: continue
            added += 1
        sched.append((t, COMMUNITIES[comm].get(t,'—'), cur))
    return sched

def classify_note_with_llm(lot, community, text):
    fn = [{
      "name":"classifyNote",
      "parameters":{
        "type":"object",
        "properties":{
          "category": {"type":"string","enum":["EPO","MonitorHang","FinalPaint","Other"]},
          "dueDate":  {"type":"string","format":"date-time"},
          "priority": {"type":"string","enum":["High","Medium","Low"]},
          "emailDraft":{"type":"string"}
        },
        "required":["category","emailDraft"]
      }
    }]
    msgs = [
      {"role":"system","content":"You’re an assistant that turns walk-through notes into actionable tasks."},
      {"role":"user","content":f"Lot {lot} in {community}: {text}"}
    ]
    res = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=msgs,
      functions=fn,
      function_call={"name":"classifyNote"}
    )
    call = res.choices[0].message.function_call
    args = json.loads(call.arguments)
    return {
      "Lot": lot,
      "Community": community,
      "Note": text,
      "Category": args.get("category","Other"),
      "Due Date": args.get("dueDate",""),
      "Priority": args.get("priority",""),
      "Email Draft": args.get("emailDraft","")
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
    with st.form("sch"):
        lot   = st.text_input("Lot number")
        comm  = st.selectbox("Community", list(COMMUNITIES))
        start = st.date_input("Start date")
        go    = st.form_submit_button("Generate Schedule")
    if go:
        sched = generate_schedule(comm, start)
        st.table({
            'Task':[t for t,_,_ in sched],
            'Sub': [s for _,s,_ in sched],
            'Date':[d.strftime('%m/%d/%Y') for *_,d in sched]
        })
        # Auth test
        try:
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"ping"}]
            )
            st.sidebar.success("🛠️ OpenAI auth test: OK")
        except Exception as e:
            st.sidebar.error(f"🛠️ OpenAI auth test failed: {e}")

# --- EPO & Tracker ---
elif mode == "EPO & Tracker":
    st.sidebar.write("🐛 BRANCH: EPO")
    st.header("✉️ EPO Automation & Tracker")
    with st.form("epo", clear_on_submit=True):
        lot      = st.text_input("Lot number")
        comm     = st.selectbox("Community", list(COMMUNITIES))
        email_to = st.text_input("Builder Email")
        amt      = st.text_input("Amount")
        photos   = st.file_uploader("Photos", accept_multiple_files=True)
        send     = st.form_submit_button("Send EPO")
    if send:
        now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
        entry = {'lot':lot,'comm':comm,'to':email_to,
                 'amt':amt,'sent':now,'replied':False,'followup':False}
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
                e['replied']=True; save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
            if not e['followup'] and not e['replied'] and cols[5].button("Send Follow-Up", key=f"f{i}"):
                e['followup']=True; save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
                st.info(f"🔔 Follow-up for Lot {e['lot']} queued.")
    else:
        st.info("No EPOs yet.")

# --- QC Scheduling ---
elif mode == "QC Scheduling":
    st.sidebar.write("🐛 BRANCH: QC")
    st.header("🔍 QC Scheduling")
    lot        = st.text_input("Lot number", key='qc_lot')
    comm       = st.selectbox("Community", list(COMMUNITIES), key='qc_comm')
    pu_date    = st.date_input("QC Point-Up date", key='qc_pu')
    paint_date = st.date_input("QC Paint date", key='qc_paint')
    paint_sub  = st.selectbox("QC Paint sub", PAINT_SUBS, key='qc_sub')
    stain_date = st.date_input("QC Stain date", key='qc_stain')
    if st.button("Schedule QC Tasks"):
        tasks = [
            {'Task':'QC Point-Up','Sub':POINTUP_SUBS.get(comm,'—'),'Date':pu_date.strftime('%m/%d/%Y')},
            {'Task':'QC Paint',   'Sub':paint_sub,                      'Date':paint_date.strftime('%m/%d/%Y')},
            {'Task':'QC Stain',   'Sub':'Dorby',                        'Date':stain_date.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)
        st.json({'lot':lot,'comm':comm,'qc_tasks':tasks})

# --- Homeowner Scheduling ---
elif mode == "Homeowner Scheduling":
    st.sidebar.write("🐛 BRANCH: Homeowner")
    st.header("🏠 Homeowner Scheduling")
    lot        = st.text_input("Lot number", key='ho_lot')
    comm       = st.selectbox("Community", list(COMMUNITIES), key='ho_comm')
    pu_date    = st.date_input("HO Point-Up date", key='ho_pu')
    paint_date = st.date_input("HO Paint date", key='ho_paint')
    paint_sub  = st.selectbox("HO Paint sub", PAINT_SUBS, key='ho_sub')
    if st.button("Schedule Homeowner Tasks"):
        tasks = [
            {'Task':'HO Point-Up','Sub':POINTUP_SUBS.get(comm,'—'),'Date':pu_date.strftime('%m/%d/%Y')},
            {'Task':'HO Paint',  'Sub':paint_sub,                    'Date':paint_date.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)
        st.json({'lot':lot,'comm':comm,'home_tasks':tasks})

# --- Note Taking with LLM Classification ---
elif mode == "Note Taking":
    st.sidebar.write("🐛 BRANCH: Note Taking")
    st.header("📝 Smart Note Taking")
    comm = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    raw  = st.text_area("Enter notes (Lot### - your note)", height=150)
    if st.button("Classify & Parse"):
        st.session_state.notes = []
        for line in raw.splitlines():
            if not line.strip(): continue
            lot_code, note_txt = (line.split('-',1) + [""])[0:2]
            item = classify_note_with_llm(lot_code.strip(), comm, note_txt.strip())
            st.session_state.notes.append(item)
        save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
    if st.session_state.notes:
        st.table(st.session_state.notes)
    else:
        st.info("No notes yet.")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.write("Demo only—no real emails or reminders.")
