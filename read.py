import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os

def get_processed_paragraphs(soup):
    """
    Processes the HTML soup to generate a list of paragraph contents.
    Non-paragraph elements like captions and images are appended to the next paragraph.
    """
    processed_paragraphs = []
    temp_content = ''
    p_tags = soup.find_all('p')

    for p in p_tags:
        p_class = p.get('class', [])
        is_paragraph = 'para' in p_class or 'chapterOpenerText' in p_class

        if is_paragraph:
            # Append temp content to this paragraph if temp_content is not empty
            if temp_content:
                full_content = temp_content + '\n' + str(p)
                temp_content = ''
            else:
                full_content = str(p)
            processed_paragraphs.append(full_content)
        else:
            # Collect the content in temp_content to be added to the next paragraph
            temp_content += str(p) + '\n'

    # Handle any remaining temp_content (if last elements are not paragraphs)
    if temp_content:
        # Append to the last paragraph if exists, else add as a new paragraph
        if processed_paragraphs:
            processed_paragraphs[-1] += '\n' + temp_content
        else:
            processed_paragraphs.append(temp_content)

    return processed_paragraphs

def display_paragraphs(paragraph_index, processed_paragraphs):
    """
    Displays three paragraphs at a time, highlighting the middle one.
    Other elements like captions and images are displayed as part of the paragraph.
    """
    # Extract the three paragraphs to be displayed
    display_paragraphs = processed_paragraphs[max(paragraph_index-1, 0):paragraph_index+2]

    html_content = ""

    for i, paragraph_html in enumerate(display_paragraphs):
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
            transition: text-shadow 0.5s;
        """
        highlighted_style = """
            background-color: var(--highlight-color-{index});
            padding: 2px 5px;
            border-radius: 5px;
            color: var(--text-color);
            position: relative;
            z-index: 1;
        """

        # Parse the paragraph_html to get the text
        soup = BeautifulSoup(paragraph_html, 'html.parser')

        # Get the combined text of the paragraph and any associated elements
        paragraph_text = ''
        for content in soup.contents:
            if content.name == 'p':
                paragraph_text += content.get_text(separator=' ') + ' '
            else:
                paragraph_text += str(content) + ' '  # Include images or other tags

        # Highlight the middle paragraph (or first if at the beginning)
        is_highlighted = (paragraph_index == 0 and i == 0) or (paragraph_index != 0 and i == 1)

        if is_highlighted:
            sentences = paragraph_text.strip().split('. ')
            highlighted_sentence = [
                f'<span style="{highlighted_style.format(index=j % 5)}">{sentence.strip()}{"." if not sentence.strip().endswith(".") else ""}</span>'
                for j, sentence in enumerate(sentences)]
            paragraph_content = ' '.join(highlighted_sentence)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Include any images or captions in the paragraph_html
            html_content += f"<div style='{font_style}'>{paragraph_text}</div>"

    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)

def inject_custom_css():
    css = """
    <style>
    :root {
        /* Light mode colors */
        --highlight-color-0: #ffd54f;
        --highlight-color-1: #aed581;
        --highlight-color-2: #64b5f6;
        --highlight-color-3: #f06292;
        --highlight-color-4: #b39ddb;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            /* Dark mode colors with adjusted opacity */
            --highlight-color-0: rgba(251, 192, 45, 0.9); /* Semi-transparent yellow */
            --highlight-color-1: #d32f2f;
            --highlight-color-2: #1976d2;
            --highlight-color-3: #388e3c;
            --highlight-color-4: #512da8;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def main():
    # Inject the custom CSS into the app
    inject_custom_css()

    # Hide the Streamlit style elements (hamburger menu, header, footer)
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Responsive font sizes for mobile devices
    responsive_styles = """
        <style>
        @media only screen and (max-width: 600px) {
            div[style] {
                font-size: 5vw !important;
            }
        }
        </style>
    """
    st.markdown(responsive_styles, unsafe_allow_html=True)

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
            # Use the get_processed_paragraphs function to get paragraphs
            chapter_paragraphs = get_processed_paragraphs(soup)

            # Initialize session state for the paragraph index
            if 'current_paragraph' not in st.session_state:
                st.session_state.current_paragraph = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph > 0:
                        st.session_state.current_paragraph -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph + 1 < len(chapter_paragraphs):
                        st.session_state.current_paragraph += 1

            # Display the paragraphs
            display_paragraphs(st.session_state.current_paragraph, chapter_paragraphs)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
