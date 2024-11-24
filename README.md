# image data extract

## Overview
Extracting data from images is matter. Imagine you have a llm-based chatbot which is using your documents to answer your questions. PDF documents can be pure, scanned or combined. Each of which may contains image.
This project is here to help. It Extracts data from images containing tables, math formula or expression an so on. Enjoy using it.

## Features
- Detecting pdf file format: typical pdf | scanned pdf | combined pdf (both typical and scanned papers).
- Finding pages contain image in a pdf document.
- Extracting data from any image if exists.
- Analyse math expression and formulas in image or text format using llm.

## Setup and Installation
- llm api key in .env file
- config file for choosing llm model (here pt-4o-2024-05-13 is being used.) and llm instruction.
- path to your pdf document

### Prerequisites
- Python 3.8+
- git

### Installation Steps

1. Clone the Repository

    ```bash
    git clone https://github.com/imsherko/image_data_extract.git
    cd your-repo
    ```
    ```bash
    python pdf_data_extractor.py
    ```

## Contact
For questions or comments, please open an issue or contact the repository owner at abdullahi.sherko11@gmail.com.
