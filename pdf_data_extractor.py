import base64
import io
from langchain_core.documents import Document
import pypdfium2 as pypdfium
from openai import OpenAI
from pypdfium2 import PdfImage, PdfDocument
from typing import List
from warnings import filterwarnings

from utils import load_api_key, load_config

filterwarnings('ignore')

client = OpenAI(api_key=load_api_key())
config = load_config("config.json")


def is_pdf_page_contains_image(pdf_document: PdfDocument, pdf_page_number: int) -> bool:
    """
        Check if a pdf page contains image.

        Args:
            pdf_document(PdfDocument): loaded pdf document
            pdf_page_number(int): pdf page number

        Returns:
            bool: True if a pdf page contains image; Else False.
    """
    pdf_page = pdf_document.get_page(pdf_page_number)
    page_objects = pdf_page.get_objects()
    for object_ in page_objects:
        if isinstance(object_, pypdfium.PdfImage):
            return True
    return False


def is_scanned_pdf_page(pdf_page) -> bool:
    """
        Check if a pdf page is scanned.

        Args:
            pdf_page: pypdfium Pdfdocument page

        Returns:
            bool: True if a pdf page is scanned; Else False.
    """
    if pdf_page.get_textpage().get_text_range():
        return False
    return True


def load_pdf(pdf_path: str) -> PdfDocument:
    """
        Load pdf document.

        Args:
            pdf_path(str): Path to pdf document

        Returns:
            PdfDocument: pypdfium pdf document
    """
    pdf_document = pypdfium.PdfDocument(pdf_path)
    return pdf_document


def convert_pypdfium_image_to_base64_scheme(image_object: PdfImage) -> base64:
    """
        Convert pypdfium image object to base64 scheme.

        Args:
            image_object(PdfImage): pypdfium image object

        Returns:
            base64: base64 scheme image
    """
    buffer = io.BytesIO()
    image_object.extract(buffer)
    buffer.seek(0)
    image_bytes = buffer.read()
    base64_scheme_image = base64.b64encode(image_bytes).decode('utf-8')
    return base64_scheme_image


def convert_pdf_to_base64_scheme(pdf_pages: PdfDocument) -> List[base64]:
    """
        Convert pdf to base64 scheme.

        Args:
            pdf_pages(list(pypdfium pdf document pages)): pypdfium pdf document page

        Returns:
            List(base64): list of pdf pages base64 scheme

    """
    base64_scheme_pdf = list()
    for page in pdf_pages:
        base64_pdf_page = convert_pdf_page_to_base64_scheme(page)
        base64_scheme_pdf.append(base64_pdf_page)
    return base64_scheme_pdf


def convert_pdf_page_to_base64_scheme(pdf_page) -> base64:
    """
        Converts pdf page to base64 scheme.

        Args:
            pdf_page: pypdfium Pdfdocument page

        Returns:
            base64: base64 scheme image
    """
    page_pixmap = pdf_page.render()
    page_image = page_pixmap.to_pil()
    buffer = io.BytesIO()
    page_image.save(buffer, format='PNG')
    buffer.seek(0)
    image_bytes = buffer.read()
    base64_scheme_page = base64.b64encode(image_bytes).decode('utf-8')
    return base64_scheme_page


def check_pdf_type(pdf_path: str) -> str:
    """
        Check pdf type

        Args:
            pdf_path(str): Path to pdf document

        Returns:
            str: pdf type: scanned_pdf_format | pure_pdf_format | combined_pdf_format
    """
    pdf_document = load_pdf(pdf_path)
    scanned_papers = list()
    for page in pdf_document:
        if page.get_textpage().get_text_range():
            scanned_papers.append(False)
        elif not page.get_textpage().get_text_range():
            scanned_papers.append(True)
    if all(scanned_papers):
        return 'scanned_pdf_format'
    elif not any(scanned_papers):
        return 'pure_pdf_format'
    else:
        return 'combined_pdf_format'


def extract_scanned_pdf_format_data(pdf_path: str) -> List[Document]:
    """
        Extract scanned pdf format data using llm.

        Args:
            pdf_path(str): Path to pdf document

        Returns:
            List[Document]: list of langchain format documents
        """
    pdf_document = load_pdf(pdf_path)
    documents = list()
    base64_scheme_pdf = convert_pdf_to_base64_scheme(pdf_document)
    for pdf_page_number, pdf_page in enumerate(base64_scheme_pdf):
        metadata = {
            'source': ' ',
            'page': pdf_page_number + 1
        }
        pdf_page_data = extract_image_data(pdf_page)
        document = Document(page_content=pdf_page_data, metadata=metadata)
        documents.append(document)
    return documents


