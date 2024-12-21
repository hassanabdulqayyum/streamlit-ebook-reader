import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import nltk
nltk.download('punkt')  # Ensure the 'punkt' tokenizer is available
from nltk.tokenize import sent_tokenize
import bs4  # Ensure bs4 is properly imported

def get_processed_elements(soup):
    """
    Parses the HTML soup to generate a list of elements with type and content.
    Elements include headings, paragraphs, images, figures, etc.
    """
    elements = []
    body = soup.find('body')
    if body:
        for child in body.children:
            if isinstance(child, bs4.element.Tag):
                if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Heading
                    heading_text = child.get_text(separator=' ', strip=True)
                    heading_level = int(child.name[1])
                    elements.append({'type': 'heading', 'content': heading_text, 'level': heading_level})
                elif child.name == 'p':
                    # Remove 'sup' tags (footnotes)
                    for sup in child.find_all('sup'):
                        sup.decompose()
                    paragraph_text = child.get_text(separator=' ', strip=False)
                    elements.append({'type': 'paragraph', 'content': paragraph_text})
                elif child.name == 'figure':
                    # Figure with optional caption
                    fig_content = {'type': 'figure'}
                    img = child.find('img')
                    caption = child.find('figcaption')
                    if img:
                        fig_content['image_src'] = img.get('src')
                    if caption:
                        fig_content['caption'] = caption.get_text(strip=True)
                    elements.append(fig_content)
                elif child.name == 'img':
                    # Image
                    src = child.get('src')
                    elements.append({'type': 'image', 'src': src})
                else:
                    # Other tag
                    pass  # You can handle more tags as needed
            elif isinstance(child, bs4.element.NavigableString):
                # Text between tags
                text = str(child).strip()
                if text:
                    elements.append({'type': 'text', 'content': text})
    return elements

def display_elements(element_index, elements):
    """
    Displays three elements at a time, highlighting the middle paragraph.
    Other elements like headings, captions, and images are displayed appropriately.
    """
    # Extract the elements to be displayed
    display_elements = elements[max(element_index-1, 0):element_index+2]

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
            padding: 15px;
        """
        is_middle = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)

        if element['type'] == 'paragraph':
            paragraph_text = element['content']
            if is_middle:
                # Highlight sentences with different colors
                sentences = sent_tokenize(paragraph_text)
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
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Non-highlighted paragraph
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif element['type'] == 'heading':
            heading_text = element['content']
            heading_level = element['level']
            heading_style = f"""
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: {26 - heading_level * 2}px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 15px auto;
                padding: 10px;
            """
            html_content += f"<div style='{heading_style}'>{heading_text}</div>"
        elif element['type'] == 'image':
            img_src = element['src']
            if img_src:
                img_tag = f'<img src="{img_src}" style="max-width: 100%; height: auto;" />'
                html_content += f"<div style='text-align: center; margin: 10px 0;'>{img_tag}</div>"
        elif element['type'] == 'figure':
            fig_content = ""
            if 'image_src' in element:
                img_src = element['image_src']
                img_tag = f'<img src="{img_src}" style="max-width: 100%; height: auto;" />'
                fig_content += img_tag
            if 'caption' in element:
                caption = element['caption']
                caption_style = """
                    font-family: Georgia, serif;
                    font-size: 16px;
                    color: var(--text-color);
                    text-align: center;
                    margin-top: 5px;
                """
                fig_content += f"<div style='{caption_style}'>{caption}</div>"
            html_content += f"<div style='text-align: center; margin: 10px 0;'>{fig_content}</div>"
        elif element['type'] == 'text':
            text = element['content']
            if text:
                html_content += f"<div style='{font_style}'>{text}</div>"
        else:
            # Other types can be added as needed
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
        --text-color: #ffffff;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ff8a80;
            --color-2: #81d4fa;
            --color-3: #a5d6a7;
            --color-4: #ce93d8;
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
            --text-color: #000000;
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

    st.title("EPUB Reader")

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
                title = item.get_name()  # You can extract title more accurately if metadata is available
                # Alternatively, if item has get_title(), use that
                chapter_titles.append(title)

        if chapters:
            # In the session state, keep track of the selected chapter
            if 'selected_chapter' not in st.session_state:
                st.session_state.selected_chapter = chapter_titles[0]

            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles, index=chapter_titles.index(st.session_state.selected_chapter))

            if st.session_state.selected_chapter != selected_chapter:
                st.session_state.selected_chapter = selected_chapter
                st.session_state.current_element = 0

            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Use the get_processed_elements function to get elements
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
            display_elements(st.session_state.current_element, chapter_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
