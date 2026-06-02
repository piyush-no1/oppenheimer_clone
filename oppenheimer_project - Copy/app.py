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

from pipeline.rag_engine import AdvancedOppenheimerRAG

if "torchcodec" in sys.modules: del sys.modules["torchcodec"]
if "torchcodec.decoders" in sys.modules: del sys.modules["torchcodec.decoders"]

from pipeline.voice_engine import voice_cloner, INIT_ERROR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
HISTORY_FILE_PATH = os.path.join(BASE_DIR, "chat_history.json")

if not GEMINI_KEY:
    st.error("Operational Failure: GEMINI_API_KEY missing from root .env file!")
    st.stop()

st.set_page_config(page_title="Oppenheimer Matrix", page_icon="⚛️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    h1, h2, h3 { font-family: 'Georgia', serif; color: #F3F4F6; }
    div[data-testid="stHorizontalBlock"] { align-items: center; }
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

def load_persistent_chat_history() -> list:
    if os.path.exists(HISTORY_FILE_PATH) and os.path.getsize(HISTORY_FILE_PATH) > 0:
        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return [{"role": "assistant", "text": "We knew the world would not be the same. A few people laughed, a few people cried, most people were silent. What is it you wish to deliberate upon?"}]

def save_persistent_chat_history(history_list: list):
    try:
        with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f: json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e: print(f"Failed to serialize session state: {e}")

if "rag_engine" not in st.session_state:
    with st.spinner("Streaming pre-compiled math indices to local RAM..."):
        st.session_state.rag_engine = AdvancedOppenheimerRAG()
        if not st.session_state.rag_engine.load_indices_from_disk():
            st.session_state.rag_engine.build_hierarchical_corpus()

if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = genai.Client(api_key=GEMINI_KEY)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_persistent_chat_history()

if "active_query" not in st.session_state:
    st.session_state.active_query = None

if "widget_counter" not in st.session_state:
    st.session_state.widget_counter = 0

with st.sidebar:
    st.title("⚛️ Digital Clone")
    st.markdown("---")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.chat_history = [{"role": "assistant", "text": "We knew the world would not be the same. A few people laughed, a few people cried, most people were silent. What is it you wish to deliberate upon?"}]
        save_persistent_chat_history(st.session_state.chat_history)
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
            <div style="background-color: #1E2530; border-left: 4px solid #00D2FF; padding: 14px; border-radius: 6px; margin-bottom: 14px; color: #E0E0E0;">
                <span style="color: #00D2FF; font-weight: bold; font-family: monospace;">[YOU]:</span> {msg['text']}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="background-color: #121620; border-left: 4px solid #FFB800; padding: 14px; border-radius: 6px; margin-bottom: 14px; color: #F3F4F6; font-family: 'Georgia', serif; line-height: 1.6;">
                <span style="color: #FFB800; font-weight: bold; font-family: monospace;">[OPPENHEIMER]:</span> {msg['text']}
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
        st.session_state.active_query = text_entry.strip()
        st.session_state.widget_counter += 1
        st.rerun()

user_input = st.session_state.active_query
if user_input:
    st.session_state.active_query = None 
    
    st.markdown(f"""
        <div style="background-color: #1E2530; border-left: 4px solid #00D2FF; padding: 14px; border-radius: 6px; margin-bottom: 14px; color: #E0E0E0;">
            <span style="color: #00D2FF; font-weight: bold; font-family: monospace;">[YOU]:</span> {user_input}
        </div>
    """, unsafe_allow_html=True)
    st.session_state.chat_history.append({"role": "user", "text": user_input})
    save_persistent_chat_history(st.session_state.chat_history)
    
    target_anim = "anim_general.json"
    if any(w in user_input.lower() for w in ["mass", "star", "collapse", "equation", "contraction"]):
        target_anim = "anim_physics.json"
    elif any(w in user_input.lower() for w in ["letter", "history", "trinity", "war", "gita", "bhagwat"]):
        target_anim = "anim_history.json"
        
    lottie_data = load_lottie_asset(target_anim)

    loader_placeholder = st.empty()
    with loader_placeholder.container():
        anim_inline_col, text_inline_col = st.columns([0.8, 11.2])
        with anim_inline_col:
            if lottie_data:
                try:
                    from streamlit_lottie import st_lottie
                    st_lottie(lottie_data, height=35, width=35, key=f"loader_{len(st.session_state.chat_history)}")
                except ImportError: pass
        with text_inline_col:
            st.markdown("<h3 style='margin:0; padding:0; color: #FFB800;'>Getting the info...</h3>", unsafe_allow_html=True)
        
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
        <div style="background-color: #121620; border-left: 4px solid #FFB800; padding: 14px; border-radius: 6px; margin-bottom: 14px; color: #F3F4F6; font-family: 'Georgia', serif; line-height: 1.6;">
            <span style="color: #FFB800; font-weight: bold; font-family: monospace;">[OPPENHEIMER]:</span> {ai_text}
        </div>
    """, unsafe_allow_html=True)
        
    st.session_state.chat_history.append({"role": "assistant", "text": ai_text})
    save_persistent_chat_history(st.session_state.chat_history)
    
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
                        base64_audio = base64.b64encode(audio_bytes).decode()
                        
                        hidden_audio_html = f"""
                            <audio autoplay="true" style="display:none;">
                                <source src="data:audio/wav;base64,{base64_audio}" type="audio/wav">
                            </audio>
                        """
                        st.markdown(hidden_audio_html, unsafe_allow_html=True)
                    else:
                        st.error("❌ Audio engine finished computation but failed to write wav asset file.")
                except Exception as audio_err:
                    st.error(f"❌ Core TTS Inference Engine Error: {audio_err}")
                    
