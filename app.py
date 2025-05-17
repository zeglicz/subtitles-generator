import streamlit as st
from io import BytesIO
from openai import OpenAI
from pydub import AudioSegment
from dotenv import dotenv_values

env = dotenv_values(".env.local")

st.set_page_config(page_title='Subtitles generator', layout='centered')
st.title('Subtitles generator')

def get_openai_client():
  return OpenAI(api_key=st.session_state['openai_api_key'])

if 'transcript' not in st.session_state:
    st.session_state.transcript = None

if 'previous_file' not in st.session_state:
    st.session_state.previous_file = None

if 'previous_file_type' not in st.session_state:
    st.session_state.previous_file_type = None

#
# MAIN
#

if not st.session_state.get('openai_api_key'):
  if 'OPENAI_API_KEY' in env:
    st.session_state['openai_api_key'] = env['OPENAI_API_KEY']
  else:
    st.info('Add your OpenAI API key to use the application')
    st.session_state['openai_api_key'] = st.text_input('API key')

if not st.session_state.get('openai_api_key'):
  st.stop()
  st.error('Invalid OpenAI API key')

openai_client = OpenAI(api_key=st.session_state['openai_api_key'])

file_type = st.selectbox('Select file type', ['', 'mp3', 'mp4', 'wav'])

if file_type != st.session_state.previous_file_type:
    st.session_state.transcript = None
    st.session_state.previous_file_type = file_type

if file_type:
    uploaded_file = st.file_uploader(f"Upload {file_type} file", type=[file_type])

    if uploaded_file is not None and uploaded_file != st.session_state.previous_file:
        st.session_state.transcript = None
        st.session_state.previous_file = uploaded_file

    if uploaded_file is not None:
        temp_file_path = f"temp/uploads/temp.{file_type}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if file_type == 'mp4':
            st.video(temp_file_path)

            st.subheader("Extracted Audio")
            audio = AudioSegment.from_file(temp_file_path, format="mp4")
            audio_path = "temp/exports/extracted_audio.mp3"
            audio.export(audio_path, format="mp3")
            st.audio(audio_path)

        elif file_type in ['mp3', 'wav']:
            st.audio(temp_file_path)

        with st.form(key='transcription_form'):
            st.write("Click the button below to generate subtitles")
            submit_button = st.form_submit_button(label='Transcribe')

            if submit_button:
                audio_bytes = BytesIO()

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

                audio_bytes.seek(0)

                st.info("Generating transcript...")
                try:
                    transcript = openai_client.audio.transcriptions.create(
                        file=("audio.mp3", audio_bytes),
                        model="whisper-1",
                        response_format="srt"
                    )

                    st.session_state.transcript = transcript

                except Exception as e:
                    st.error(f"Error generating transcript: {str(e)}")

        if st.session_state.transcript:
            st.subheader("Generated Subtitles (SRT format)")
            st.text_area("Transcript", value=st.session_state.transcript, height=300)

            st.download_button(
                label="Download SRT file",
                data=st.session_state.transcript,
                file_name="subtitles.srt",
                mime="text/plain"
            )

    else:
        st.info(f"Please upload a {file_type} file to generate subtitles.")
else:
    st.info("Please select a file type first.")