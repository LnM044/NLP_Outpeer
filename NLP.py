import streamlit as st
import openai
import os
import tempfile  # <--- for creating temp files
from TTS.api import TTS
from pydub import AudioSegment
from io import BytesIO

# ----------------------------
# 1) OpenAI setup
# ----------------------------

# Fetch the API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize session state for feedback
if "feedback" not in st.session_state:
    st.session_state["feedback"] = None

# Supported languages
LANGUAGE_MAP = {
    "English": "en",
    "Russian": "ru",
    "French": "fr",
    "Spanish": "es",
    "German": "de"
}

# ----------------------------
# 2) Background music selection
# ----------------------------
THEME_MUSIC_MAP = {
    "space": "background_sound/space.wav",
    "fantastic": "background_sound/fantasy.wav",
    "medieval": "background_sound/medieval.wav",
    "horror": "background_sound/horror.wav",
    "sea": "background_sound/sea.wav",
    "sci-fi": "background_sound/sci-fi.wav",
    "forest": "background_sound/day_forest.wav"
}

DEFAULT_BG_MUSIC = "background_sound/fairy_tail_slow.wav"

def pick_background_music(theme):
    theme_lower = theme.lower()
    for key, music_file in THEME_MUSIC_MAP.items():
        if key in theme_lower:
            return music_file
    return DEFAULT_BG_MUSIC

# ----------------------------
# 3) Fairy Tale Generation
# ----------------------------
def generate_fairy_tale(scenario, main_character, themes, language_code, progress_bar):
    """
    Generate a fairy tale using OpenAI ChatCompletion.
    Incorporate user feedback (like/dislike) into the system message.
    """
    # Incorporate feedback into system message:
    if st.session_state["feedback"] == "like":
        feedback_note = (
            "The user liked your previous story. Maintain or enhance that appealing style/tone.\n"
        )
    elif st.session_state["feedback"] == "dislike":
        feedback_note = (
            "The user disliked your previous story. Try a different approach or style.\n"
        )
    else:
        feedback_note = ""

    system_message = (
        "You are a creative AI specialized in crafting original fairy tales. "
        "Write a complete story with a clear beginning, middle, and end. "
        "It should be relatively small, around 1000 words. "
        "Use rich detail, do not end abruptly, and conclude with a final resolution. "
        f"Write the story in {language_code} language.\n"
        + feedback_note
    )

    user_message = (
        f"Initial Scenario: {scenario}\n"
        f"Main Character: {main_character}\n"
        f"Themes: {themes}\n\n"
        "Please write the fairy tale using these elements, up to around 1000 words, ending conclusively."
    )

    try:
        with st.spinner("Generating fairy tale..."):
            progress_bar.progress(33)
            response = openai.chat.completions.create(
                model="gpt-4",  # Or "gpt-3.5-turbo"/"gpt-4" depending on your plan
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature = 0.7,
                max_tokens = 2000,   # Might adjust for a slightly longer story
                top_p = 1.0,
                frequency_penalty = 0.5,
                presence_penalty = 0.5
            )
            progress_bar.progress(66)
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred while generating the fairy tale: {e}")
        return None

# ----------------------------
# 4) TTS Synthesis (Coqui)
# ----------------------------
def text_to_speech_coqui(story_text, language_code, progress_bar, voice_sample_path=None):
    """
    voice_sample_path can be a BytesIO object (if user uploaded)
    or a string (if using 'Islam.wav').
    
    If it's BytesIO, we re-export it via pydub to ensure it's a valid PCM WAV
    before passing it to Coqui TTS.
    """
    try:
        with st.spinner("Synthesizing speech..."):
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            tts = TTS(model_name=model_name)
            progress_bar.progress(75)

            # If user uploaded a file, voice_sample_path will be a BytesIO
            if isinstance(voice_sample_path, BytesIO):
                # Convert user-uploaded WAV to a standard PCM WAV
                voice_sample_path.seek(0)
                try:
                    audio_seg = AudioSegment.from_file(voice_sample_path, format="wav")
                except Exception as ex:
                    st.error(f"Error reading uploaded WAV file: {ex}")
                    return None

                # Create a temp PCM WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    audio_seg.export(tmp_wav.name, format="wav")
                    speaker_wav_path = tmp_wav.name
            else:
                # It's a file path (default "Islam.wav")
                speaker_wav_path = voice_sample_path

            # Now run Coqui TTS
            with BytesIO() as audio_buffer:
                tts.tts_to_file(
                    text=story_text,
                    speaker_wav=speaker_wav_path,
                    file_path=audio_buffer,
                    language=language_code
                )
                audio_buffer.seek(0)
                progress_bar.progress(90)
                return audio_buffer.read()

    except Exception as e:
        st.error(f"An error occurred during TTS: {e}")
        return None

