import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os

def parse_chapter_content(soup):
    """
    Parses the HTML content of a chapter and returns a list of blocks.
    Each block is a dictionary with type ('heading', 'paragraph', 'image', etc.) and content.
    Headings are placed above their first paragraph and below the preceding paragraph.
    """
    blocks = []

    # Get all elements directly under the body tag
    body = soup.find('body')
    if not body:
        return blocks  # Return empty list if no body

    elements = body.find_all(recursive=False)

    for elem in elements:
        # Handle headings
        if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            heading_text = elem.get_text(strip=True)
            if heading_text:
                blocks.append({'type': 'heading', 'content': heading_text})
        # Handle paragraphs
        elif elem.name == 'p':
            p_classes = elem.get('class', [])
            if 'para' in p_classes or 'chapterOpenerText' in p_classes or 'paraNoIndent' in p_classes:
                paragraph_text = elem.get_text(separator=' ', strip=True)
                if paragraph_text:
                    blocks.append({'type': 'paragraph', 'content': paragraph_text})
            elif 'caption' in p_classes or 'centerImage' in p_classes:
                caption_text = elem.get_text(separator=' ', strip=True)
                if caption_text:
                    blocks.append({'type': 'caption', 'content': caption_text})
            else:
                # Other paragraphs
                paragraph_text = elem.get_text(separator=' ', strip=True)
                if paragraph_text:
                    blocks.append({'type': 'paragraph', 'content': paragraph_text})
        # Handle images
        elif elem.name == 'img':
            img_src = elem.get('src')
            if img_src:
                blocks.append({'type': 'image', 'src': img_src})
        # Handle lists
        elif elem.name in ['ul', 'ol']:
            list_items = [li.get_text(separator=' ', strip=True) for li in elem.find_all('li')]
            if list_items:
                blocks.append({'type': 'list', 'items': list_items})
        # Handle other elements by processing their children
        else:
            inner_blocks = parse_chapter_content(elem)
            blocks.extend(inner_blocks)
    return blocks

def display_blocks(block_index, blocks):
    """
    Displays three blocks at a time, highlighting the middle one if it's a paragraph.
    Other elements like headings, images, captions are displayed appropriately.
    """
    display_blocks_list = blocks[max(block_index-1, 0):block_index+2]
    html_content = ""

    for i, block in enumerate(display_blocks_list):
        # Base style
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

        is_highlighted = (block_index == 0 and i == 0) or (block_index != 0 and i == 1)

        if block['type'] == 'heading':
            heading_style = font_style + "font-weight: bold; font-size: 24px;"
            html_content += f"<h2 style='{heading_style}'>{block['content']}</h2>"
        elif block['type'] == 'paragraph':
            paragraph_text = block['content']
            if is_highlighted:
                sentences = paragraph_text.strip().split('. ')
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
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}{"." if not sentence.strip().endswith(".") else ""}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif block['type'] == 'caption':
            caption_style = font_style + "font-style: italic; color: gray;"
            html_content += f"<div style='{caption_style}'>{block['content']}</div>"
        elif block['type'] == 'image':
            img_src = block['src']
            image_html = f"<img src='{img_src}' style='max-width: 100%; height: auto;'>"
            html_content += f"<div style='{font_style}'>{image_html}</div>"
        elif block['type'] == 'list':
            list_html = '<ul>' + ''.join(f"<li>{item}</li>" for item in block['items']) + '</ul>'
            html_content += f"<div style='{font_style}'>{list_html}</div>"
        else:
            content = block.get('content', '')
            if content:
                html_content += f"<div style='{font_style}'>{content}</div>"

    st.write(html_content, unsafe_allow_html=True)

def main():
    st.markdown("""
    <style>
    :root {
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: rgba(251, 192, 45, 0.9);
    }
    @media (prefers-color-scheme: light) {
        :root {
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9);
        }
    }
    #MainMenu, header, footer {visibility: hidden;}
    @media only screen and (max-width: 600px) {
        div[style] {
            font-size: 5vw !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Reader")
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            book = epub.read_epub(tmp_file_path)
        except Exception as e:
            st.error(f"An error occurred while reading the EPUB file: {e}")
            return
        finally:
            os.remove(tmp_file_path)

        chapters = []
        chapter_titles = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            chapter_blocks = parse_chapter_content(soup)
            if not chapter_blocks:
                st.error("No content found in the selected chapter.")
                return

            if 'current_block' not in st.session_state:
                st.session_state.current_block = 0

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_block > 0:
                        st.session_state.current_block -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_block + 1 < len(chapter_blocks):
                        st.session_state.current_block += 1

            display_blocks(st.session_state.current_block, chapter_blocks)
        else:
            st.error("No readable content found in the EPUB file.")
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
