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

# --- OpenAI Client Setup with Secrets Fallback ---
# Try environment variable first, then Streamlit secrets.toml
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    st.error("OpenAI API key not found. Please set OPENAI_API_KEY as an environment variable or in Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

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

# The rest of your app follows unchanged...
# (Schedule tab, EPO tab, QC tab, Homeowner tab, Note Taking tab)

