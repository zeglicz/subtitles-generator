import streamlit as st
from io import BytesIO
from openai import OpenAI
from pydub import AudioSegment
from dotenv import dotenv_values

env = dotenv_values(".env.local")
openai_client = OpenAI(api_key=env["OPENAI_API_KEY"])

st.title('Subtitles generator')

# Inicjalizacja stanu sesji dla przechowywania transkrypcji
if 'transcript' not in st.session_state:
    st.session_state.transcript = None

# Interfejs użytkownika z pustą opcją na początku
file_type = st.selectbox('Select file type', ['', 'mp3', 'mp4', 'wav'])

# Jeśli wybrany typ pliku nie jest pusty
if file_type:
    uploaded_file = st.file_uploader(f"Upload {file_type} file", type=[file_type])

    if uploaded_file is not None:
        # Zapisanie przesłanego pliku tymczasowo
        temp_file_path = f"temp.{file_type}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Wyświetlenie przesłanego pliku
        if file_type == 'mp4':
            st.video(temp_file_path)

            # Ekstrakcja i wyświetlenie dźwięku z wideo
            st.subheader("Extracted Audio")
            audio = AudioSegment.from_file(temp_file_path, format="mp4")
            audio_path = "extracted_audio.mp3"
            audio.export(audio_path, format="mp3")
            st.audio(audio_path)

        elif file_type in ['mp3', 'wav']:
            st.audio(temp_file_path)

        # Użycie formularza do kontrolowania generowania transkrypcji
        with st.form(key='transcription_form'):
            st.write("Click the button below to generate subtitles")
            submit_button = st.form_submit_button(label='Transcribe')

            if submit_button:
                # Przygotowanie BytesIO do przechowania audio
                audio_bytes = BytesIO()

                # Konwersja w zależności od typu pliku
                if file_type == 'mp4':
                    st.info("Converting video to audio...")
                    # Możemy użyć już wyekstrahowanego audio
                    audio = AudioSegment.from_file(audio_path, format="mp3")
                    audio.export(audio_bytes, format="mp3")
                elif file_type == 'mp3':
                    st.info("Processing mp3 file...")
                    audio = AudioSegment.from_file(temp_file_path, format="mp3")
                    audio.export(audio_bytes, format="mp3")
                elif file_type == 'wav':
                    st.info("Processing wav file...")
                    audio = AudioSegment.from_file(temp_file_path, format="wav")
                    audio.export(audio_bytes, format="mp3")

                # Ustawienie wskaźnika na początek
                audio_bytes.seek(0)

                # Generowanie transkrypcji
                st.info("Generating transcript...")
                try:
                    transcript = openai_client.audio.transcriptions.create(
                        file=("audio.mp3", audio_bytes),
                        model="whisper-1",
                        response_format="srt"
                    )

                    # Zapisanie transkrypcji w stanie sesji
                    st.session_state.transcript = transcript

                except Exception as e:
                    st.error(f"Error generating transcript: {str(e)}")

        # Wyświetlenie transkrypcji i przycisku pobierania POZA formularzem
        if st.session_state.transcript:
            st.subheader("Generated Subtitles (SRT format)")
            st.text_area("Transcript", value=st.session_state.transcript, height=300)

            # Opcja pobrania (poza formularzem)
            st.download_button(
                label="Download SRT file",
                data=st.session_state.transcript,
                file_name="subtitles.srt",
                mime="text/plain"
            )

        # Uwaga: w Streamlit pliki nie są usuwane automatycznie między sesjami
        # Możliwe, że warto dodać jakąś logikę czyszczenia starych plików

    else:
        st.info(f"Please upload a {file_type} file to generate subtitles.")
else:
    st.info("Please select a file type first.")