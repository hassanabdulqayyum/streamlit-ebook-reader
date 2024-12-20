import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os

# Colors for highlighting sentences
colors = ["#ffd54f", "#aed581", "#64b5f6", "#f06292", "#ba68c8"]  # Lighter pastel shades

def get_color(index):
    # Cycle through the color list based on the sentence index
    return colors[index % len(colors)]

def get_processed_paragraphs(soup):
    # [Your existing get_processed_paragraphs function remains unchanged]
    # ...

def display_paragraphs(paragraph_index, processed_paragraphs):
    # [Your existing display_paragraphs function remains unchanged]
    # ...

def main():
    st.title("EPUB Reader")

    # Step 1: Check if the file has been uploaded
    if 'uploaded_file_content' not in st.session_state:
        # Display the file uploader
        uploaded_file = st.file_uploader("Choose an EPUB file", type="epub")
        if uploaded_file is not None:
            # Save the uploaded file content to session state
            st.session_state['uploaded_file_content'] = uploaded_file.getvalue()
    else:
        # File has been uploaded, proceed to the next step
        pass  # We don't display the file uploader again

    # Step 2: Process the EPUB file if uploaded
    if 'uploaded_file_content' in st.session_state:
        if 'book' not in st.session_state:
            # Create a temporary file to store the EPUB file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
                tmp_file.write(st.session_state['uploaded_file_content'])
                tmp_file_path = tmp_file.name

            try:
                # Load the EPUB file from the temporary file path
                book = epub.read_epub(tmp_file_path)
                st.session_state['book'] = book
            except Exception as e:
                st.error(f"An error occurred while reading the EPUB file: {e}")
                del st.session_state['uploaded_file_content']
                return
            finally:
                # Clean up the temporary file
                os.remove(tmp_file_path)
        else:
            # Book is already loaded
            book = st.session_state['book']

        # Step 3: Check if a chapter has been selected
        if 'selected_chapter' not in st.session_state:
            # Initialize the chapters
            if 'chapter_titles' not in st.session_state:
                chapters = []
                chapter_titles = []
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        chapters.append(item)
                        # Attempt to get the chapter title
                        title = item.get_name()
                        chapter_titles.append(title)
                st.session_state['chapters'] = chapters
                st.session_state['chapter_titles'] = chapter_titles
            else:
                chapters = st.session_state['chapters']
                chapter_titles = st.session_state['chapter_titles']

            # Display the chapter selection dropdown
            selected_chapter = st.selectbox("Select a chapter", st.session_state['chapter_titles'])
            st.session_state['selected_chapter'] = selected_chapter
            chapter_index = st.session_state['chapter_titles'].index(selected_chapter)
            st.session_state['selected_chapter_index'] = chapter_index
        else:
            # Chapter has been selected, proceed to display content
            selected_chapter = st.session_state['selected_chapter']
            chapter_index = st.session_state['selected_chapter_index']
            # We don't display the chapter selection again

        # Step 4: Display the chapter content
        selected_item = st.session_state['chapters'][chapter_index]

        # Parse and process the chapter content
        if 'chapter_paragraphs' not in st.session_state:
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            chapter_paragraphs = get_processed_paragraphs(soup)
            st.session_state['chapter_paragraphs'] = chapter_paragraphs
        else:
            chapter_paragraphs = st.session_state['chapter_paragraphs']

        # Initialize or retrieve the current paragraph index
        if 'current_paragraph' not in st.session_state:
            st.session_state['current_paragraph'] = 0

        # Display navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous"):
                if st.session_state['current_paragraph'] > 0:
                    st.session_state['current_paragraph'] -= 1
        with col2:
            # Optionally, you can show current paragraph info
            st.write(f"Paragraph {st.session_state['current_paragraph'] + 1} of {len(chapter_paragraphs)}")
        with col3:
            if st.button("Next"):
                if st.session_state['current_paragraph'] + 1 < len(chapter_paragraphs):
                    st.session_state['current_paragraph'] += 1

        # Display the paragraphs
        display_paragraphs(st.session_state['current_paragraph'], chapter_paragraphs)

    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
