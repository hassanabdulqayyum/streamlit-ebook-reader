import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import tempfile
import os
import nltk
from nltk.tokenize import sent_tokenize

# Download NLTK data files
nltk.download('punkt')

def get_chapter_elements(soup):
    """
    Parses the chapter soup and returns a list of elements in order.
    Each element is a dictionary with keys 'type' and 'content'.
    Types can be 'heading', 'paragraph', 'image', 'caption', etc.
    """
    elements = []
    for elem in soup.body.children:
        if isinstance(elem, NavigableString):
            continue
        if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements.append({'type': 'heading', 'content': elem.get_text(separator=' ').strip()})
        elif elem.name == 'p':
            # Check if paragraph is empty
            text = elem.get_text(separator=' ').strip()
            if text:
                elements.append({'type': 'paragraph', 'content': text})
        elif elem.name == 'img':
            elements.append({'type': 'image', 'content': elem})
        elif elem.name == 'figure':
            # Figure may contain image and caption
            imgs = elem.find_all('img')
            for img in imgs:
                elements.append({'type': 'image', 'content': img})
            caption = elem.find('figcaption')
            if caption:
                elements.append({'type': 'caption', 'content': caption.get_text(separator=' ').strip()})
        elif elem.name == 'div':
            # Some EPUBs may use divs for different content
            class_list = elem.get('class', [])
            if 'caption' in class_list:
                elements.append({'type': 'caption', 'content': elem.get_text(separator=' ').strip()})
            else:
                # Check for paragraphs within div
                for child in elem.descendants:
                    if isinstance(child, NavigableString):
                        continue
                    if child.name == 'p':
                        text = child.get_text(separator=' ').strip()
                        if text:
                            elements.append({'type': 'paragraph', 'content': text})
        else:
            # Handle other elements if necessary
            pass

    return elements

def display_elements(element_index, elements):
    """
    Displays three elements at a time, highlighting the middle paragraph if it's a paragraph.
    Other elements like headings, images, captions are displayed appropriately.
    """
    # Extract the three elements to be displayed
    start_index = max(element_index - 1, 0)
    end_index = min(element_index + 2, len(elements))
    display_elements = elements[start_index:end_index]

    html_content = ""

    default_font_style = """
                font-family: Georgia, serif;
                font-weight: 450;
                font-size: 20px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 700px;
                margin: 10px auto;
                bottom-margin: 20px;
                padding: 15px;
                border: 1px solid var(--primary-color);
                transition: text-shadow 0.5s;
            """

    for i, element in enumerate(display_elements):
        # Determine if this is the middle element
        is_middle_element = (i == 1) if element_index != 0 else (i == 0)
        if element['type'] == 'paragraph':
            paragraph_text = element['content']
            if is_middle_element:
                # Use nltk to tokenize sentences
                sentences = sent_tokenize(paragraph_text)
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    # Avoid splitting on references or abbreviations
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                        position: relative;
                        z-index: 1;
                    """
                    sentence = sentence.strip()
                    # Ensure sentence ends with punctuation
                    if not sentence.endswith(('.', '!', '?')):
                        sentence += '.'
                    sentence_html = f'<span style="{highlighted_style}">{sentence}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{default_font_style}'>{paragraph_content}</div>"
            else:
                # Display paragraph normally
                html_content += f"<div style='{default_font_style}'>{paragraph_text}</div>"
        elif element['type'] == 'heading':
            # Display heading
            heading_text = element['content']
            heading_style = """
                font-family: Georgia, serif;
                font-weight: 600;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 800px;
                margin: 20px auto 10px auto;
                padding: 5px;
                /* No border for headings */
                border: none;
            """
            html_content += f"<h2 style='{heading_style}'>{heading_text}</h2>"
        elif element['type'] == 'image':
            # Display image if possible
            # Note: This requires handling the image data from the EPUB
            # For simplicity, we'll skip images or handle them if desired
            pass
        elif element['type'] == 'caption':
            # Display caption
            caption_text = element['content']
            caption_style = """
                font-family: Georgia, serif;
                font-weight: 400;
                font-size: 18px;
                color: var(--text-color-secondary);
                line-height: 1.4;
                max-width: 700px;
                margin: 5px auto;
                padding: 5px;
                font-style: italic;
            """
            html_content += f"<div style='{caption_style}'>{caption_text}</div>"
        # ... other types as needed

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
        --text-color: #ffffff;
        --text-color-secondary: #cccccc;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
            --text-color: #000000;
            --text-color-secondary: #333333;
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
                # Get title from the EPUB's table of contents if available
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')

            # Use the get_chapter_elements function to get elements
            elements = get_chapter_elements(soup)

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
