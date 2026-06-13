# ⚛️ The "Virtual Oppenheimer" Digital Clone System

A digital clone framework engineered to simulate the cognitive persona, historical knowledge base, and unique acoustic vocal signature of theoretical physicist J. Robert Oppenheimer. 

By merging an optimized, localized **Hierarchical Parent-Child Retrieval-Augmented Generation (RAG)** pipeline with a **Non-Autoregressive Flow-Matching Text-to-Speech (TTS)** cloning matrix, the platform delivers historically accurate, low-latency, context-aware interactions entirely within a localized consumer-hardware computing environment.

---

## 🛠️ Performance Architecture & Hardening

* **Ingestion-Time Tensor Caching ($O(\log N)$):** Completely separates knowledge ingestion from runtime query windows. Token-level multi-vectors and dense text coordinates are pre-calculated and serialized down to disk storage (`child_token_embeddings.pkl`). Upon boot, these stream directly into RAM via high-speed, single-pass I/O maps, reducing retrieval time to single-digit milliseconds.
* **Vectorized Cosine Similarity Matrix:** Replaces traditional sequential scalar loops with optimized linear algebra dot-products via NumPy (`np.dot`). The entire child document database is scored simultaneously within a single hardware clock cycle.
* **Acoustic Isolation Matrix:** Slices raw text generations into individual sentence blocks using look-behind regex splitters. Processing each sentence independently on the GPU prevents cross-attention alignment drift—completely eliminating word duplication and vocal hallucinations over extended context frames.
* **Lifecycle Inversion Controls:** Heavy AI logic runs at the absolute top of the file layout structure. Text and audio arrays are pre-computed and committed to a state buffer (`st.session_state.pending_audio`) before any rendering occurs. The browser then loops through historical threads first, locking the input fields permanently to the absolute bottom of the viewport.

---

## 📁 Repository Directory Blueprint

```text
OPPENHEIMER_PROJECT/
│
├── .streamlit/
│   └── config.toml                # Frontend workspace layout configuration sheets
│
├── assets/
│   ├── anim_general.json          # Responsive Lottie asset: Default cognitive loop
│   ├── anim_history.json          # Responsive Lottie asset: Historical query matrix
│   ├── anim_physics.json          # Responsive Lottie asset: Advanced astrophysics matrix
│   ├── oppenheimer_output.wav     # Runtime cache: Local target sound waveform
│   └── oppenheimer_ref.wav        # Studio reference file: 1965 interview vocal signature
│
├── data_source/
│   └── oppenheimer_corpus.txt     # Specialized database text: Correspondence and research notes
│
├── pipeline/
│   ├── __init__.py                # Package path initialization file
│   ├── rag_engine.py              # Retrieval script: Multi-vector hybrid matching environment
│   └── voice_engine.py            # Neural speech model: F5-TTS inference and sound array joining
│
├── scripts/
│   ├── __init__.py                # Internal script route initialization file
│   ├── fetch_animations.py        # Automation utility: Downloads structural UI assets
│   ├── fetch_dataset.py           # Automation utility: Pulls source context text blocks
│   ├── fetch_voice.py             # Automation utility: Collects reference voice recordings
│   └── trim_and_boost.py          # Audio mastering: Normalization and waveform trimming
│
├── vector_store/
│   ├── bm25_model.pkl             # Serialized keyword tracking frequency model
│   ├── child_chunks.json          # Text database: Isolated child data blocks (400 char)
│   ├── child_embeddings.npy       # Pre-computed coordinate arrays: Dense representation matrix
│   ├── child_token_embeddings.pkl # Pre-computed tensor mapping: Late-interaction embeddings
│   └── parent_chunks.json         # Text database: Extended parent context blocks (1800 char)
│
├── .env                           # Protected registry configuration file: Houses API keys
├── app.py                         # Application Master Core: Lifecycle manager and layout interface
└── chat_history.json              # Persistent workspace storage: Conversation log database

