import os
import replicate
import openai
import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import base64

# 🔐 Clés API (hardcodées pour test uniquement)
client = openai.api_key = st.secrets["OPENAI_API_KEY"]
os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]
# Streamlit UI
st.set_page_config(page_title="AI Interior Designer", layout="centered")
st.markdown("""
    <style>
    body {
        background-color: #0f0f0f;
        color: white;
    }
    .stButton>button {
        background-color: #444;
        color: white;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏠 AI Interior Designer")
st.write("Répondez aux questions ci-dessous pour générer une pièce selon vos goûts.")

if "prompt_v1" not in st.session_state:
    st.session_state.prompt_v1 = ""
if "prompt_v2" not in st.session_state:
    st.session_state.prompt_v2 = ""

with st.form("user_inputs"):
    piece_type = st.selectbox("Type de pièce", ["Salon", "Chambre", "Cuisine", "Salle de bain", "Bureau", "Salle à manger", "Hall d'entrée", "Dressing", "Toilettes", "Bibliothèque"])
    style = st.text_input("Style de la pièce", placeholder="Ex : Scandinave, Japandi, Industriel...")
    colors = st.text_input("Couleurs dominantes", placeholder="Ex : bois clair, blanc, beige")
    ambiance = st.text_input("Ambiance souhaitée", placeholder="Ex : Chaleureuse, lumineuse, calme...")
    matériaux = st.text_input("Matériaux préférés (optionnel)", placeholder="Ex : bois, métal, pierre")
    mobilier = st.text_area("Mobilier souhaité (optionnel)", placeholder="Ex : canapé d'angle, table basse, étagères murales...")
    éclairage = st.text_input("Éclairage (optionnel)", placeholder="Ex : lumière naturelle, suspensions design...")
    éléments_déco = st.text_input("Éléments décoratifs (optionnel)", placeholder="Ex : plantes, tableaux, tapis...")
    vue_extérieure = st.text_input("Vue extérieure (optionnel)", placeholder="Ex : grandes baies vitrées, jardin, ville...")
    fonction_spéciale = st.text_input("Fonction spéciale de la pièce (optionnel)", placeholder="Ex : coin lecture, espace télétravail...")
    inspirations = st.text_input("Références ou inspirations (optionnel)", placeholder="Ex : Pinterest, loft new-yorkais...")
    longueur = st.number_input("Longueur de la pièce (m)", min_value=1.0, step=0.1)
    largeur = st.number_input("Largeur de la pièce (m)", min_value=1.0, step=0.1)
    hauteur = st.number_input("Hauteur sous plafond (m)", min_value=2.0, step=0.1)
    contraintes = st.text_input("Contraintes particulières (optionnel)", placeholder="Ex : enfants, animaux, pas de meubles suspendus...")
    submit = st.form_submit_button("Générer le prompt")

if submit:
    with st.spinner("Génération du prompt avec ChatGPT..."):
        user_prompt = f"""
        Crée une description visuelle réaliste et détaillée d'une pièce de type {piece_type.lower()}.
        Style : {style.lower()}.
        Couleurs dominantes : {colors}.
        Ambiance générale : {ambiance}.
        Matériaux : {matériaux}.
        Mobilier : {mobilier}.
        Éclairage : {éclairage}.
        Éléments décoratifs : {éléments_déco}.
        Vue extérieure : {vue_extérieure}.
        Fonction spéciale : {fonction_spéciale}.
        Inspirations : {inspirations}.
        Contraintes à respecter : {contraintes}.
        Dimensions de la pièce : longueur {longueur} m, largeur {largeur} m, hauteur sous plafond {hauteur} m.
        Conçois une pièce harmonieuse et esthétiquement cohérente dans ce contexte.
        La description doit être compatible avec une IA de génération d’image (type Midjourney), sans mentionner le budget.
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en design intérieur et tu crées des descriptions réalistes de pièces pour des générateurs d'images IA."},
                {"role": "user", "content": user_prompt}
            ]
        )
        prompt = response.choices[0].message.content.strip()
        st.session_state.prompt_v1 = prompt
        st.success("Prompt généré !")
        st.text_area("Prompt Midjourney-like", prompt, height=180)

    with st.spinner("Génération des images avec Replicate..."):
        output_urls = replicate.run(
            "davisbrown/designer-architecture",
            input={"prompt": prompt, "num_outputs": 3}
        )

        images = []
        for url in output_urls:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            images.append(img)

    st.subheader("Choisissez votre image préférée")
    cols = st.columns(3)
    selected_index = None

    for i, col in enumerate(cols):
        with col:
            st.image(images[i], caption=f"Image {i+1}", use_column_width=True)
            if st.button(f"Choisir l'image {i+1}"):
                selected_index = i

    if selected_index is not None:
        selected_img = images[selected_index]
        output_path = f"generated_{piece_type.lower()}_{selected_index+1}.png"
        selected_img.save(output_path)
        st.success(f"Image sauvegardée sous : {output_path}")
        st.image(selected_img, caption="Image sélectionnée", use_column_width=True)

        def get_image_download_link(img, filename):
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            href = f"<a href='data:file/png;base64,{img_str}' download='{filename}'>📥 Télécharger l'image</a>"
            return href

        st.markdown(get_image_download_link(selected_img, output_path), unsafe_allow_html=True)

        with st.expander("🔧 Ajuster le prompt et régénérer"):
            adjusted_prompt = st.text_area("Modifiez le prompt si besoin :", st.session_state.prompt_v1, height=180)
            if st.button("🔄 Générer de nouvelles images"):
                with st.spinner("Génération d'images alternatives..."):
                    output_urls = replicate.run(
                        "davisbrown/designer-architecture",
                        input={"prompt": adjusted_prompt, "num_outputs": 3}
                    )
                    images = []
                    for url in output_urls:
                        response = requests.get(url)
                        img = Image.open(BytesIO(response.content))
                        images.append(img)

                st.session_state.prompt_v2 = adjusted_prompt
                st.subheader("Nouvelles propositions")
                for i, img in enumerate(images):
                    st.image(img, caption=f"Image {i+1} (ajustée)", use_column_width=True)
