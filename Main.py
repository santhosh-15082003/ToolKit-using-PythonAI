import os
import streamlit as st  # pyrefly: ignore[missing-import]
import pandas as pd  # pyrefly: ignore[missing-import]
from docx import Document  # pyrefly: ignore[missing-import]
from PyPDF2 import PdfReader, PdfWriter  # pyrefly: ignore[missing-import]
from langchain_text_splitters import CharacterTextSplitter  # pyrefly: ignore[missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI  # pyrefly: ignore[missing-import]
from langchain_community.vectorstores import FAISS  # pyrefly: ignore[missing-import]
from langchain_classic.chains.question_answering import load_qa_chain  # pyrefly: ignore[missing-import]
import pytesseract  # pyrefly: ignore[missing-import]
from PIL import Image  # pyrefly: ignore[missing-import]


class PDF:

    def ChatPDF(self, text):
        # split into chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

        chunks = text_splitter.split_text(text)

        # Get Google Gemini API Key
        GOOGLE_API_KEY = st.text_input("Google Gemini API Key", type="password",
                                        help="Get your free key at https://aistudio.google.com/app/apikey")
        if GOOGLE_API_KEY:
            with st.spinner("Creating Knowledge Base..."):
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="gemini-embedding-2-preview",
                    google_api_key=GOOGLE_API_KEY
                )
                knowledge_base = FAISS.from_texts(chunks, embeddings)
            st.success("Knowledge Base created!")

            def ask_question(i=0):
                user_question = st.text_input("Ask a question about your PDF?", key=i)
                if user_question:
                    with st.spinner("Thinking..."):
                        docs = knowledge_base.similarity_search(user_question)
                        llm = ChatGoogleGenerativeAI(
                            model="gemini-3.6-flash",
                            google_api_key=GOOGLE_API_KEY,
                            temperature=0.3
                        )
                        chain = load_qa_chain(llm, chain_type="stuff")
                        response = chain.run(input_documents=docs, question=user_question)
                    st.write(response)
                    ask_question(i + 1)

            ask_question()

    def main_pdf(self):

        hide_st_style = """
                <style>
                #mainMenue {visibility: hidden;}
                footer {visibility: hidden;}
                #header {visibility: hidden;}
                </style>
        """
        st.markdown(hide_st_style, unsafe_allow_html=True)

        st.header("Ask your PDF 🤔💭")

        # uploading file
        pdf = st.file_uploader("Upload your PDF ", type="pdf")

        # extract the text
        if pdf is not None:
            option = st.selectbox("What you want to do with PDF📜", [
                "Meta Data📂",
                "Extract Raw Text📄",
                "Extract Links🔗",
                "Extract Images🖼️",
                "Make PDF password protected🔐",
                "ChatPDF💬"
            ])
            pdf_reader = PdfReader(pdf)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

            if option == "Meta Data📂":
                st.write(pdf_reader.metadata)

            elif option == "Make PDF password protected🔐":
                pswd = st.text_input("Enter your Password", type="password")
                if pswd:
                    with st.spinner("Encrypting..."):
                        pdf_writer = PdfWriter()
                        for page_num in range(len(pdf_reader.pages)):
                            pdf_writer.add_page(pdf_reader.pages[page_num])

                        pdf_writer.encrypt(pswd)
                        with open(f"{pdf.name.split('.')[0]}_encrypted.pdf", "wb") as f:
                            pdf_writer.write(f)

                        st.success("Encryption Successful!")
                        st.download_button(
                            label="Download Encrypted PDF",
                            data=open(f"{pdf.name.split('.')[0]}_encrypted.pdf", "rb").read(),
                            file_name=f"{pdf.name.split('.')[0]}_encrypted.pdf",
                            mime="application/octet-stream",
                        )
                        try:
                            os.remove(f"{pdf.name.split('.')[0]}_encrypted.pdf")
                        except Exception:
                            pass

            elif option == "Extract Raw Text📄":
                st.write(text)

            elif option == "Extract Links🔗":
                for page in pdf_reader.pages:
                    if "/Annots" in page:
                        for annot in page["/Annots"]:
                            subtype = annot.get_object()["/Subtype"]
                            if subtype == "/Link":
                                try:
                                    st.write(annot.get_object()["/A"]["/URI"])
                                except Exception:
                                    pass

            elif option == "Extract Images🖼️":
                for page in pdf_reader.pages:
                    try:
                        for img in page.images:
                            st.write(img.name)
                            st.image(img.data)
                    except Exception:
                        pass

            elif option == "PDF Annotation📝":
                for page in pdf_reader.pages:
                    if "/Annots" in page:
                        for annot in page["/Annots"]:
                            obj = annot.get_object()
                            st.write(obj)
                            st.write("***********")
                            annotation = {"subtype": obj["/Subtype"], "location": obj["/Rect"]}
                            st.write(annotation)

            elif option == "ChatPDF💬":
                pdf_obj = PDF()
                pdf_obj.ChatPDF(text)


