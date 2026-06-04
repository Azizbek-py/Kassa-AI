import io
import base64
import json
import requests
from datetime import datetime, timedelta
from huggingface_hub import InferenceClient
from groq import Groq
from settings import prompt as prompt_system
from settings import GROQ_TOKEN

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

def format_number(value) -> str:
    """
    Format number as: 42 916 000,00
    """
    if value == 0 or value is None:
        return "0,00"
    
    try:
        # Convert to float if string
        if isinstance(value, str):
            # Remove spaces and normalize decimal separator
            value_str = str(value).replace(" ", "").replace(".", ",")
            value = float(value_str.replace(",", "."))
        else:
            value = float(value)
        
        # Format with thousands separator and 2 decimals
        # Split into integer and decimal parts
        int_part = int(value)
        dec_part = round((value - int_part) * 100)
        
        # Format integer part with spaces
        int_formatted = f"{int_part:,}".replace(",", " ")
        
        return f"{int_formatted},{dec_part:02d}"
    except:
        return "0,00"


def format_date(date_str: str, is_estimated: bool = False) -> str:
    """
    Format date and add (tahminiy) if estimated.
    """
    if not date_str or date_str.strip() == "":
        # Use previous day as default
        date_str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        is_estimated = True
    
    suffix = " (tahminiy)" if is_estimated else ""
    return f"{date_str}{suffix}"

def describe_photo(filename: str, prompt: str, url: str) -> dict:
    """
    Analyzes a financial document image using Groq's vision API.
    
    Args:
        filename: Path to the image file
        prompt: Additional prompt text
        url: URL of the image for API
        
    Returns:
        Dictionary with parsed analysis results
    """
    with open(filename, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    client = Groq(api_key=GROQ_TOKEN)

    completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": prompt_system,
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                    },
                },
            ],
        }
    ],
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    )

    message = completion.choices[0].message

    resp = {
        "text": message.content,
        "model": completion.model,
        "usage": completion.usage,
        "raw": completion
    }
    
    clean_text = (
        resp["text"]
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    return json.loads(clean_text)


def format_cash_message(data: dict, group_name: str, sender_name: str, message_link: str) -> str:
    """
    Formats a cash register report for sending to analytics group.
    """
    # Check if date is provided, if not it's estimated
    is_date_estimated = not data.get("date", "").strip()
    
    date = format_date(data.get("date", ""), is_date_estimated)
    
    expected_cash = format_number(data.get("expected_cash", 0))
    cash = format_number(data.get("cash", 0))
    dollar = format_number(data.get("dollar", 0))
    coin = format_number(data.get("coin", 0))
    click = format_number(data.get("click", 0))
    terminal = format_number(data.get("terminal", 0))
    expense = format_number(data.get("expense", 0))
    
    message = f"""
-{group_name} - Kassa atchot 
-{sender_name}

Sana: {date}

Kassada bo'lishi kerak: {expected_cash}

Naqt pullar: {cash}
Terminal: {terminal}
Tangalar: {coin}
Klik: {click}
Rasxod: {expense}

Xabar linki: {message_link}"""
    
    return message


def format_sklad_message(data: dict, group_name: str, sender_name: str, message_link: str) -> str:
    """
    Formats a warehouse report for sending to analytics group.
    """
    is_date_estimated = not data.get("date", "").strip()
    date = format_date(data.get("date", ""), is_date_estimated)
    
    message = f"""
-{group_name} - Sklad atchot 
-{sender_name}

Sana: {date}

Xabar linki: {message_link}"""
    
    return message


def format_klik_message(data: dict, group_name: str, sender_name: str, message_link: str) -> str:
    """
    Formats a Click funds screenshot for sending to analytics group.
    """
    is_date_estimated = not data.get("date", "").strip()
    date = format_date(data.get("date", ""), is_date_estimated)
    
    time = data.get("time", "")
    click_amount = format_number(data.get("click_amount", 0))
    
    message = f"""
-{group_name} - Klik skrenshot
-{sender_name}

Sana: {date} - {time}

KLikdagi mablag': {click_amount}

Xabar linki: {message_link}"""
    
    return message


