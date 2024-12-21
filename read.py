import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
from markdownify import markdownify as md

def get_markdown_content(soup):
    """
    Converts the HTML content to Markdown and splits it into content units.
    """
    # Convert the entire HTML to Markdown
    full_markdown = md(str(soup), heading_style="ATX")
    
    # Split the Markdown content into lines
    content_lines = full_markdown.split('\n')

    content_units = []
    current_paragraph = ""

    for line in content_lines:
        stripped_line = line.strip()
        if not stripped_line:
            # Empty line indicates a paragraph break
            if current_paragraph:
                content_units.append({'type': 'paragraph', 'content': current_paragraph.strip()})
                current_paragraph = ""
            continue
        elif stripped_line.startswith('#'):
            # This is a heading
            if current_paragraph:
                content_units.append({'type': 'paragraph', 'content': current_paragraph.strip()})
                current_paragraph = ""
            content_units.append({'type': 'heading', 'content': stripped_line})
        elif stripped_line.startswith(('-', '*', '+')) or stripped_line[0].isdigit():
            # This is a list item
            if current_paragraph:
                content_units.append({'type': 'paragraph', 'content': current_paragraph.strip()})
                current_paragraph = ""
            content_units.append({'type': 'list_item', 'content': stripped_line})
        else:
            # Accumulate lines into the current paragraph
            current_paragraph += ' ' + stripped_line

    # Add any remaining paragraph
    if current_paragraph:
        content_units.append({'type': 'paragraph', 'content': current_paragraph.strip()})

    # Combine consecutive list items into lists
    updated_content_units = []
    i = 0
    while i < len(content_units):
        if content_units[i]['type'] == 'list_item':
            # Start collecting list items
            list_items = []
            while i < len(content_units) and content_units[i]['type'] == 'list_item':
                list_items.append(content_units[i]['content'])
                i += 1
            # Combine into a list
            list_content = '\n'.join(list_items)
            updated_content_units.append({'type': 'list', 'content': list_content})
        else:
            updated_content_units.append(content_units[i])
            i += 1

    return updated_content_units

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
        headings = []
        while idx >= 0 and content_units[idx]['type'] in ['heading', 'image', 'caption']:
            if content_units[idx]['type'] == 'heading':
                headings.insert(0, content_units[idx])  # Insert at the beginning
            idx -= 1

        # Add headings to display units
        display_units.extend(headings)

        # Add the paragraph
        display_units.append(content_units[paragraph_pos])

        # Collect any content units immediately after the paragraph (e.g., lists)
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

    # Prepare the Markdown content
    markdown_content = ""

    for cu in display_units:
        content_type = cu['type']
        content_md = cu['content']
        if content_type == 'heading':
            # Headings are already formatted in Markdown
            markdown_content += f"{content_md}\n\n"
        elif content_type == 'paragraph':
            # Determine if this is the current paragraph to highlight
            if cu == content_units[curr_para_pos]:
                # Highlight the paragraph
                # Split into sentences
                sentences = content_md.strip().split('. ')
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"background-color: {color_variable}; padding: 2px 5px; border-radius: 5px; color: var(--text-color);"
                    if sentence.strip():
                        # Ensure proper punctuation at the end
                        if not sentence.endswith('.'):
                            sentence += '.'
                        sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                        highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                markdown_content += f"{paragraph_content}\n\n"
            else:
                # Regular paragraph
                markdown_content += f"{content_md}\n\n"
        elif content_type == 'list':
            markdown_content += f"{content_md}\n\n"
        else:
            # Other content types
            markdown_content += f"{content_md}\n\n"

    # Display the content using Streamlit
    st.markdown(markdown_content, unsafe_allow_html=True)

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

    /* Style for the highlighted text */
    p {
        font-family: Georgia, serif;
        font-size: 20px;
        line-height: 1.6;
    }

    /* Hide the Streamlit style elements (hamburger menu, header, footer) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive font sizes for mobile devices */
    @media only screen and (max-width: 600px) {
        p {
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
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')

            # Use the get_markdown_content function to get content units
            content_units = get_markdown_content(soup)

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
