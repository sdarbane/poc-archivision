import os
import replicate
import openai
import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64

# Setup OpenAI and Replicate API keys via Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]

# Streamlit UI Configuration
st.set_page_config(page_title="Archivision — AI Interior Generator", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #111111;
        color: #f0f0f0;
        font-family: 'Segoe UI', sans-serif;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > textarea,
    .stSelectbox > div > div > div {
        background-color: #1e1e1e;
        color: #f0f0f0;
        border-radius: 8px;
    }
    .stButton > button {
        background-color: #444;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🪄 Archivision: Create interior concepts with AI")
st.markdown("Craft beautiful, tailor-made room visuals with GPT-4 and Replicate.")

if "prompt_v1" not in st.session_state:
    st.session_state.prompt_v1 = ""

with st.form("interior_form"):
    st.subheader("📐 Design Input")
    col1, col2 = st.columns(2)
    with col1:
        room_type = st.text_input("Room type", "Living room")
        style = st.text_input("Interior style", "Minimalist, Japandi")
        colors = st.text_input("Dominant colors", "White, wood, beige")
        ambiance = st.text_input("Ambiance", "Cozy and calm")
        dimensions = st.text_input("Dimensions (LxW in meters)", "5x4")
        height = st.text_input("Ceiling height (in meters)", "2.8")
    with col2:
        furniture = st.text_area("Key furniture", "Sofa, low table, bookshelves")
        lighting = st.text_input("Lighting elements", "Natural light, pendant lights")
        decor = st.text_input("Decor elements", "Plants, abstract paintings")
        special_function = st.text_input("Special function (optional)", "Reading corner")
        view = st.text_input("Outside view (optional)", "Garden with large windows")
        constraints = st.text_input("Constraints (optional)", "Children-friendly")
    submitted = st.form_submit_button("✨ Generate Prompt")

if submitted:
    with st.spinner("Talking to GPT-4 to generate your design prompt..."):
        prompt_request = f"""
        You are an expert interior designer. Create a rich, vivid, midjourney-style image prompt for the following room:
        - Type: {room_type}
        - Style: {style}
        - Dominant colors: {colors}
        - Ambiance: {ambiance}
        - Dimensions: {dimensions}m, ceiling height: {height}m
        - Furniture: {furniture}
        - Lighting: {lighting}
        - Decor: {decor}
        - Function: {special_function}
        - View: {view}
        - Constraints: {constraints}
        The output should be detailed, visual, and suitable for a text-to-image AI.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI for generating architectural visual prompts."},
                {"role": "user", "content": prompt_request}
            ]
        )
        prompt = response.choices[0].message["content"].strip()
        st.session_state.prompt_v1 = prompt
        st.success("Prompt ready!")
        st.code(prompt, language="markdown")

    with st.spinner("Generating images via Replicate..."):
        output_urls = replicate.run(
            "davisbrown/designer-architecture",
            input={"prompt": st.session_state.prompt_v1, "num_outputs": 3}
        )

        images = []
        for url in output_urls:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            images.append(img)

    st.subheader("🖼️ Choose your favorite result")
    cols = st.columns(3)
    selected_index = None

    for i, col in enumerate(cols):
        with col:
            st.image(images[i], caption=f"Image {i+1}", use_column_width=True)
            if st.button(f"Select image {i+1}"):
                selected_index = i

    if selected_index is not None:
        selected_img = images[selected_index]
        output_path = f"archivision_{room_type.lower().replace(' ', '_')}_{selected_index+1}.png"
        selected_img.save(output_path)
        st.success(f"Saved: {output_path}")
        st.image(selected_img, caption="✅ Selected image", use_column_width=True)

        def download_link(img, filename):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            href = f"<a href='data:file/png;base64,{img_str}' download='{filename}'>📥 Download image</a>"
            return href

        st.markdown(download_link(selected_img, output_path), unsafe_allow_html=True)

        with st.expander("🔧 Adjust prompt and regenerate"):
            adjusted = st.text_area("Edit prompt", st.session_state.prompt_v1, height=160)
            if st.button("🔄 Generate new images"):
                with st.spinner("Generating alternative concepts..."):
                    output_urls = replicate.run(
                        "davisbrown/designer-architecture",
                        input={"prompt": adjusted, "num_outputs": 3}
                    )
                    for i, url in enumerate(output_urls):
                        response = requests.get(url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, caption=f"Alternative {i+1}", use_column_width=True)
