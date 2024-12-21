import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
import bs4  # Import the bs4 module
from bs4 import BeautifulSoup
import tempfile
import os
import re

def split_into_sentences(text):
    """
    Splits text into sentences, handling periods within references and abbreviations.
    """
    # Regex pattern to split text into sentences considering exceptions
    pattern = r'''
    (?<!\b\w\.\w)      # Negative lookbehind for abbreviations like U.S.A
    (?<![A-Z][a-z]\.)  # Negative lookbehind for abbreviations like Dr.
    (?<!\s[0-9]\.)     # Negative lookbehind for numbered lists
    (?<!\s[A-Z]\.)     # Negative lookbehind for single-letter initials
    (?<!\[\d+\])       # Negative lookbehind for references like [1]
    (?<=\.|\?|!)       # Positive lookbehind for end of sentence punctuation
    \s+                # Split at whitespace
    '''
    sentences = re.split(pattern, text, flags=re.VERBOSE)
    return sentences

def get_processed_elements(soup):
    """
    Processes the HTML soup to generate a list of content elements.
    Classify elements as paragraphs, headings, images, captions, etc.
    """
    processed_elements = []
    # Loop over all direct children of body or the entire soup if body is None
    if soup.body is None:
        body_elements = soup.find_all(recursive=False)
    else:
        body_elements = list(soup.body.children)
    for element in body_elements:
        if isinstance(element, bs4.element.Tag):
            if element.name == 'p':
                # It's a paragraph
                processed_elements.append({'type': 'paragraph', 'content': element})
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # It's a heading
                processed_elements.append({'type': 'heading', 'content': element})
            elif element.name == 'img':
                # It's an image
                processed_elements.append({'type': 'image', 'content': element})
            elif element.name == 'figure':
                # May contain image and caption
                processed_elements.append({'type': 'figure', 'content': element})
            elif element.name == 'div' or element.name == 'span':
                # Process div's children recursively
                child_elements = get_processed_elements(element)
                processed_elements.extend(child_elements)
            else:
                # Other elements
                pass
        elif isinstance(element, bs4.element.NavigableString):
            text = str(element).strip()
            if text:
                processed_elements.append({'type': 'text', 'content': text})
    return processed_elements

def display_content(element_index, processed_elements):
    """
    Displays three content elements at a time, highlighting the middle one if it's a paragraph.
    Other elements like headings, captions, and images are displayed appropriately.
    """
    # Extract the three elements to be displayed
    display_elements = processed_elements[max(element_index-1, 0):element_index+2]

    html_content = ""

    for i, element in enumerate(display_elements):
        # Define base font style for readability
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
            /* Remove or set background-color to transparent */
            /* background-color: transparent; */
            transition: text-shadow 0.5s;
        """

        element_type = element['type']
        content = element['content']

        # Highlight the middle element (or first if at the beginning)
        is_highlighted = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)

        if element_type == 'paragraph':
            paragraph_text = content.get_text(separator=' ')
            if is_highlighted:
                # Split sentences carefully
                sentences = split_into_sentences(paragraph_text)
                if not sentences:
                    sentences = [paragraph_text.strip()]
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
                    # Include the trailing punctuation
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
            else:
                paragraph_content = paragraph_text

            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"

        elif element_type == 'heading':
            heading_text = content.get_text(separator=' ')
            heading_style = """
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 10px auto;
                bottom-margin: 20px;
                padding: 15px;
                /* Customize heading styles as needed */
            """
            html_content += f"<div style='{heading_style}'>{heading_text}</div>"

        elif element_type == 'image':
            # Include the image
            img_html = str(content)
            html_content += f"<div style='text-align: center;'>{img_html}</div>"

        elif element_type == 'figure':
            # Include the figure, handling image and caption
            figure_html = str(content)
            html_content += f"<div style='text-align: center;'>{figure_html}</div>"

        elif element_type == 'text':
            text = content.strip()
            if text:
                html_content += f"<div style='{font_style}'>{text}</div>"

        else:
            # Other types, skip or handle as needed
            pass

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
                # Alternatively, use item.get_title() if available
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Use the get_processed_elements function to get content elements
            chapter_elements = get_processed_elements(soup)

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
            display_content(st.session_state.current_element, chapter_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
