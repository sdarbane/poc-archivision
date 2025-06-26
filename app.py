import os
import replicate
import openai
import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64
from replicate.exceptions import ReplicateError

# Configuration Streamlit
st.set_page_config(page_title="🪄 Archivision — AI Interior Generator", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #0e1117;
        color: #f0f0f0;
        font-family: 'Segoe UI', sans-serif;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > textarea,
    .stSelectbox > div > div > div {
        background-color: #1f222b;
        color: #f0f0f0;
        border-radius: 8px;
        border: 1px solid #555;
    }
    .stButton > button {
        background: linear-gradient(to right, #7b2ff7, #f107a3);
        color: white;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: bold;
        border: none;
        transition: background 0.3s ease-in-out;
    }
    .stButton > button:hover {
        background: linear-gradient(to right, #f107a3, #7b2ff7);
    }
    </style>
""", unsafe_allow_html=True)

# API Keys (via Streamlit secrets)
openai.api_key = st.secrets["OPENAI_API_KEY"]
os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]

st.title("🪄 Archivision: AI-powered Interior Concept Generator")
st.markdown("Generate vivid, photorealistic interior designs using GPT-4 + Replicate.")

if "prompt_v1" not in st.session_state:
    st.session_state.prompt_v1 = ""

with st.form("interior_form"):
    st.subheader("📐 Design Parameters")
    col1, col2 = st.columns(2)
    with col1:
        room_type = st.text_input("Room type", "Living room")
        style = st.text_input("Interior style", "Japandi, modern")
        colors = st.text_input("Dominant colors", "Beige, wood, white")
        ambiance = st.text_input("Ambiance", "Cozy, calm")
        dimensions = st.text_input("Dimensions (LxW in meters)", "5x4")
        height = st.text_input("Ceiling height (in meters)", "2.8")
    with col2:
        furniture = st.text_area("Key furniture", "Sofa, bookshelves, coffee table")
        lighting = st.text_input("Lighting", "Natural light, pendant lights")
        decor = st.text_input("Decor elements", "Plants, abstract art")
        special_function = st.text_input("Special function (optional)", "Reading corner")
        view = st.text_input("Outside view (optional)", "Garden")
        constraints = st.text_input("Constraints (optional)", "Kids-friendly")

    submitted = st.form_submit_button("✨ Generate Prompt + Design")

if submitted:
    with st.spinner("🔮 Talking to GPT-4 to generate your design prompt..."):
        prompt_request = f"""
        You are an expert interior designer. Create a rich, visual prompt for a text-to-image AI based on:
        - Room: {room_type}
        - Style: {style}
        - Colors: {colors}
        - Ambiance: {ambiance}
        - Dimensions: {dimensions}m, Height: {height}m
        - Furniture: {furniture}
        - Lighting: {lighting}
        - Decor: {decor}
        - Special function: {special_function}
        - View: {view}
        - Constraints: {constraints}
        The prompt must be detailed and suitable for a model like Midjourney.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI for generating architectural visual prompts."},
                    {"role": "user", "content": prompt_request}
                ]
            )
            prompt = response.choices[0].message["content"].strip()
            st.session_state.prompt_v1 = prompt
            st.success("✅ Prompt generated!")
            st.code(prompt, language="markdown")
        except Exception as e:
            st.error(f"❌ GPT Error: {e}")

    with st.spinner("🖼️ Generating images via Replicate..."):
        try:
            output_urls = replicate.run(
                "davisbrown/designer-architecture:0d6f0893b05f14500ce03e45f54290cbffb907d14db49699f2823d0fd35def46",
                input={
                    "prompt": st.session_state.prompt_v1,
                    "num_outputs": 3,
                    "aspect_ratio": "16:9",
                    "guidance_scale": 3.5,
                    "output_quality": 100
                }
            )
            images = []
            for url in output_urls:
                response = requests.get(url)
                img = Image.open(BytesIO(response.content))
                images.append(img)
        except ReplicateError as e:
            st.error(f"❌ Replicate error: {e}")
            images = []

    if images:
        st.subheader("🖼️ Choose Your Favorite Design")
        cols = st.columns(3)
        for i, col in enumerate(cols):
            with col:
                st.image(images[i], caption=f"Image {i+1}", use_column_width=True)

        selected_index = st.radio("Which image do you want to download?", [1, 2, 3], horizontal=True) - 1
        selected_img = images[selected_index]
        output_path = f"archivision_{room_type.lower().replace(' ', '_')}_{selected_index+1}.png"
        selected_img.save(output_path)
        st.success(f"✅ Image saved: {output_path}")

        def download_link(img, filename):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            href = f"<a href='data:file/png;base64,{img_str}' download='{filename}'>📥 Download image</a>"
            return href

        st.markdown(download_link(selected_img, output_path), unsafe_allow_html=True)

        with st.expander("✏️ Regenerate with Modified Prompt"):
            adjusted = st.text_area("Edit prompt", st.session_state.prompt_v1, height=160)
            if st.button("🔄 Generate New Images"):
                with st.spinner("🔄 Regenerating..."):
                    try:
                        output_urls = replicate.run(
                            "davisbrown/designer-architecture:0d6f0893b05f14500ce03e45f54290cbffb907d14db49699f2823d0fd35def46",
                            input={
                                "prompt": adjusted,
                                "num_outputs": 3,
                                "aspect_ratio": "16:9",
                                "guidance_scale": 3.5,
                                "output_quality": 100
                            }
                        )
                        for i, url in enumerate(output_urls):
                            response = requests.get(url)
                            img = Image.open(BytesIO(response.content))
                            st.image(img, caption=f"Alternative {i+1}", use_column_width=True)
                    except ReplicateError as e:
                        st.error(f"❌ Replicate error: {e}")
