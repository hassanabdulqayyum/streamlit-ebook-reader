import streamlit as st
import ebooklib
from ebooklib import epub
from markdownify import markdownify as md

import tempfile
import os
import markdown

def get_content_units(html_content):
    """
    Converts HTML content to Markdown, splits into blocks, and returns content units.
    Each content unit is a dictionary with 'type' and 'content' keys.
    """
    # Convert HTML to Markdown
    md_content = md(html_content)
    
    # Split the content into blocks by double newlines
    blocks = md_content.split('\n\n')
    
    content_units = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        if block.startswith('#'):
            # Heading
            content_units.append({'type': 'heading', 'content': block})
        elif block.startswith('!['):
            # Image
            content_units.append({'type': 'image', 'content': block})
        elif block.startswith(('* ', '- ', '+ ', '1. ')):
            # List
            content_units.append({'type': 'list', 'content': block})
        else:
            # Paragraph
            content_units.append({'type': 'paragraph', 'content': block})
            
    return content_units

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
        while idx >= 0:
            prev_cu = content_units[idx]
            if prev_cu['type'] == 'heading':
                headings.insert(0, prev_cu)  # Insert at the beginning
            else:
                break
            idx -= 1
    
        # Add headings to display units
        display_units.extend(headings)
    
        # Add the paragraph
        display_units.append(content_units[paragraph_pos])
    
        # Collect any non-paragraph content units immediately after the paragraph
        idx = paragraph_pos + 1
        while idx < len(content_units) and content_units[idx]['type'] in ['caption', 'image', 'list']:
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
        content_md = cu['content']
        if content_type == 'heading':
            # Convert Markdown to HTML
            content_html = markdown.markdown(content_md)
            # Apply heading styles
            heading_style = "font-size: 28px; font-weight: bold; margin-top: 30px;"
            html_content += f"<div style='{heading_style}'>{content_html}</div>"
        elif content_type == 'paragraph':
            # Convert Markdown to HTML
            content_html = markdown.markdown(content_md)
            # Determine if this is the current paragraph to highlight
            if cu == content_units[curr_para_pos]:
                # Highlight the paragraph
                soup = markdown.markdown(content_md)
                paragraph_text = BeautifulSoup(soup, 'html.parser').get_text()
                sentences = paragraph_text.strip().split('. ')
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                    """
                    if sentence.strip():
                        # Ensure proper punctuation at the end
                        if not sentence.endswith('.'):
                            sentence += '.'
                        sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                        highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div>{paragraph_content}</div>"
            else:
                # Regular paragraph style
                html_content += f"<div>{content_html}</div>"
        elif content_type == 'list':
            # Convert Markdown to HTML
            content_html = markdown.markdown(content_md)
            html_content += f"<div>{content_html}</div>"
        elif content_type == 'image':
            # Convert Markdown to HTML
            content_html = markdown.markdown(content_md)
            image_style = "display: flex; justify-content: center; margin: 20px 0;"
            html_content += f"<div style='{image_style}'>{content_html}</div>"
        else:
            # Default style
            content_html = markdown.markdown(content_md)
            html_content += f"<div>{content_html}</div>"
    
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
                title = item.get_name()
                # Alternatively, use item.get_title() if available
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            html_content = selected_item.get_body_content().decode('utf-8')
            # Use the get_content_units function to get content units
            content_units = get_content_units(html_content)

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
