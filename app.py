import streamlit as st
import os
from publishing_agent import PublishingAgent


st.set_page_config(
    page_title="ArtFlow AI",
    layout="wide"
)

st.title("ArtFlow AI")
st.write("AI publishing folder agent for independent artists.")

api_key = st.text_input(
    "Enter Gemini API Key (Optional)",
    type="password",
    help="If left blank, the app will still create cropped images and fallback captions."
)

uploaded_files = st.file_uploader(
    "Upload artwork images",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

st.subheader("Brand Source")

website_link = st.text_input(
    "Client Website Link",
    placeholder="https://www.roxymegyesi.com/"
)

if uploaded_files:
    os.makedirs("uploads", exist_ok=True)

    st.subheader("Uploaded Artworks")

    for uploaded_file in uploaded_files:
        image_path = os.path.join("uploads", uploaded_file.name)

        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.image(image_path, caption=uploaded_file.name, width=250)

    if st.button("Generate Publishing Folders for All Images"):
        brand_context = {
            "website": website_link
        }

        agent = PublishingAgent(api_key if api_key.strip() else None)

        for uploaded_file in uploaded_files:
            image_path = os.path.join("uploads", uploaded_file.name)

            st.divider()
            st.subheader(f"Processing: {uploaded_file.name}")

            with st.spinner("Creating publishing folder..."):
                result = agent.process_artwork(image_path, brand_context)

            st.success(f"Publishing folder created for {uploaded_file.name}")

            st.subheader("Output Folder")
            st.code(result["output_folder"])

            st.subheader("Generated Content")

            with open(result["content_file"], "r", encoding="utf-8") as f:
                content = f.read()

            st.text_area(
                f"Content Pack - {uploaded_file.name}",
                content,
                height=400
            )

            st.subheader("Generated Images")

            for image in result["generated_images"]:
                st.image(image, width=300)

                with open(image, "rb") as file:
                    st.download_button(
                        label=f"Download {os.path.basename(image)}",
                        data=file,
                        file_name=os.path.basename(image),
                        mime="image/jpeg",
                        key=f"{uploaded_file.name}_{os.path.basename(image)}"
                    )

            st.subheader("Human Approval")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.button(
                    "Approve",
                    key=f"approve_{uploaded_file.name}"
                )

            with col2:
                st.button(
                    "Revise",
                    key=f"revise_{uploaded_file.name}"
                )

            with col3:
                st.button(
                    "Reject",
                    key=f"reject_{uploaded_file.name}"
                )

else:
    st.info("Upload one or more artwork images to begin.")