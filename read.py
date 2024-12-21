import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup
import bs4
import tempfile
import os
import re

def process_chapter_content(soup):
    """
    Processes the chapter content soup into a flat list of elements with types.
    """
    elements = []
    block_elements = set(['p', 'div', 'figure', 'blockquote', 'ul', 'ol', 'li', 
                          'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    def recursively_process_node(node):
        for child in node.contents:
            if isinstance(child, bs4.element.Tag):
                if child.name in block_elements:
                    # It's a block element, add to elements
                    elements.append({'type': child.name, 'content': child})
                else:
                    # It's an inline element or unrecognized tag, process its children
                    recursively_process_node(child)
            elif isinstance(child, bs4.element.NavigableString):
                text = child.strip()
                if text:
                    # Check if parent is a block element
                    if child.parent and child.parent.name in block_elements:
                        # Do not add text separately; it will be included in the block element
                        pass
                    else:
                        # Add as a text element
                        elements.append({'type': 'text', 'content': text})

    recursively_process_node(soup.body)
    return elements

def render_element(element):
    """
    Renders an HTML string for an element based on its type
    """
    if element['type'] == 'text':
        html = f"<p>{element['content']}</p>"
        return html
    else:
        # For all other types, convert the content to string (which is HTML)
        html = str(element['content'])
        return html

def split_sentences(text):
    # Use regex to split sentences on period, question mark, exclamation mark followed by space
    # This regex avoids splitting at common abbreviations and handles footnote references
    sentence_endings = re.compile(r'(?<!\b(?:[A-Za-z]\.|[A-Za-z]{2}\.|[A-Za-z]{3}\.))(?<=[.!?])\s+')
    sentences = sentence_endings.split(text.strip())
    return sentences

def display_elements(element_index, elements):
    """
    Displays three elements at a time, highlighting the middle one if it's a paragraph.
    """
    # Get the elements to display
    display_elements = elements[max(element_index - 1, 0): element_index + 2]

    html_content = ""

    for i, element in enumerate(display_elements):
        # Define base font style
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 10px auto;
            padding: 15px;
            /* Additional styles */
        """

        # Determine if this element is the middle one to highlight
        is_highlighted = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)

        if is_highlighted and element['type'] == 'p':
            # Highlight sentences
            # Get the text content
            paragraph_text = element['content'].get_text(separator=' ', strip=True)
            # Split into sentences
            sentences = split_sentences(paragraph_text)
            # Apply highlighting to sentences
            highlighted_sentences = []
            for j, sentence in enumerate(sentences):
                color_variable = f"var(--color-{(j % 5) + 1})"
                highlighted_style = f"""
                    background-color: {color_variable};
                    padding: 2px 5px;
                    border-radius: 5px;
                    color: var(--text-color);
                    position: relative;
                    z-index: 1;
                """
                # Clean up the sentence
                sentence = sentence.strip()
                # Build the sentence HTML
                sentence_html = f'<span style="{highlighted_style}">{sentence}</span>'
                highlighted_sentences.append(sentence_html)
            # Combine the sentences
            paragraph_content = ' '.join(highlighted_sentences)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Render the element without highlighting
            element_html = render_element(element)
            html_content += f"<div style='{font_style}'>{element_html}</div>"

    # Display the content
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
                # Attempt to get the chapter title from the item's metadata
                title = item.get_name()
                # If you want to extract more meaningful titles, you might need to parse the content
                # and find headings or use item.get_content() to extract title tags
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')

            # Process the chapter content into elements
            elements = process_chapter_content(soup)

            # Initialize session state for the element index
            if 'current_element' not in st.session_state:
                st.session_state.current_element = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_element > 0:
                        st.session_state.current_element -= 1
            with col2:
                st.write(f"Element {st.session_state.current_element + 1} of {len(elements)}")
            with col3:
                if st.button("Next"):
                    if st.session_state.current_element + 1 < len(elements):
                        st.session_state.current_element += 1

            # Display the elements
            display_elements(st.session_state.current_element, elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
