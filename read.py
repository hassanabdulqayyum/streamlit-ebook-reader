import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
import bs4  # Ensure bs4 is imported

def process_element(element, elements, paragraph_indices):
    if isinstance(element, bs4.element.Tag):
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements.append({'type': 'heading', 'content': str(element)})
        elif element.name == 'p':
            elements.append({'type': 'paragraph', 'content': str(element)})
            paragraph_indices.append(len(elements)-1)
        elif element.name == 'img':
            elements.append({'type': 'image', 'content': str(element)})
        elif element.name in ['div', 'section', 'body']:
            for child in element.contents:
                process_element(child, elements, paragraph_indices)
        else:
            # Handle other tags if necessary
            elements.append({'type': element.name, 'content': str(element)})
    elif isinstance(element, bs4.element.NavigableString):
        if element.strip():
            elements.append({'type': 'text', 'content': element.strip()})

def process_chapter_content(soup):
    elements = []
    paragraph_indices = []
    content_parent = soup.find('body') or soup
    process_element(content_parent, elements, paragraph_indices)
    return elements, paragraph_indices

def display_paragraphs(current_paragraph_index, elements, paragraph_indices):
    """
    Displays three paragraphs at a time, highlighting the middle one.
    Also displays other elements like headings, images, etc.
    """
    # Get indices of the current, previous, and next paragraphs
    para_indices = paragraph_indices
    total_paragraphs = len(para_indices)
    
    # Determine the indices of the paragraphs to display
    indices_to_display = []
    if current_paragraph_index == 0:
        indices_to_display = para_indices[:min(3, total_paragraphs)]
    elif current_paragraph_index == total_paragraphs - 1:
        indices_to_display = para_indices[-min(3, total_paragraphs):]
    else:
        indices_to_display = para_indices[current_paragraph_index - 1: current_paragraph_index + 2]

    # Gather all element indices between the first and last paragraph indices to display
    start_elem_index = indices_to_display[0]
    end_elem_index = indices_to_display[-1]

    content_to_display = elements[start_elem_index:end_elem_index+1]

    html_content = ''

    for elem in content_to_display:
        elem_type = elem['type']
        elem_html = elem['content']

        # Apply appropriate styling based on element type
        if elem_type == 'heading':
            font_style = """
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 20px auto;
                padding: 15px;
            """
            html_content += f"<h2 style='{font_style}'>{elem_html}</h2>"
        elif elem_type == 'paragraph':
            font_style = """
                font-family: Georgia, serif;
                font-weight: 450;
                font-size: 20px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 10px auto;
                padding: 15px;
            """
            is_highlighted = (elem == elements[para_indices[current_paragraph_index]])
            if is_highlighted:
                # Split sentences using NLTK
                soup = BeautifulSoup(elem_html, 'html.parser')
                paragraph_text = soup.get_text(separator=' ')
                sentences = sent_tokenize(paragraph_text)
                highlighted_sentence = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                        position: relative;
                        z-index: 1;
                    """
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Display the paragraph without highlighting
                html_content += f"<div style='{font_style}'>{elem_html}</div>"

        elif elem_type == 'image' or elem_type == 'figure':
            # Handle image display
            html_content += elem_html
        else:
            # Other elements
            html_content += elem_html

    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)

def main():

    # Inject CSS styles
    st.markdown("""
    <style>
    :root {
        /* Dark theme colors */
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: #fbc02d;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: #fbc02d;
        }
    }

    /* Hide the Streamlit style elements (hamburger menu, header, footer) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive font sizes for mobile devices */
    @media only screen and (max-width: 600px) {
        div[style] {
            font-size: 5vw !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Reader")

    # Move file uploader to sidebar
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Load the EPUB file from the temporary file path
            book = epub.read_epub(tmp_file_path)
        except Exception as e:
            st.error(f"An error occurred while reading the EPUB file: {e}")
            return
        finally:
            # Clean up the temporary file
            os.remove(tmp_file_path)

        # Initialize the chapter content
        chapters = []
        chapter_titles = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                # Attempt to get the chapter title
                title = item.get_name()
                # Alternatively, use item.get_title() if available
                chapter_titles.append(title)

        if chapters:
            if 'selected_chapter' not in st.session_state:
                st.session_state.selected_chapter = chapter_titles[0]

            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles, index=chapter_titles.index(st.session_state.selected_chapter))

            if st.session_state.selected_chapter != selected_chapter:
                st.session_state.selected_chapter = selected_chapter
                st.session_state.current_paragraph_index = 0

            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')

            # Process chapter content to get elements and paragraph indices
            elements, paragraph_indices = process_chapter_content(soup)

            # Initialize session state for the paragraph index
            if 'current_paragraph_index' not in st.session_state:
                st.session_state.current_paragraph_index = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_index > 0:
                        st.session_state.current_paragraph_index -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_index + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_index += 1

            # Display the paragraphs
            display_paragraphs(st.session_state.current_paragraph_index, elements, paragraph_indices)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