# ----------------------------
# 5) Mixing Narration + Background
# ----------------------------
def mix_audio_files(narration_data, background_path, progress_bar, music_volume_db=-15, fade_out_ms=3000):
    with st.spinner("Mixing audio..."):
        narration = AudioSegment.from_file(BytesIO(narration_data), format="wav")
        narration_duration = len(narration)
        background = AudioSegment.from_file(background_path)

        if len(background) < narration_duration:
            times_to_repeat = (narration_duration // len(background)) + 1
            background = background * times_to_repeat

        background = background[:narration_duration].fade_out(fade_out_ms)
        background = background + music_volume_db
        final_mix = background.overlay(narration, position=0)

        out_buffer = BytesIO()
        final_mix.export(out_buffer, format="wav")
        progress_bar.progress(100)
        return out_buffer.read()

# ----------------------------
# 6) Streamlit App
# ----------------------------
def main():
    st.title("Multilingual Fairy Tale Generator with Feedback")

    # Language selection
    language = st.selectbox("Choose the language for your fairy tale:", list(LANGUAGE_MAP.keys()))
    language_code = LANGUAGE_MAP[language]

    # User inputs
    scenario = st.text_input("Enter an initial scenario or prompt for your fairy tale:")
    main_character = st.text_input("Who is your main character?")

    # Theme selection
    theme_options = ["space", "fantastic", "medieval", "horror", "sea", "sci-fi", "forest", "Other"]
    selected_theme = st.radio("Select a theme", theme_options)

    other_theme = ""
    if selected_theme == "Other":
        other_theme = st.text_input("Enter your custom theme:")

    # Voice example uploader
    st.subheader("Optional: Upload a Voice Example")
    voice_file = st.file_uploader("Upload a WAV file to customize narration voice:", type=["wav"])

    # Progress bar
    progress_bar = st.progress(0)

    # Generate button
    if st.button("Generate Fairy Tale"):
        final_theme = other_theme if selected_theme == "Other" else selected_theme

        # Generate fairy tale
        fairy_tale = generate_fairy_tale(scenario, main_character, final_theme, language_code, progress_bar)
        if fairy_tale:
            st.subheader(f"AI-Generated Fairy Tale ({language})")
            st.write(fairy_tale)

            # Pick background music
            bg_music_path = pick_background_music(final_theme)

            # Use uploaded voice or default "Islam.wav"
            if voice_file is not None:
                voice_path = BytesIO(voice_file.read())  # user-uploaded
            else:
                voice_path = "Islam.wav"  # fallback to default voice

            # Convert to TTS
            narration_data = text_to_speech_coqui(fairy_tale, language_code, progress_bar, voice_path)
            if narration_data:
                # Mix narration + background
                final_mix_data = mix_audio_files(narration_data, bg_music_path, progress_bar)

                st.subheader("Final Narrated Fairy Tale with Background Music")
                st.audio(final_mix_data, format="audio/wav")

                st.download_button(
                    label="Download Narrated Fairy Tale",
                    data=final_mix_data,
                    file_name="narrated_fairy_tale.wav",
                    mime="audio/wav"
                )

            # --- Like/Dislike Buttons ---
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Like", key="like_button"):
                    st.session_state["feedback"] = "like"
                    st.success("You liked this story! Future stories will try to maintain the same style.")

            with col2:
                if st.button("👎 Dislike", key="dislike_button"):
                    st.session_state["feedback"] = "dislike"
                    st.warning("You disliked this story. Future stories will try a different style or tone.")

if __name__ == "__main__":
    main()
