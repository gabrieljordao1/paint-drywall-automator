import streamlit as st
import pandas as pd
import datetime
import os
import json
import io
import wave
from vosk import Model, KaldiRecognizer
from streamlit_audiorecorder import audiorecorder

# --- Streamlit Config & Branding ---
st.set_page_config(
    page_title="Paint & Drywall Automator",
    page_icon="🏠",
    layout="wide"
)
st.markdown("""
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
      .stTable table {border-radius: 8px; overflow: hidden;}
    </style>
""", unsafe_allow_html=True)

# Sidebar logo
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)

# --- Vosk Model Initialization ---
# Assumes you have uncompressed the model under "models/vosk-model-small-en-us-0.15"
vosk_model = Model("models/vosk-model-small-en-us-0.15")

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe WAV bytes via Vosk offline ASR."""
    wf = wave.open(io.BytesIO(audio_bytes), "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(False)
    text_parts = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text_parts.append(res.get("text", ""))
    final_res = json.loads(rec.FinalResult())
    text_parts.append(final_res.get("text", ""))
    return " ".join(text_parts).strip()

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

# --- Business Data & Helpers ---
TASKS = ['Hang', 'Scrap', 'Tape', 'Bed', 'Skim', 'Sand']
COMMUNITIES = {
    'Galloway': {t: 'America Drywall' for t in TASKS},
    'Huntersville Town Center': {t: 'America Drywall' for t in TASKS},
    'Claremont': {
        'Hang':'Ricardo','Scrap':'Scrap Brothers',
        'Tape':'Juan Trejo','Bed':'Juan Trejo',
        'Skim':'Juan Trejo','Sand':'Juan Trejo'
    },
    'Context': {t: 'America Drywall' for t in TASKS},
    'Greenway Overlook': {t: 'America Drywall' for t in TASKS},
    'Camden': {t: 'America Drywall' for t in TASKS},
    'Olmstead': {
        'Hang':'Ricardo','Scrap':'Scrap Brothers',
        'Tape':'Juan Trejo','Bed':'Juan Trejo',
        'Skim':'Juan Trejo','Sand':'Juan Trejo'
    },
    'Maxwell': {t: 'America Drywall' for t in TASKS},
}
POINTUP_SUBS = {
    'Galloway':'Luis A. Lopez','Huntersville Town Center':'Luis A. Lopez',
    'Claremont':'Edwin','Context':'Edwin','Greenway Overlook':'Edwin',
    'Camden':'Luis A. Lopez','Olmstead':'Luis A. Lopez','Maxwell':'Luis A. Lopez'
}
PAINT_SUBS = [
    'GP Painting Services','Jorge Gomez',
    'Christian Painting','Carlos Gabriel','Juan Ulloa'
]

def classify_note_locally(lot, community, text):
    txt = text.lower()
    # Determine action
    if any(k in txt for k in ['clean-out','clean out','schedule clean']):
        action = 'Schedule Clean-Out Materials'
        sub = 'Scrap Truck'
        due_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%m/%d/%Y')
        email_to = ""
        email_draft = ""
    elif 'drywall' in txt and 'frame' in txt:
        action, sub, due_date, email_to, email_draft = 'Monitor Hang', '', '', '', ''
    elif any(kw in txt for kw in ['ready for final','final paint','final point up']):
        action = 'Notify Final Point-Up/Paint'
        sub = ''
        due_date = ''
        email_to = 'office@scheduling.example.com'
        email_draft = (
            f"Hi team,\n\nLot {lot} in {community} appears ready for final point-up or paint. "
            f"Please confirm scheduling.\n\nThanks."
        )
    elif 'epo' in txt:
        action, sub, due_date, email_to, email_draft = 'Request EPO', '', '', '', ''
    else:
        action, sub, due_date, email_to, email_draft = 'Note Logged', '', '', '', ''
    return {
        "Lot": lot,
        "Community": community,
        "Note": text,
        "Next Action": action,
        "Sub": sub,
        "Due Date": due_date,
        "Email To": email_to,
        "Email Draft": email_draft
    }

# --- Sidebar Navigation ---
st.sidebar.markdown("---")
mode = st.sidebar.selectbox("Mode", [
    "Schedule & Order Mud",
    "EPO & Tracker",
    "QC Scheduling",
    "Homeowner Scheduling",
    "Note Taking"
])

# --- Modes Implementation (omitted for brevity) ---

# --- Note Taking with Vosk Dictation ---
if mode == "Note Taking":
    st.header("Smart Note Taking")
    st.markdown("### 🎙️ Dictate your note")
    audio_bytes = audiorecorder("Click to record", "Recording…")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        transcript = transcribe_audio(audio_bytes)
        st.markdown(f"**Transcribed:** {transcript}")
        raw = st.text_area("Edit your note:", value=transcript, height=100)
    else:
        raw = st.text_area("Enter notes (Lot### - your note)", height=100)

    community = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    if st.button("Parse Notes"):
        st.session_state.notes = []
        for line in raw.splitlines():
            if not line.strip(): continue
            lot_code, note_txt = (line.split('-', 1) + [""])[0:2]
            item = classify_note_locally(lot_code.strip(), community, note_txt.strip())
            st.session_state.notes.append(item)
        save_data({'epo_log': st.session_state.epo_log, 'notes': st.session_state.notes})

    if st.session_state.notes:
        df = pd.DataFrame(st.session_state.notes).reset_index(drop=True)
        st.table(df)
    else:
        st.info("No notes yet.")

# --- Footer ---
st.markdown("---")
st.write("Demo only — no real emails or reminders.")

