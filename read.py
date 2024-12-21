import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString, Tag
import tempfile
import os
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')

from nltk.tokenize import sent_tokenize

def get_content_units(soup):
    """
    Processes the HTML content and returns a list of content units in the order they appear.
    Each content unit is a dictionary with 'type' and 'content' keys.
    """
    content_units = []

    def process_element(element):
        """Recursively process element and its children."""
        if isinstance(element, NavigableString):
            # Ignore strings that are whitespace
            if element.strip():
                # Wrap the text in a paragraph unit if it's significant
                content_units.append({'type': 'text', 'content': str(element)})
            return
        elif isinstance(element, Tag):
            # Process the element based on its tag
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Heading
                content_units.append({'type': 'heading', 'content': str(element)})
            elif element.name == 'p':
                p_class = element.get('class', [])
                if not p_class:
                    p_class = []
                # Check if the paragraph is empty or a spacer
                is_empty = not element.get_text(strip=True)
                if is_empty or 'spaceBreak1' in p_class:
                    # Spacer or empty paragraph
                    content_units.append({'type': 'spacer', 'content': str(element)})
                elif 'caption' in p_class:
                    # Caption
                    content_units.append({'type': 'caption', 'content': str(element)})
                elif 'centerImage' in p_class:
                    # Image (wrapped in a <p> tag)
                    content_units.append({'type': 'image', 'content': str(element)})
                elif 'chapterSubtitle' in p_class or 'chapterSubtitle1' in p_class or 'chapterOpenerText' in p_class:
                    # Treat these as headings
                    content_units.append({'type': 'heading', 'content': str(element)})
                else:
                    # Regular paragraph
                    content_units.append({'type': 'paragraph', 'content': str(element)})
            elif element.name in ['ul', 'ol']:
                # List
                content_units.append({'type': 'list', 'content': str(element)})
            elif element.name == 'div':
                # Process children of the div
                for child in element.contents:
                    process_element(child)
            elif element.name == 'img':
                # Image
                content_units.append({'type': 'image', 'content': str(element)})
            else:
                # Process children of other tags
                for child in element.contents:
                    process_element(child)
        else:
            # Other element types
            pass

    # Start processing from the body
    body = soup.find('body')
    if body:
        for elem in body.contents:
            process_element(elem)
    else:
        # Start from the root if body is not found
        for elem in soup.contents:
            process_element(elem)

    return content_units

def extract_chapter_title(item):
    """
    Extracts the chapter title from the EpubHtml item by parsing the content
    and looking for heading tags or the <title> tag.
    """
    soup = BeautifulSoup(item.get_content(), 'html.parser')
    # Try to find the first <h1>, <h2>, <h3>, or <title> tag
    title_tag = soup.find(['h1', 'h2', 'h3', 'title'])
    if title_tag:
        return title_tag.get_text().strip()
    else:
        # Fallback to the item's file name if no title is found
        return item.get_name()

def get_display_content(paragraph_index, content_units):
    """
    Given the current paragraph index, return the content units to display.
    Includes the headings associated with each paragraph, and ensures three paragraphs are displayed.
    """
    # Build a list of indices of paragraphs
    paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

    num_paragraphs = len(paragraph_indices)

    # Handle the case where no paragraphs are found
    if num_paragraphs == 0:
        return [], paragraph_index

    # Ensure paragraph_index is within bounds
    if paragraph_index < 0:
        paragraph_index = 0
    elif paragraph_index >= num_paragraphs:
        paragraph_index = num_paragraphs - 1

    # Get indices for the three paragraphs
    indices_to_show = []
    for offset in [-1, 0, 1]:
        para_idx = paragraph_index + offset
        if 0 <= para_idx < num_paragraphs:
            indices_to_show.append(para_idx)

    display_units = []
    for para_idx in indices_to_show:
        paragraph_pos = paragraph_indices[para_idx]

        # Collect any headings immediately preceding the paragraph
        idx = paragraph_pos - 1
        # Collect headings in reverse order until we hit a non-heading element
        headings = []
        while idx >= 0 and content_units[idx]['type'] in ['heading', 'image', 'caption', 'spacer']:
            if content_units[idx]['type'] == 'heading':
                headings.insert(0, content_units[idx])  # Insert at the beginning
            idx -= 1

        # Add headings to display units
        display_units.extend(headings)

        # Add the paragraph
        display_units.append(content_units[paragraph_pos])

        # Collect any non-paragraph content units immediately after the paragraph
        idx = paragraph_pos + 1
        while idx < len(content_units) and content_units[idx]['type'] not in ['paragraph', 'heading']:
            if content_units[idx]['type'] != 'spacer':
                display_units.append(content_units[idx])
            idx += 1

    return display_units, paragraph_index

