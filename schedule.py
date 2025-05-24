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
# show masked snippet so you know your key is actually loaded
if api_key:
    st.sidebar.write("🔑 Key loaded:", api_key[:5] + "…" + api_key[-5:])
else:
    st.sidebar.error("❌ No OpenAI key found! Check your Secrets.")
    st.stop()

# instantiate the new client
client = OpenAI(api_key=api_key)

# --- Data Persistence Utilities ---
DATA_FILE = "demo_data.json"
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return json.load(open(DATA_FILE))
        except:
            return {"epo_log": [], "notes": []}
    return {"epo_log": [], "notes": []}

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, default=str, indent=2)

st.session_state.setdefault('epo_log', load_data().get('epo_log', []))
st.session_state.setdefault('notes',    load_data().get('notes',    []))

# --- Business Constants & Logic ---
TASKS = ['Hang','Scrap','Tape','Bed','Skim','Sand']
# ... COMMUNITIES, DUR, POINTUP_SUBS, PAINT_SUBS definitions as before ...

def generate_schedule(comm, start_date):
    sched, cur = [], start_date
    for t in TASKS:
        days = DUR[t]
        skip_sun, skip_wk = (t!='Scrap'), (t=='Scrap')
        added = 0
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday()>=5: continue
            if skip_sun and cur.weekday()==6: continue
            added += 1
        sched.append((t, COMMUNITIES[comm].get(t,'—'), cur))
    return sched

def classify_note_with_llm(lot, community, text):
    fn = [{
      "name":"classifyNote",
      "parameters":{
        "type":"object",
        "properties":{
          "category":{"type":"string","enum":["EPO","MonitorHang","FinalPaint","Other"]},
          "dueDate":{"type":"string","format":"date-time"},
          "priority":{"type":"string","enum":["High","Medium","Low"]},
          "emailDraft":{"type":"string"}
        },
        "required":["category","emailDraft"]
      }
    }]
    msgs = [
      {"role":"system","content":"You’re an assistant that turns construction notes into action items."},
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
      "Lot": lot, "Community": community, "Note": text,
      "Category": args.get("category","Other"),
      "Due Date": args.get("dueDate",""),
      "Priority": args.get("priority",""),
      "Email Draft": args.get("emailDraft","")
    }

# --- Sidebar Navigation & Debugging ---
st.sidebar.markdown("---")
mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule & Order Mud","EPO & Tracker","QC Scheduling",
    "Homeowner Scheduling","Note Taking"
])
st.sidebar.write(f"🐛 MODE: {mode}")

# --- Schedule & Order Mud ---
if mode=="Schedule & Order Mud":
    st.sidebar.write("🐛 BRANCH: Schedule")
    st.header("📆 Schedule Generator & Mud Order")
    with st.form("sch"):
        lot  = st.text_input("Lot #")
        comm = st.selectbox("Community", list(COMMUNITIES))
        start = st.date_input("Start date")
        go = st.form_submit_button("Generate")
    if go:
        sched = generate_schedule(comm,start)
        st.table({ 'Task':[t for t,_,_ in sched],
                   'Sub': [s for _,s,_ in sched],
                   'Date':[d.strftime('%m/%d/%Y') for *_,d in sched] })
        # **AUTH TEST** ping once to confirm key
        try:
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"ping"}]
            )
            st.sidebar.success("🛠️ OpenAI auth test: OK")
        except Exception as e:
            st.sidebar.error(f"🛠️ OpenAI auth test failed: {e}")

# --- EPO & Tracker ---
elif mode=="EPO & Tracker":
    st.sidebar.write("🐛 BRANCH: EPO")
    # ... your existing EPO code ...

# --- QC Scheduling ---
elif mode=="QC Scheduling":
    st.sidebar.write("🐛 BRANCH: QC")
    # ... your existing QC code ...

# --- Homeowner Scheduling ---
elif mode=="Homeowner Scheduling":
    st.sidebar.write("🐛 BRANCH: Homeowner")
    # ... your existing Homeowner code ...

# --- Note Taking ---
elif mode=="Note Taking":
    st.sidebar.write("🐛 BRANCH: Note Taking")
    st.header("📝 Smart Note Taking")
    comm = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    raw  = st.text_area("Notes (Lot### - note)")
    if st.button("Classify & Parse"):
        st.session_state.notes = []
        for line in raw.splitlines():
            if not line.strip(): continue
            lot_code, note_txt = (line.split('-',1)+[""])[0:2]
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
