import streamlit as st
import pandas as pd
import datetime
import os
import json
import io
import wave
import requests
import zipfile
from vosk import Model, KaldiRecognizer

# --- Streamlit Config & Branding ---
st.set_page_config(
    page_title="Paint & Drywall Automator",
    page_icon="🏠",
    layout="wide"
)
st.markdown("""
    <style>
      #MainMenu {visibility: hidden;}
      footer     {visibility: hidden;}
      header     {visibility: hidden;}
      .stTable table {border-radius: 8px; overflow: hidden;}
    </style>
""", unsafe_allow_html=True)

# Sidebar logo
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)

# --- Ensure Vosk Model is Present (Download if Missing) ---
MODEL_DIR = "models/vosk-model-small-en-us-0.15"
MODEL_ZIP_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

if not os.path.exists(MODEL_DIR):
    os.makedirs("models", exist_ok=True)
    with st.spinner("Downloading Vosk model (approx. 50MB)…"):
        r = requests.get(MODEL_ZIP_URL)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall("models")

# Initialize Vosk ASR
try:
    vosk_model = Model(MODEL_DIR)
except Exception as e:
    st.error(f"Failed to load Vosk model: {e}")
    st.stop()

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

# --- Business Constants & Helpers (omitted for brevity) ---
# [Include generate_schedule, classify_note_locally, etc., unchanged]

# --- Sidebar Navigation ---
st.sidebar.markdown("---")
mode = st.sidebar.selectbox("Mode", [
    "Schedule & Order Mud",
    "EPO & Tracker",
    "QC Scheduling",
    "Homeowner Scheduling",
    "Note Taking"
])

# --- Note Taking with Vosk Dictation ---
if mode == "Note Taking":
    st.header("📝 Smart Note Taking")
    st.markdown("### 🎙️ Click to record and transcribe")
    audio_bytes = st.file_uploader("Upload a WAV file of your dictation", type=["wav"])
    if audio_bytes:
        transcript = transcribe_audio(audio_bytes.read())
        st.markdown(f"**Transcribed:** {transcript}")
        raw = st.text_area("Edit your note:", value=transcript, height=100)
    else:
        raw = st.text_area("Enter notes (format: Lot### - your note)", height=100)

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

# ... other modes unchanged ...

# --- Footer ---
st.markdown("---")
st.write("Demo only — no real emails or reminders.")