def display_paragraphs(display_units, paragraph_index, content_units):
    """
    Displays the content units, highlighting the current paragraph.
    """
    # Build a list of indices of paragraphs
    paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

    # Handle the case where no paragraphs are found
    if not paragraph_indices:
        st.warning("No paragraphs found in this chapter.")
        return

    curr_para_pos = paragraph_indices[paragraph_index]

    # Prepare the HTML content
    html_content = ""

    for cu in display_units:
        content_type = cu['type']
        content_html = cu['content']
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 10px auto;
            padding: 15px;
            border: 1px solid var(--primary-color);
            transition: text-shadow 0.5s;
        """
        if content_type == 'heading':
            # Apply heading styles
            heading_style = font_style + "font-size: 28px; font-weight: bold; border: none; padding-top: 30px;"
            html_content += f"<div style='{heading_style}'>{content_html}</div>"
        elif content_type == 'paragraph':
            # Determine if this is the current paragraph to highlight
            if cu == content_units[curr_para_pos]:
                # Highlight the paragraph
                soup = BeautifulSoup(content_html, 'html.parser')

                # Handle any lists within the paragraph
                lists = soup.find_all(['ul', 'ol'])
                for lst in lists:
                    # Replace lists with placeholders to prevent splitting sentences within lists
                    placeholder = f"__LIST_PLACEHOLDER_{id(lst)}__"
                    lst.replace_with(placeholder)

                paragraph_text = soup.get_text()
                sentences = sent_tokenize(paragraph_text.strip())
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    # Replace placeholders back with the list HTML
                    if "__LIST_PLACEHOLDER_" in sentence:
                        for lst in lists:
                            placeholder = f"__LIST_PLACEHOLDER_{id(lst)}__"
                            if placeholder in sentence:
                                sentence = sentence.replace(placeholder, str(lst))
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                    """
                    if sentence.strip():
                        sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                        highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)

                # Re-insert any lists that were outside of sentences
                if "__LIST_PLACEHOLDER_" in paragraph_content:
                    for lst in lists:
                        placeholder = f"__LIST_PLACEHOLDER_{id(lst)}__"
                        if placeholder in paragraph_content:
                            paragraph_content = paragraph_content.replace(placeholder, str(lst))

                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Regular paragraph style
                html_content += f"<div style='{font_style}'>{content_html}</div>"
        elif content_type == 'caption':
            # Apply caption style
            caption_style = font_style + "font-size: 18px; font-style: italic; border: none;"
            html_content += f"<div style='{caption_style}'>{content_html}</div>"
        elif content_type == 'image':
            # Apply image style
            image_style = "display: flex; justify-content: center; margin: 20px 0;"
            html_content += f"<div style='{image_style}'>{content_html}</div>"
        elif content_type == 'list':
            # Apply list style
            list_style = font_style + "padding-left: 40px; list-style-type: disc; border: none;"
            # Ensure list tags are wrapped in a <div> with the style
            html_content += f"<div style='{list_style}'>{content_html}</div>"
        elif content_type == 'spacer':
            # Skip spacers or add appropriate spacing if needed
            pass
        else:
            # Default style for other content
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
        --color-5: #FBC02D;
        --text-color: #FFFFFF;
        --primary-color: #0E1117;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: #FBC02D;
            --text-color: #000000;
            --primary-color: #FFFFFF;
        }
    }

    /* Hide the Streamlit style elements (hamburger menu, header, footer) */
    
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive font sizes for mobile devices */
    @media only screen and (max-width: 600px) {
        div[style] {
            font-size: 5vw !important;
        }
    }

    ul, ol {
        margin: 0;
        padding-left: 1.5em;
    }

    li {
        margin-bottom: 0.5em;
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
                # Extract chapter title
                title = extract_chapter_title(item)
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')
            # Use the get_content_units function to get content units
            content_units = get_content_units(soup)

            # Build a list of indices of paragraphs
            paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

            # Initialize session state for the paragraph index
            if 'current_paragraph' not in st.session_state or st.session_state.chapter != selected_chapter:
                st.session_state.current_paragraph = 0
                st.session_state.chapter = selected_chapter  # Keep track of selected chapter

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph > 0:
                        st.session_state.current_paragraph -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph += 1

            # Get the display content units
            display_units, para_idx = get_display_content(st.session_state.current_paragraph, content_units)

            # Display the content units
            display_paragraphs(display_units, st.session_state.current_paragraph, content_units)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
