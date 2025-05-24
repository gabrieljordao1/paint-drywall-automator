import streamlit as st
import datetime
import json
import re
import openai

# Load your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Business logic ---
TASKS = ['Hang', 'Scrap', 'Tape', 'Bed', 'Skim', 'Sand']
COMMUNITIES = {
    'Galloway': {t: 'America Drywall' for t in TASKS},
    'Huntersville Town Center': {t: 'America Drywall' for t in TASKS},
    'Claremont': {
        'Hang': 'Ricardo', 'Scrap': 'Scrap Brothers', 'Tape': 'Juan Trejo',
        'Bed': 'Juan Trejo', 'Skim': 'Juan Trejo', 'Sand': 'Juan Trejo'
    },
    'Context': {t: 'America Drywall' for t in TASKS},
    'Greenway Overlook': {t: 'America Drywall' for t in TASKS},
    'Camden': {t: 'America Drywall' for t in TASKS},
    'Olmstead': {
        'Hang': 'Ricardo', 'Scrap': 'Scrap Brothers', 'Tape': 'Juan Trejo',
        'Bed': 'Juan Trejo', 'Skim': 'Juan Trejo', 'Sand': 'Juan Trejo'
    },
    'Maxwell': {t: 'America Drywall' for t in TASKS},
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

# Define OpenAI function schema for note parsing
parse_note_fn = {
    "name": "parse_note",
    "description": "Extract lot, community, issue, action, and followup date from a note.",
    "parameters": {
        "type": "object",
        "properties": {
            "lot": {"type": "string", "description": "Lot number"},
            "community": {"type": "string", "description": "Community context"},
            "issue": {"type": "string", "enum": ["EPO","framing","clean_out","final_paint","other"]},
            "action": {"type": "string", "enum": ["request_epo","monitor_hang","schedule_clean_up","notify_final","log_note"]},
            "details": {"type": "string", "description": "Additional details"},
            "followup": {"type": "string", "format": "date-time", "description": "Suggested follow-up datetime"}
        },
        "required": ["lot","community","issue","action"]
    }
}

st.set_page_config(page_title="Paint & Drywall Automator Demo")
st.title("🏠 Paint & Drywall Automator Demo")

mode = st.sidebar.selectbox("Choose demo mode", [
    "Schedule & Order Mud",
    "EPO & Tracker",
    "QC Scheduling",
    "Homeowner Scheduling",
    "Note Taking"
])

# --- Existing tabs omitted for brevity ---
# (Schedule & Order Mud, EPO & Tracker, QC Scheduling, Homeowner Scheduling remain unchanged)

# --- Note Taking ---
elif mode == "Note Taking":
    st.header("📝 Note Taking")
    comm = st.selectbox("Community Context", list(COMMUNITIES.keys()))

    # Audio upload for Whisper
    audio = st.file_uploader("Upload a voice note (wav/m4a)", type=["wav","m4a"])
    if audio:
        with st.spinner("Transcribing audio..."):
            transcript = openai.Audio.transcribe("whisper-1", audio)
        notes_input = transcript.get("text", "")
        st.write("🗣️ Transcribed:", notes_input)
    else:
        notes_input = st.text_area("Or enter notes manually (one per line, Lot### - note)")

    if st.button("Parse Notes"):
        st.session_state.notes = []
        for line in notes_input.splitlines():
            if not line.strip():
                continue
            # Call GPT function
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-0613",
                messages=[
                    {"role": "system", "content": f"Community context: {comm}"},
                    {"role": "user", "content": line}
                ],
                functions=[parse_note_fn],
                function_call={"name": "parse_note"}
            )
            args = json.loads(response.choices[0].message.function_call.arguments)
            # Normalize and append
            st.session_state.notes.append({
                "Community": comm,
                "Lot": args.get("lot",""),
                "Issue": args.get("issue",""),
                "Action": args.get("action",""),
                "Details": args.get("details",""),
                "Follow-Up": args.get("followup","")
            })

    if st.session_state.notes:
        st.subheader("Parsed Notes")
        st.table(st.session_state.notes)

# Sidebar
st.sidebar.markdown("---")
st.sidebar.write("This is a **demo only**—no actual emails go out.")