class File:

    def process_multiple_files(self, files):
        combined_text = ""
        for uploaded_file in files:
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension == ".pdf":
                pdf_reader = PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    combined_text += page.extract_text()
            elif file_extension == ".txt":
                combined_text += uploaded_file.read().decode("utf-8")
            elif file_extension == ".xlsx":
                excel_data = pd.read_excel(uploaded_file)
                combined_text += excel_data.to_string()
            elif file_extension == ".sql":
                combined_text += uploaded_file.read().decode("utf-8")
            elif file_extension == ".docx":
                doc = Document(uploaded_file)
                for paragraph in doc.paragraphs:
                    combined_text += paragraph.text + "\n"
            elif file_extension == ".csv":
                csv_data = pd.read_csv(uploaded_file)
                combined_text += csv_data.to_string()
            else:
                st.warning(f"Unsupported file type: {file_extension}. Skipping.")
        return combined_text

    def main_file(self):

        st.header("FileQueryHub 📂🤖")

        files = st.file_uploader(
            "Upload multiple files",
            type=["pdf", "txt", "xlsx", "sql", "docx", "csv"],
            accept_multiple_files=True
        )

        if files:
            combined_text = self.process_multiple_files(files)
            GOOGLE_API_KEY = st.text_input("Google Gemini API Key", type="password",
                                            help="Get your free key at https://aistudio.google.com/app/apikey")

            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            chunks = text_splitter.split_text(combined_text)

            if GOOGLE_API_KEY:
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="gemini-embedding-2-preview",
                    google_api_key=GOOGLE_API_KEY
                )
                with st.spinner("Creating Knowledge Base..."):
                    knowledge_base = FAISS.from_texts(chunks, embeddings)
                st.success("Knowledge Base created!")

                st.write("Chat with Multiple Files 🗣️📚")

                def ask_question(i=0):
                    user_question = st.text_input("Ask a question about your Document?", key=i)
                    if user_question:
                        with st.spinner("Searching for answers..."):
                            docs = knowledge_base.similarity_search(user_question)
                            with st.expander("See relevant docs"):
                                st.write(docs)

                            llm = ChatGoogleGenerativeAI(
                                model="gemini-3.6-flash",
                                google_api_key=GOOGLE_API_KEY,
                                temperature=0.3
                            )
                            chain = load_qa_chain(llm, chain_type="stuff")
                            response = chain.run(input_documents=docs, question=user_question)
                        st.write(response)
                        ask_question(i + 1)

                ask_question()


class Ocr:
    # Set the path to your Tesseract installation (adjust based on your system)
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows

    @staticmethod
    def extract_text(image):
        """
        Extracts text from a PIL Image object.

        Args:
            image: A PIL Image object.

        Returns:
            The extracted text as a string.
        """
        try:
            # Convert image to RGB mode if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Extract text from the image
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""

    def main_ocr(self):

        st.title("OCR")

        uploaded_file = st.file_uploader("Choose an image", type=["jpg", "png", "jpeg"])

        if uploaded_file is not None:
            # Read the uploaded image
            image = Image.open(uploaded_file)

            # Extract text
            extracted_text = Ocr.extract_text(image)

            # Display the uploaded image and extracted text
            st.image(image, caption="Uploaded Image")

            if extracted_text:
                st.success(f"Extracted Text: {extracted_text}")
            else:
                st.warning("No text found in the image.")


def main():

    st.title("PYTHON TOOLKIT")

    # Let the user choose which module to use
    selected_module = st.selectbox("Select a Tool", ["Ask your PDF 🤔💭", "FileQueryHub 📂🤖", "Optical Character Recognition"])

    if selected_module == "Ask your PDF 🤔💭":
        pdf = PDF()
        pdf.main_pdf()
    elif selected_module == "FileQueryHub 📂🤖":
        file = File()
        file.main_file()
    elif selected_module == "Optical Character Recognition":
        ocr = Ocr()
        ocr.main_ocr()


if __name__ == "__main__":
    main()
