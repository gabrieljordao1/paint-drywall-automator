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

# Instantiate client
client = OpenAI(api_key=api_key)

# --- Persistence ---
DATA_FILE = "demo_data.json"
def load_data():
    try:
        return json.load(open(DATA_FILE))
    except:
        return {"epo_log": [], "notes": []}

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, default=str, indent=2)

st.session_state.setdefault('epo_log', load_data().get('epo_log', []))
st.session_state.setdefault('notes',    load_data().get('notes',    []))

# --- Business Data & Helpers ---
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
PAINT_SUBS = ['GP Painting Services','Jorge Gomez','Christian Painting','Carlos Gabriel','Juan Ulloa']

def generate_schedule(comm, start):
    sched, cur = [], start
    for t in TASKS:
        days, added = DUR[t], 0
        skip_sun, skip_wk = (t!='Scrap'), (t=='Scrap')
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday()>=5: continue
            if skip_sun and cur.weekday()==6: continue
            added += 1
        sched.append((t, COMMUNITIES[comm][t], cur))
    return sched

def classify_note_with_llm(lot, community, text):
    functions=[{
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
    messages=[
      {"role":"system","content":"Turn construction walk-through notes into action items."},
      {"role":"user","content":f"Lot {lot} in {community}: {text}"}
    ]
    # ← use a model everyone has access to:
    res = client.chat.completions.create(
      model="gpt-3.5-turbo-0613",
      messages=messages,
      functions=functions,
      function_call={"name":"classifyNote"}
    )
    call = res.choices[0].message.function_call
    args = json.loads(call.arguments)
    return {
      "Lot": lot, "Community": community, "Note": text,
      "Category": args["category"],
      "Due Date": args.get("dueDate",""),
      "Priority": args.get("priority",""),
      "Email Draft": args["emailDraft"]
    }

# --- Sidebar & Debug ---
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
        lot   = st.text_input("Lot number")
        comm  = st.selectbox("Community", list(COMMUNITIES))
        start = st.date_input("Start date")
        go    = st.form_submit_button("Generate")
    if go:
        sched = generate_schedule(comm,start)
        st.table({
          'Task':[t for t,_,_ in sched],
          'Sub':[s for _,s,_ in sched],
          'Date':[d.strftime('%m/%d/%Y') for *_,d in sched]
        })

# --- EPO & Tracker ---
elif mode=="EPO & Tracker":
    st.sidebar.write("🐛 BRANCH: EPO")
    …  # your existing EPO code unchanged

# --- QC Scheduling ---
elif mode=="QC Scheduling":
    st.sidebar.write("🐛 BRANCH: QC")
    …  # unchanged

# --- Homeowner Scheduling ---
elif mode=="Homeowner Scheduling":
    st.sidebar.write("🐛 BRANCH: Homeowner")
    …  # unchanged

# --- Note Taking with Auth Test ---
elif mode=="Note Taking":
    st.sidebar.write("🐛 BRANCH: Note Taking")
    st.header("📝 Smart Note Taking")
    comm = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    raw  = st.text_area("Enter notes (Lot### - note)")
    if st.button("Classify & Parse"):
        st.session_state.notes = []
        # **IMPLEMENTS AUTH TEST HERE**
        try:
            client.chat.completions.create(
              model="gpt-3.5-turbo-0613",
              messages=[{"role":"system","content":"ping"}]
            )
            st.sidebar.success("🛠️ OpenAI auth test: OK")
        except Exception as e:
            st.sidebar.error(f"🛠️ OpenAI auth test failed: {e}")
        # now do your real classification
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
