import streamlit as st
import ebooklib
from ebooklib import epub
import lxml.html
from lxml import etree
import tempfile
import os
import nltk
import re

# Download NLTK data if not already present
nltk.download('punkt', quiet=True)

def extract_chapter_elements(content):
    """Extract elements from the chapter content, preserving order."""
    # Parse the HTML content
    tree = lxml.html.fromstring(content)
    # Extract elements
    elements = []
    # Find the body element
    body = tree.xpath('//body')[0]
    # Iterate over the immediate children of body
    for elem in body:
        if elem.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'img', 'figure', 'figcaption', 'div']:
            elements.append(elem)
    return elements

def display_elements(current_index, elements):
    """Display three elements at a time, with middle one highlighted if it's a paragraph."""
    # Extract the three elements to be displayed
    display_elements = elements[max(current_index-1, 0):current_index+2]
    html_content = ""
    for i, elem in enumerate(display_elements):
        # Define base font style for readability
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 10px auto;
            padding: 15px;
            transition: text-shadow 0.5s;
        """
        # Highlight the middle element if it's a paragraph
        is_middle = (current_index == 0 and i == 0) or (current_index != 0 and i == 1)
        if is_middle and elem.tag == 'p':
            # Use NLTK to split paragraph into sentences
            paragraph_text = elem.text_content()
            # Use NLTK for sentence tokenization
            sentences = nltk.tokenize.sent_tokenize(paragraph_text)
            highlighted_sentences = []
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
                # Escape HTML special characters in sentence
                sentence_escaped = etree.Element("span")
                sentence_escaped.text = sentence.strip()
                sentence_html = etree.tostring(sentence_escaped, method='html', encoding='unicode').replace('<span>', '').replace('</span>', '')
                sentence_html = f'<span style="{highlighted_style}">{sentence_html}</span>'
                highlighted_sentences.append(sentence_html)
            paragraph_content = ' '.join(highlighted_sentences)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # For headings, adjust the font size and weight
            if elem.tag.startswith('h'):
                # Adjust font size according to heading level
                heading_level = int(elem.tag[1])
                heading_style = font_style + f"font-size: {24 + (6 - heading_level) * 2}px; font-weight: bold;"
                heading_text = elem.text_content()
                html_content += f"<div style='{heading_style}'>{heading_text}</div>"
            elif elem.tag == 'img':
                # For images, handle appropriately if needed
                pass  # Implement image handling if necessary
            elif elem.tag == 'figure':
                # For figures, include the inner HTML
                figure_html = lxml.html.tostring(elem, encoding='unicode')
                html_content += f"<div style='{font_style}'>{figure_html}</div>"
            else:
                # For other elements like captions, display them normally
                elem_content = elem.text_content()
                html_content += f"<div style='{font_style}'>{elem_content}</div>"
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
                # Try to get the chapter title
                if item.get_name():
                    title = item.get_name()
                else:
                    title = 'Chapter'
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            content = selected_item.get_content()
            content = content.decode('utf-8')  # Assuming UTF-8 encoding
            # Use the extract_chapter_elements function to get elements
            chapter_elements = extract_chapter_elements(content)

            # Initialize session state for the element index
            if 'current_element' not in st.session_state:
                st.session_state.current_element = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_element > 0:
                        st.session_state.current_element -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_element + 1 < len(chapter_elements):
                        st.session_state.current_element += 1

            # Display the elements
            display_elements(st.session_state.current_element, chapter_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
