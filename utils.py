import base64
from dotenv import load_dotenv
import io
import json
import os
import sys
from ultralyticsplus import YOLO


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def pil_to_base64_scheme(pil_img):
    output = io.BytesIO()
    pil_img.save(output, format='JPEG')
    hex_data = output.getvalue()
    return base64.b64encode(hex_data).decode("utf-8")


def set_table_detection_model():
    model = YOLO('foduucom/table-detection-and-extraction')
    model.overrides['conf'] = 0.75
    model.overrides['iou'] = 0.75
    model.overrides['agnostic_nms'] = False
    model.overrides['max_det'] = 5
    return model


def load_config(config_path="config.json"):
    with open(resource_path(config_path), "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def load_api_key() -> str:
    """Load OpenAI API key from the environment variables."""
    load_dotenv()
    return os.environ.get("OPENAI_API_KEY")
