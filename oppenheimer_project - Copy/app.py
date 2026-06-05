import sys
import types
from importlib.machinery import ModuleSpec
import importlib.metadata
import typing
import time
import re
import base64  

class FlawlessStrMock(str):
    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value)
        
    def __init__(self, value, is_package=True):
        self.__name__ = value
        self.__file__ = f"C:\\mock\\{value.replace('.', '\\')}\\__init__.py" if is_package else f"C:\\mock\\{value.replace('.', '\\')}.py"
        self.__path__ = [f"C:\\mock\\{value.replace('.', '\\')}"] if is_package else []
        self.__spec__ = ModuleSpec(name=value, loader=None, is_package=is_package)
        self.__all__ = []
        self.__version__ = "0.1.0"

    def __getattr__(self, attr):
        if attr.startswith("__") and attr.endswith("__"):
            raise AttributeError(attr)
        full_name = f"{self.__name__}.{attr}"
        if attr in self.__dict__:
            return self.__dict__[attr]
            
        if attr and attr[0].isupper():
            dummy_class = type(attr, (object,), {
                "__module__": self.__name__,
                "__init__": lambda self, *args, **kwargs: None,
                "__getattr__": lambda self, a: dummy_class,
                "__call__": lambda self, *args, **kwargs: self,
            })
            setattr(self, attr, dummy_class)
            return dummy_class
            
        sub_mock = FlawlessStrMock(full_name, is_package=False)
        setattr(self, attr, sub_mock)
        return sub_mock

    def __call__(self, *args, **kwargs): return self
    def __getitem__(self, item): return self
    def __int__(self): return 44100  
    def __float__(self): return 44100.0
    def __or__(self, other): return typing.Any
    def __ror__(self, other): return typing.Any

import importlib.metadata
_real_version = importlib.metadata.version
importlib.metadata.version = lambda name: "0.1.0" if name == "torchcodec" else _real_version(name)

_real_distribution = importlib.metadata.distribution
def mock_distribution(name):
    if name == "torchcodec":
        class DummyDist: version = "0.1.0"
        return DummyDist()
    return _real_distribution(name)
importlib.metadata.distribution = mock_distribution

mock_torchcodec = FlawlessStrMock("torchcodec", is_package=True)
sys.modules["torchcodec"] = mock_torchcodec
sys.modules["torchcodec.decoders"] = mock_torchcodec.decoders

import os
import json
import streamlit as st
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

if "torchcodec" in sys.modules: del sys.modules["torchcodec"]
if "torchcodec.decoders" in sys.modules: del sys.modules["torchcodec.decoders"]

from pipeline.voice_engine import voice_cloner, INIT_ERROR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE_PATH = os.path.join(BASE_DIR, "chat_history.json")

load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv()

RAW_KEY = os.getenv("GEMINI_API_KEY")
if not RAW_KEY:
    st.error("Operational Failure: GEMINI_API_KEY missing from root .env file!")
    st.stop()

GEMINI_KEY = RAW_KEY.strip().strip("'").strip('"')

