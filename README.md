# NLP_Outpeer — Fairy Tale Generator with Text-to-Speech

This project generates short **fairy tales from a topic prompt** and converts them into **speech audio files (WAV)**.  
It was developed as part of an NLP bootcamp project and demonstrates **text generation + TTS integration**.

---

## ✨ Features
- Input a topic or theme → generate a **fairy tale story**.  
- Convert generated text into audio (`.wav`) with **text-to-speech**.  
- Notebook (`NLP.ipynb`) for experimentation + Python script (`NLP.py`) for direct execution.  
- Sample outputs included (`fairy_tale.wav`, `record.wav`).  

---

## 📂 Repository Contents
NLP_Outpeer/
├─ NLP.ipynb # Jupyter notebook demo
├─ NLP.py # Script version
├─ fairy_tale.wav # Example generated audio
├─ record.wav # Another sample audio file
└─ README.md # This file

yaml

---

## ⚙️ Installation
Create a virtual environment and install required packages.  
(This project was tested on **Python 3.9+**.)

git clone https://github.com/LnM044/NLP_Outpeer.git
cd NLP_Outpeer

# (optional) create env
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
If requirements.txt is missing, you can recreate it with:

pip install transformers torch soundfile gTTS
(adjust depending on the actual TTS backend you used)

🚀 Usage
Run with Jupyter Notebook
Open the notebook and run the cells step by step:
jupyter notebook NLP.ipynb

Run the Python Script
python NLP.py