def extract_pure_pdf_format_data(pdf_path: str) -> List[Document]:
    """
        Extract pure pdf format data using pypdfium and (if contains image) llm.

        Args:
            pdf_path(str): Path to pdf document

        Returns:
            List[Document]: list of langchain format documents
    """
    pdf_document = load_pdf(pdf_path)
    documents = list()
    for pdf_page_number in range(len(pdf_document)):
        print('-' * 40)
        pdf_page = pdf_document.get_page(pdf_page_number)
        pdf_page_data = pdf_page.get_textpage().get_text_range() + '\n'
        metadata = {
            'source': ' ',
            'page': pdf_page_number + 1
        }
        if not is_pdf_page_contains_image(pdf_document, pdf_page_number):
            pass
        else:
            page_images_data = str()
            page_objects = pdf_page.get_objects()
            print(f'page {pdf_page_number + 1}/{len(pdf_document)} of pdf document contains image.')
            for object_ in page_objects:
                if isinstance(object_, pypdfium.PdfImage):
                    base64_scheme_image = convert_pypdfium_image_to_base64_scheme(object_)
                    image_data = extract_image_data(base64_scheme_image)
                    if image_data == 'no_data':
                        print(f'page {pdf_page_number + 1}/{len(pdf_document)} image object contains no data.')
                        pass
                    else:
                        print(f'page {pdf_page_number + 1}/{len(pdf_document)} image object contains data.')
                        page_images_data += image_data + '\n'
            pdf_page_data += page_images_data
        document = Document(page_content=pdf_page_data, metadata=metadata)
        documents.append(document)
    return documents


def extract_combined_pdf_format_data(pdf_path: str):
    """
        Extract combined pdf format data using pypdfium and llm.

        Args:
            pdf_path(str): Path to pdf document

        Returns:
            List[Document]: list of langchain format documents
        """
    documents = list()
    pdf_document = load_pdf(pdf_path)
    for pdf_page_number, page in enumerate(pdf_document):
        print('-' * 40)
        pdf_page = pdf_document.get_page(pdf_page_number)
        metadata = {
            'source': ' ',
            'page': pdf_page_number + 1
        }
        if is_scanned_pdf_page(pdf_page):
            print(f'page {pdf_page_number + 1}/{len(pdf_document)} is scanned.')
            base64_pdf_page = convert_pdf_page_to_base64_scheme(pdf_page)
            pdf_page_data = extract_image_data(base64_pdf_page)
        else:
            print(f'page {pdf_page_number + 1}/{len(pdf_document)} is pure.')
            pdf_page_data = pdf_page.get_textpage().get_text_range() + '\n'
            if not is_pdf_page_contains_image(pdf_document, pdf_page_number):
                pass
            else:
                print(f'page {pdf_page_number + 1}/{len(pdf_document)} of pdf document contains image.')
                page_image_data = str()
                page_objects = pdf_page.get_objects()
                for object_ in page_objects:
                    if isinstance(object_, pypdfium.PdfImage):
                        base64_scheme_image = convert_pypdfium_image_to_base64_scheme(object_)
                        image_data = extract_image_data(base64_scheme_image)
                        page_image_data += image_data + '\n'
                pdf_page_data += page_image_data
        document = Document(page_content=pdf_page_data, metadata=metadata)
        documents.append(document)
    return documents


def extract_pdf_data(pdf_path: str) -> List[Document]:
    """
        Extract pdf document based on its type.

        Args:
            pdf_path(str): Path to pdf document

        Returns:
            List[Document]: list of langchain format documents
    """
    documents = list()
    try:
        pdf_type = check_pdf_type(pdf_path)
        print(pdf_type)
        if pdf_type == 'pure_pdf_format':
            documents = extract_pure_pdf_format_data(pdf_path)
        elif pdf_type == 'scanned_pdf_format':
            documents = extract_scanned_pdf_format_data(pdf_path)
        elif pdf_type == 'combined_pdf_format':
            documents = extract_combined_pdf_format_data(pdf_path)
        else:
            print('Undefined pdf format.')
    except FileNotFoundError:
        print('pdf file does not exist.')
    except Exception as e:
        print(f"An error occurred: {e}")
    return documents


def extract_image_data(encoded_image: base64) -> str:
    """
         Extract data from an image.

         Args:
             encoded_image(base64): base64 encoded format of an image

         Returns:
             response(str): extracted data from image by llm
    """
    response = client.chat.completions.create(
        model=config['ai_model'],
        messages=
        [
            {'role': 'system',
             'content': 'You are a helpful assistant which can understand images. \
                                 Help me analyse data inside tables and math expressions in a given image.'
             },
            {'role': 'user', 'content':
                [
                    {'type': 'text',
                     'text': config['image_instruction']
                     },
                    {'type': 'image_url', 'image_url':
                        {
                            'url': f'data:image/png;base64,{encoded_image}'
                        }
                     }
                ]
             }
        ],
        temperature=0.0,
    )
    response = response.choices[0].message.content
    return response


if __name__ == '__main__':
    path = 'documents/golrang_system/100.pdf'
    print(extract_pdf_data(path))
