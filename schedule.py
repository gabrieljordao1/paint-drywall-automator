import streamlit as st
import pandas as pd
import datetime
import io
import os
import json
import openai
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
      footer     {visibility: hidden;}
      header     {visibility: hidden;}
      .stTable table {border-radius: 8px; overflow: hidden;}
    </style>
""", unsafe_allow_html=True)

# Sidebar logo
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)

# --- OpenAI Whisper Setup ---
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
openai.api_key = api_key

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
TASKS = ['Hang','Scrap','Tape','Bed','Skim','Sand']
COMMUNITIES = {
    'Galloway': {t:'America Drywall' for t in TASKS},
    'Huntersville Town Center': {t:'America Drywall' for t in TASKS},
    'Claremont': {'Hang':'Ricardo','Scrap':'Scrap Brothers','Tape':'Juan Trejo',
                  'Bed':'Juan Trejo','Skim':'Juan Trejo','Sand':'Juan Trejo'},
    'Context': {t:'America Drywall' for t in TASKS},
    'Greenway Overlook': {t:'America Drywall' for t in TASKS},
    'Camden': {t:'America Drywall' for t in TASKS},
    'Olmstead': {'Hang':'Ricardo','Scrap':'Scrap Brothers','Tape':'Juan Trejo',
                 'Bed':'Juan Trejo','Skim':'Juan Trejo','Sand':'Juan Trejo'},
    'Maxwell': {t:'America Drywall' for t in TASKS},
}
DUR = {'Hang':1,'Scrap':1,'Sand':1,'Tape':2,'Bed':2,'Skim':2}
POINTUP_SUBS = {
    'Galloway':'Luis A. Lopez','Huntersville Town Center':'Luis A. Lopez',
    'Claremont':'Edwin','Context':'Edwin','Greenway Overlook':'Edwin',
    'Camden':'Luis A. Lopez','Olmstead':'Luis A. Lopez','Maxwell':'Luis A. Lopez'
}
PAINT_SUBS = ['GP Painting Services','Jorge Gomez','Christian Painting',
              'Carlos Gabriel','Juan Ulloa']

def generate_schedule(community, start_date):
    schedule, cur = [], start_date
    for task in TASKS:
        days, added = DUR[task], 0
        skip_sun, skip_wk = (task!='Scrap'), (task=='Scrap')
        while added < days:
            cur += datetime.timedelta(days=1)
            if skip_wk and cur.weekday() >= 5: continue
            if skip_sun and cur.weekday() == 6: continue
            added += 1
        schedule.append((task, COMMUNITIES[community].get(task,'—'), cur))
    return schedule

def classify_note_locally(lot, community, text):
    txt = text.lower()
    action, sub, due_date, email_to, email_draft = 'Note Logged','', '','', ''
    if 'clean-out' in txt or 'schedule clean' in txt:
        action, sub = 'Schedule Clean-Out Materials','Scrap Truck'
        due_date = (datetime.datetime.now()+datetime.timedelta(days=1)).strftime('%m/%d/%Y')
    elif 'drywall' in txt and 'frame' in txt:
        action = 'Monitor Hang'
    elif any(kw in txt for kw in ['ready for final','final paint','final point up']):
        action = 'Notify Final Point-Up/Paint'
        email_to = 'office@scheduling.example.com'
        email_draft = (
            f"Hi team,\n\n"
            f"Lot {lot} in {community} appears ready or nearing final point-up/paint. "
            f"Please confirm if it's on the schedule.\n\nThanks."
        )
    elif 'epo' in txt:
        action = 'Request EPO'
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
mode = st.sidebar.selectbox("Mode",[
    "Schedule & Order Mud","EPO & Tracker","QC Scheduling",
    "Homeowner Scheduling","Note Taking"
])

# --- Modes ---
if mode == "Schedule & Order Mud":
    st.header("Schedule Generator & Mud Order")
    with st.form("sch"):
        lot = st.text_input("Lot number")
        community = st.selectbox("Community", list(COMMUNITIES))
        start = st.date_input("Start date")
        if st.form_submit_button("Generate"):
            sched = generate_schedule(community, start)
            st.table({
                'Task':[t for t,_,_ in sched],
                'Sub':[s for _,s,_ in sched],
                'Date':[d.strftime('%m/%d/%Y') for *_,d in sched]
            })
            if st.button("Order Mud for Scrap Date"):
                st.success(f"Mud order queued for {sched[1][2].strftime('%m/%d/%Y')}")

elif mode == "EPO & Tracker":
    st.header("EPO Automation & Tracker")
    with st.form("epo", clear_on_submit=True):
        lot = st.text_input("Lot number")
        community = st.selectbox("Community", list(COMMUNITIES))
        email_to = st.text_input("Builder Email")
        amount = st.text_input("Amount")
        photos = st.file_uploader("Attach photos", accept_multiple_files=True)
        if st.form_submit_button("Send EPO"):
            now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
            e = {'lot':lot,'comm':community,'to':email_to,
                 'amt':amount,'sent':now,'replied':False,'followup':False}
            st.session_state.epo_log.append(e)
            save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
            st.success(f"EPO for Lot {lot} recorded at {now}")
    st.subheader("EPO Tracker")
    if st.session_state.epo_log:
        for i,e in enumerate(st.session_state.epo_log):
            c = st.columns(6)
            c[0].write(e['lot']); c[1].write(e['comm']); c[2].write(e['sent'])
            status = 'Replied' if e['replied'] else ('Follow-Up Sent' if e['followup'] else 'Pending')
            c[3].write(status)
            if not e['replied'] and c[4].button("Mark Replied",key=f"r{i}"):
                e['replied']=True; save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
            if not e['followup'] and not e['replied'] and c[5].button("Send Follow-Up",key=f"f{i}"):
                e['followup']=True; save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})
                st.info(f"Follow-up queued for Lot {e['lot']}")

elif mode == "QC Scheduling":
    st.header("QC Scheduling")
    lot = st.text_input("Lot number",key='qc_lot')
    community = st.selectbox("Community", list(COMMUNITIES), key='qc_comm')
    pu = st.date_input("QC Point-Up date",key='qc_pu')
    pd = st.date_input("QC Paint date",key='qc_paint')
    ps = st.selectbox("QC Paint subcontractor", PAINT_SUBS, key='qc_sub')
    sd = st.date_input("QC Stain date",key='qc_stain')
    if st.button("Schedule QC Tasks"):
        tasks = [
            {'Task':'QC Point-Up','Sub':POINTUP_SUBS[community],'Date':pu.strftime('%m/%d/%Y')},
            {'Task':'QC Paint','Sub':ps,'Date':pd.strftime('%m/%d/%Y')},
            {'Task':'QC Stain','Sub':'Dorby','Date':sd.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)

elif mode == "Homeowner Scheduling":
    st.header("Homeowner Scheduling")
    lot = st.text_input("Lot number",key='ho_lot')
    community = st.selectbox("Community", list(COMMUNITIES),key='ho_comm')
    pu = st.date_input("HO Point-Up date",key='ho_pu')
    pd = st.date_input("HO Paint date",key='ho_paint')
    ps = st.selectbox("HO Paint subcontractor", PAINT_SUBS,key='ho_sub')
    if st.button("Schedule HO Tasks"):
        tasks = [
            {'Task':'HO Point-Up','Sub':POINTUP_SUBS[community],'Date':pu.strftime('%m/%d/%Y')},
            {'Task':'HO Paint','Sub':ps,'Date':pd.strftime('%m/%d/%Y')}
        ]
        st.table(tasks)

elif mode == "Note Taking":
    st.header("Smart Note Taking")

    # Dictation feature
    st.markdown("### 🎤 Dictate a note")
    audio_bytes = audiorecorder("Click to record", "Recording…")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        # transcribe via Whisper
        transcript = openai.Audio.transcriptions.create(
            model="whisper-1",
            file=io.BytesIO(audio_bytes)
        )
        note_text = transcript["text"]
        st.markdown(f"**Transcribed:** {note_text}")
        raw = st.text_area("Or edit your note:", value=note_text, height=100)
    else:
        raw = st.text_area("Enter or edit your note:", height=100)

    community = st.selectbox("Community", list(COMMUNITIES), key='note_comm')
    if st.button("Parse Notes"):
        st.session_state.notes = []
        lines = raw.splitlines() if raw else []
        for line in lines:
            if not line.strip(): continue
            lot_code,note_txt = (line.split('-',1)+[""])[0:2]
            item = classify_note_locally(lot_code.strip(), community, note_txt.strip())
            st.session_state.notes.append(item)
        save_data({'epo_log':st.session_state.epo_log,'notes':st.session_state.notes})

    if st.session_state.notes:
        df = pd.DataFrame(st.session_state.notes).reset_index(drop=True)
        st.table(df)
    else:
        st.info("No notes yet.")

# Footer
st.markdown("---")
st.write("Demo only—no real emails or reminders.")
