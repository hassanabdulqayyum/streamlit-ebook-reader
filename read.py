import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re

def get_content_elements(soup):
    """
    Processes the HTML soup to generate a list of content elements.
    Each element is a dictionary with 'type' and 'content'.
    Types can be 'paragraph', 'heading', 'image', 'caption', etc.
    """
    elements = []
    paragraph_positions = []
    def process_contents(parent):
        for content in parent.contents:
            if isinstance(content, str):
                continue
            if content.name == 'p':
                p_class = content.get('class', [])
                is_paragraph = 'para' in p_class or 'chapterOpenerText' in p_class or not p_class
                if is_paragraph:
                    elements.append({'type': 'paragraph', 'content': content})
                    paragraph_positions.append(len(elements)-1)
                else:
                    elements.append({'type': 'other', 'content': content})
            elif content.name in ['h1','h2','h3','h4','h5','h6']:
                elements.append({'type': 'heading', 'content': content})
            elif content.name == 'img':
                elements.append({'type': 'image', 'content': content})
            elif content.name in ['figure', 'figcaption']:
                elements.append({'type': content.name, 'content': content})
            else:
                elements.append({'type': 'other', 'content': content})

            # Process the content's children recursively, for nested elements
            if content.contents:
                process_contents(content)
    body = soup.find('body')
    process_contents(body)

    return elements, paragraph_positions

def get_display_range(paragraph_positions, current_paragraph_index, elements_length):
    # Determine the start and end element indices to display
    # For previous paragraph
    if current_paragraph_index > 0:
        start_element_index = paragraph_positions[current_paragraph_index -1]
    else:
        start_element_index = 0

    # For end_element_index
    if current_paragraph_index + 2 < len(paragraph_positions):
        end_element_index = paragraph_positions[current_paragraph_index + 2]
    else:
        end_element_index = elements_length
    return start_element_index, end_element_index

def split_sentences(paragraph_text):
    # A regex to split sentences, matching punctuation
    # Avoid splitting at periods that are part of abbreviations or numbers
    sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s')

    sentences = sentence_endings.split(paragraph_text.strip())
    return sentences

def display_paragraphs(current_paragraph_index, elements, paragraph_positions):
    # Get the display range
    start_index, end_index = get_display_range(paragraph_positions, current_paragraph_index, len(elements))
    display_elements = elements[start_index:end_index]

    current_element_idx = paragraph_positions[current_paragraph_index]

    html_content = ""
    for idx, elem in enumerate(elements[start_index:end_index], start=start_index):
        content_html = str(elem['content'])
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 10px auto;
            bottom-margin: 20px;
            padding: 15px;
            border: 1px solid var(--primary-color);
            transition: text-shadow 0.5s;
        """
        if elem['type'] == 'heading':
            font_style += "font-size: 24px; font-weight: bold;"
            html_content += f"<div style='{font_style}'>{content_html}</div>"
        elif elem['type'] == 'paragraph':
            # Check if this is the current paragraph
            if idx == current_element_idx:
                # Highlight this paragraph
                paragraph_text = elem['content'].get_text()
                sentences = split_sentences(paragraph_text)
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j % 5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                        position: relative;
                        z-index: 1;
                    """
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Regular paragraph
                paragraph_text = elem['content'].get_text()
                paragraph_content = paragraph_text.strip()
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Other types
            html_content += f"<div style='{font_style}'>{content_html}</div>"
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
        --color-5: rgba(251, 192, 45, 0.9);
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
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
        # Create a temporary file to store the EPUB file
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
                # Alternatively, use item.get_name() or item.file_name
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Use the get_content_elements function to get content
            elements, paragraph_positions = get_content_elements(soup)

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
                    if st.session_state.current_paragraph_index + 1 < len(paragraph_positions):
                        st.session_state.current_paragraph_index += 1

            # Display the paragraphs
            display_paragraphs(st.session_state.current_paragraph_index, elements, paragraph_positions)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