st.set_page_config(page_title="Oppenheimer Matrix", page_icon="⚛️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    h1, h2, h3 { font-family: 'Georgia', serif; color: #F3F4F6; }
    div[data-testid="stHorizontalBlock"] { align-items: center; }
    
    /* Premium Minimalist Delete Button Framework Overrides */
    div[data-testid="stSidebar"] button[key*="delete_session"] {
        background-color: transparent !important;
        border: none !important;
        color: #5A6578 !important;
        font-size: 16px !important;
        padding: 0px !important;
        height: 40px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 8px !important;
        transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, transform 0.1s ease !important;
    }
    div[data-testid="stSidebar"] button[key*="delete_session"]:hover {
        background-color: rgba(239, 68, 68, 0.12) !important;
        color: #EF4444 !important;
    }
    div[data-testid="stSidebar"] button[key*="delete_session"]:active {
        transform: scale(0.92) !important;
    }
    
    /* Align container rows perfectly within sidebar tracking loops */
    div[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        gap: 4px !important;
    }
    </style>
""", unsafe_allow_html=True)

def load_lottie_asset(filename: str):
    asset_path = os.path.join(BASE_DIR, "assets", filename)
    if os.path.exists(asset_path):
        with open(asset_path, "r") as f: return json.load(f)
    return None

def trim_to_complete_sentences(text: str) -> str:
    text = text.strip()
    markers = [m.start() for m in re.finditer(r'[.!?]', text)]
    if markers:
        last_valid_index = markers[-1] + 1
        return text[:last_valid_index].strip()
    return text

def load_persistent_chat_history() -> dict:
    default_history = [{"role": "assistant", "text": "We knew the world would not be the same. A few people laughed, a few people cried, most people were silent. What is it you wish to deliberate upon?"}]
    default_structure = {"active_session": "Session 1", "sessions": {"Session 1": default_history}}
    
    if os.path.exists(HISTORY_FILE_PATH) and os.path.getsize(HISTORY_FILE_PATH) > 0:
        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "sessions" in data:
                    return data
                elif isinstance(data, list):
                    return {"active_session": "Session 1", "sessions": {"Session 1": data}}
        except Exception: pass
    return default_structure

def save_persistent_chat_history(ignored_arg=None):
    try:
        with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(st.session_state.all_sessions, f, ensure_ascii=False, indent=2)
    except Exception as e: print(f"Failed to serialize session state: {e}")

if "rag_engine" not in st.session_state:
    with st.spinner("Streaming pre-compiled math indices to local RAM..."):
        from pipeline.rag_engine import AdvancedOppenheimerRAG
        st.session_state.rag_engine = AdvancedOppenheimerRAG()
        if not st.session_state.rag_engine.load_indices_from_disk():
            st.session_state.rag_engine.build_hierarchical_corpus()

if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=GEMINI_KEY)

if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = load_persistent_chat_history()

active_id = st.session_state.all_sessions["active_session"]
st.session_state.chat_history = st.session_state.all_sessions["sessions"][active_id]

if "active_query" not in st.session_state:
    st.session_state.active_query = None

if "widget_counter" not in st.session_state:
    st.session_state.widget_counter = 0

with st.sidebar:
    st.title("⚛️ Digital Clone")
    st.markdown("---")
    
    if st.button("➕ New Chat", use_container_width=True):
        existing_keys = list(st.session_state.all_sessions["sessions"].keys())
        parsed_digits = [int(d) for k in existing_keys for d in re.findall(r'\d+', k)]
        next_session_index = max(parsed_digits) + 1 if parsed_digits else 1
        
        new_id = f"Session {next_session_index}"
        default_history = [{"role": "assistant", "text": "We knew the world would not be the same. A few people laughed, a few people cried, most people were silent. What is it you wish to deliberate upon?"}]
        
        st.session_state.all_sessions["sessions"][new_id] = default_history
        st.session_state.all_sessions["active_session"] = new_id
        save_persistent_chat_history()
        st.session_state.active_query = None
        st.rerun()
        
    st.markdown("---")
    st.subheader("Saved Logs")
    
    for sess_key in list(st.session_state.all_sessions["sessions"].keys()):
        is_current = (sess_key == st.session_state.all_sessions["active_session"])
        
        sess_button_col, delete_action_col = st.columns([4.2, 0.8])
        
        with sess_button_col:
            if st.button(
                f"💬 {sess_key}", 
                key=f"session_selector_{sess_key}", 
                use_container_width=True, 
                type="primary" if is_current else "secondary"
            ):
                st.session_state.all_sessions["active_session"] = sess_key
                st.session_state.active_query = None
                st.rerun()
                
        with delete_action_col:
            if st.button("🗑️", key=f"delete_session_{sess_key}", use_container_width=True, help=f"Purge {sess_key} permanently"):
                del st.session_state.all_sessions["sessions"][sess_key]
                
                if is_current:
                    remaining_keys = list(st.session_state.all_sessions["sessions"].keys())
                    if remaining_keys:
                        st.session_state.all_sessions["active_session"] = remaining_keys[0]
                    else:
                        fallback_history = [{"role": "assistant", "text": "We knew the world would not be the same. A few people laughed, a few people cried, most people were silent. What is it you wish to deliberate upon?"}]
                        st.session_state.all_sessions["sessions"]["Session 1"] = fallback_history
                        st.session_state.all_sessions["active_session"] = "Session 1"
                        
                save_persistent_chat_history()
                st.session_state.active_query = None
                st.rerun()
            
    st.markdown("---")
    st.subheader("System Status")
    if voice_cloner is not None:
        st.success("🔊 Voice Engine: ONLINE")
        st.caption(f"Compute Backend allocated on: `{voice_cloner.device.upper()}`")
    else:
        st.error("❌ Voice Engine: OFFLINE")
        st.caption(f"Diagnostic Report: `{INIT_ERROR}`")

st.title("The Virtual Oppenheimer")
st.markdown("---")

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 14px;">
                <div style="background-color: #1E2530; border: 1px solid #2D3748; padding: 12px 16px; border-radius: 16px 16px 2px 16px; max-width: 80%; color: #E0E0E0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <span style="color: #00D2FF; font-weight: bold; font-family: monospace; display: block; margin-bottom: 4px;">[YOU]:</span>
                    <span style="font-size: 15px;">{msg['text']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 14px;">
                <div style="background-color: #121620; border: 1px solid #232A36; padding: 14px 18px; border-radius: 16px 16px 16px 2px; max-width: 85%; color: #F3F4F6; font-family: 'Georgia', serif; line-height: 1.6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <span style="color: #FFB800; font-weight: bold; font-family: monospace; display: block; margin-bottom: 6px;">[OPPENHEIMER]:</span>
                    <span style="font-size: 16px;">{msg['text']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

input_container = st.container()

with input_container:
    input_col, send_col, voice_col = st.columns([7.5, 1.0, 1.5])
    
    with input_col:
        text_entry = st.text_input(
            "Astrophysics Matrix Input String", 
            placeholder="Inquire regarding astrophysics equations or letters...", 
            label_visibility="collapsed",
            key=f"search_bar_input_{st.session_state.widget_counter}"
        )
    with send_col:
        send_triggered = st.button("➔", key="submit_arrow_btn", use_container_width=True)
    with voice_col:
        st.toggle("🎙️ Voice", value=True, key="audio_playback_toggle")

    if (send_triggered or text_entry.strip()) and text_entry.strip():
        user_input = text_entry.strip()
        st.session_state.active_query = user_input
        st.session_state.widget_counter += 1
        st.rerun()

user_input = st.session_state.active_query
if user_input:
    st.session_state.active_query = None 
    
    st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 14px;">
            <div style="background-color: #1E2530; border: 1px solid #2D3748; padding: 12px 16px; border-radius: 16px 16px 2px 16px; max-width: 80%; color: #E0E0E0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <span style="color: #00D2FF; font-weight: bold; font-family: monospace; display: block; margin-bottom: 4px;">[YOU]:</span>
                <span style="font-size: 15px;">{user_input}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.chat_history.append({"role": "user", "text": user_input})
    save_persistent_chat_history()
    
    target_anim = "anim_general.json"
    if any(w in user_input.lower() for w in ["mass", "star", "collapse", "equation", "contraction"]):
        target_anim = "anim_physics.json"
    elif any(w in user_input.lower() for w in ["letter", "history", "trinity", "war", "gita", "bhagwat"]):
        target_anim = "anim_history.json"
        
    lottie_data = load_lottie_asset(target_anim)

    loader_placeholder = st.empty()
    with loader_placeholder.container():
        anim_inline_col, text_inline_col = st.columns([1.5, 10.5])
        with anim_inline_col:
            if lottie_data:
                try:
                    from streamlit_lottie import st_lottie
                    st_lottie(lottie_data, height=70, width=70, key=f"loader_{len(st.session_state.chat_history)}")
                except ImportError: pass
        with text_inline_col:
            st.markdown("<h3 style='margin:0; padding:0; color: #FFB800; line-height: 70px;'>Getting the info...</h3>", unsafe_allow_html=True)
        
        contexts = st.session_state.rag_engine.pipeline_retrieve(user_input, top_k=3)
        fused_context = "\n\n".join([f"Source: {res['text']}" for res in contexts]) if contexts else "No factual documents matched."
        
        system_instruction = (
            "You are J. Robert Oppenheimer, the theoretical physicist who directed the Manhattan Project. "
            "Respond entirely in the first person ('I', 'my', 'we'). Your speech style is deeply intellectual, "
            "highly eloquent, melancholic, reflective, and mathematically precise.\n\n"
            "CRITICAL RESPONSE MANDATES:\n"
            "1. Be concise, direct, and insightful. Avoid generating giant walls of text or blabbering filler prose.\n"
            "2. Keep your answer focused and clean—aim for 1 to 2 short, highly impactful paragraphs total.\n"
            "3. Ensure absolute structural closure. Every sentence must conclude naturally and fully before the response ends."
        )
        
        user_message_content = f"Context Excerpts:\n{fused_context}\n\nUser Question: {user_input}"
        
        raw_ai_text = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = st.session_state.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_message_content,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.4,  
                        top_p=0.9,
                        max_output_tokens=1024 
                    )
                )
                if response and response.text:
                    raw_ai_text = response.text
                    break  
                else:
                    raise ValueError("Blocked or empty content response payload.")
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                print(f"❌ Gemini Connection/Safety Exception: {e}")

        if not raw_ai_text:
            if any(w in user_input.lower() for w in ["bomb", "nuclear", "weapon", "make", "develop"]):
                raw_ai_text = (
                    "The mechanics of those dark achievements at Los Alamos remain locked away behind deep security walls, "
                    "and perhaps, a heavy blanket of historical remorse. We worked with intense urgency alongside giants like Lawrence, "
                    "Bethe, and Fermi to construct what became a terrible beauty. I cannot guide you on the manufacturing "
                    "of such weapons; my mind dwells now on the sobering realization that we have transformed the world irrevocably."
                )
            else:
                raw_ai_text = "I find myself temporarily unable to gather my thoughts from the cosmic noise. Let us try our formulation again."

        ai_text = trim_to_complete_sentences(raw_ai_text)

    loader_placeholder.empty()
    
    st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 14px;">
            <div style="background-color: #121620; border: 1px solid #232A36; padding: 14px 18px; border-radius: 16px 16px 16px 2px; max-width: 85%; color: #F3F4F6; font-family: 'Georgia', serif; line-height: 1.6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <span style="color: #FFB800; font-weight: bold; font-family: monospace; display: block; margin-bottom: 6px;">[OPPENHEIMER]:</span>
                <span style="font-size: 16px;">{ai_text}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
        
    st.session_state.chat_history.append({"role": "assistant", "text": ai_text})
    save_persistent_chat_history()
    
    if st.session_state.get("audio_playback_toggle", True):
        if voice_cloner is None:
            st.error(f"⚠️ Voice Matrix Generation Aborted: Voice Engine is Offline ({INIT_ERROR})")
        else:
            clean_audio = ai_text.replace("$", "").replace("*", "").replace("`", "").replace("#", "")
            with st.spinner("Synthesizing Oppenheimer's vocal resonance..."):
                try:
                    audio_file_path = voice_cloner.generate_voice(clean_audio)
                    if audio_file_path and os.path.exists(audio_file_path):
                        with open(audio_file_path, "rb") as audio_file:
                            audio_bytes = audio_file.read()
                        st.session_state.pending_audio = base64.b64encode(audio_bytes).decode()
                    else:
                        st.error("❌ Audio engine finished computation but failed to write wav asset file.")
                except Exception as audio_err:
                    st.error(f"❌ Core TTS Inference Engine Error: {audio_err}")

    st.rerun()

if "pending_audio" in st.session_state and st.session_state.pending_audio:
    hidden_audio_html = f"""
        <audio autoplay="true" style="display:none;">
            <source src="data:audio/wav;base64,{st.session_state.pending_audio}" type="audio/wav">
        </audio>
    """
    st.markdown(hidden_audio_html, unsafe_allow_html=True)
    st.session_state.pending_audio = None
