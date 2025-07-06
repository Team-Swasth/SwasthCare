import os
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
import json
import re
import warnings
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalysisFeature # type: ignore
from azure.ai.inference import ChatCompletionsClient #type: ignore
from azure.ai.inference.models import SystemMessage, UserMessage #type: ignore
import time

warnings.filterwarnings("ignore", category=DeprecationWarning)
# warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
# Set up environment variables for security

def extract_raw_text(result):
    """
    Extracts only the text content from DI result, ignoring all metadata.
    Returns a single string with all text, separated by newlines.
    """

    # Use paragraphs if available (usually best for natural order)
    if hasattr(result, "paragraphs") and result.paragraphs:
        return "\n".join([para.content for para in result.paragraphs if para.content])
    # Fallback: Use lines if paragraphs are missing
    elif hasattr(result, "pages") and result.pages:
        lines = []
        for page in result.pages:
            if hasattr(page, "lines"):
                lines.extend([line.content for line in page.lines if line.content])
        return "\n".join(lines)
    else:
        return ""

def analyze_and_print_raw_text(file_path):
    """
    Runs DI on the image and prints only the raw extracted text.
    Logs timing for each step.
    """
    di_endpoint = settings.AZURE_DI_ENDPOINT
    di_api_key = settings.AZURE_DI_API_KEY

    if not di_endpoint or not di_api_key:
        raise ValueError("Please set AZURE_DI_ENDPOINT and AZURE_DI_API_KEY in your environment.")
    document_analysis_client = DocumentAnalysisClient(
        endpoint=di_endpoint, credential=AzureKeyCredential(di_api_key)
    )

    try:
        start_total = time.time()
        with open(file_path, "rb") as f:
            start_analyze = time.time()
            poller = document_analysis_client.begin_analyze_document(
                "prebuilt-document",
                document=f,
                features=[AnalysisFeature.BARCODES]
            )
            print(f"Time to send request: {time.time() - start_analyze:.2f} seconds")
            start_poll = time.time()
            result = poller.result()
            print(f"Time waiting for result: {time.time() - start_poll:.2f} seconds")
    except Exception as e:
        print(f"Error processing document: {e}")
        return

    # Extract and print only the text
    start_extract = time.time()
    raw_text = extract_raw_text(result)
    print(f"Time to extract raw text: {time.time() - start_extract:.2f} seconds")
    print(f"Total time for analyze_and_print_raw_text: {time.time() - start_total:.2f} seconds")
    return raw_text

def extract_structured_data_from_label(raw_text):
    def extract_json_from_codeblock(text):
        """
        Extracts JSON from a markdown code block in the model output.
        """
        # Remove code block markers if present
        match = re.search(r"``````", text, re.IGNORECASE)
        if match:
            return match.group(1)
        # Fallback: try to find the first {...} block
        match = re.search(r"(\{[\s\S]*\})", text)
        if match:
            return match.group(1)
        raise ValueError("No JSON object found in the text.")

    ai_endpoint = settings.AZURE_AI_ENDPOINT
    model_name = "gpt-4.1-mini"
    ai_api_key = settings.AZURE_AI_API_KEY

    client = ChatCompletionsClient(
        endpoint=ai_endpoint,
        credential=AzureKeyCredential(ai_api_key),
        # api_version is not required for gpt-4.1-mini, remove if not needed
    )

    prompt = f"""
    Extract the following fields from the product label text. 
    Return only a JSON object with these exact keys and formats. 
    If a field is missing, set its value to null.

    {{
    "prod_name": "(string) Product name",
    "prod_type": "(string) Product type/category",
    "Ingredients (Camel Cased)": "(string) Full ingredients list",
    "nutritional_info": {{
        "energy_kcal": "(float or 0)",
        "protein_g": "(float or 0)",
        "total_fat_g": "(float or 0)",
        "saturated_fat_g": "(float or 0)",
        "trans_fat_g": "(float or 0)",
        "cholesterol_mg": "(float or 0)",
        "carbohydrate_g": "(float or 0)",
        "sugars_g": "(float or 0)",
        "fiber_g": "(float or 0)",
        "sodium_mg": "(float or 0)",
        "calcium_mg": "(float or 0)",
        "iron_mg": "(float or 0)",
        "potassium_mg": "(float or 0)",
        "vitamin_c_mg": "(float or 0)",
        "vitamin_d_mcg": "(float or 0)"
    }},
    "allergen_info (camel case)": "(string or null)",
    "barcode": "(string, digits only, no spaces or symbols)",
    "manufacturing_date (DD-MM-YYYY)": "(DD-MM-YYYY or null)",
    "expiry": {{
        "tenure (in months, calculate from manufacturing and expiry_date)": "(number or null)",
        "expiry_date (DD-MM-YYYY)": "(DD-MM-YYYY or null)"
    }},
    "price(should be for the whole product, not per gram or any other unit) in Rupees": "(float or null)"
    }}

    Product label text:
    \"\"\"
    {raw_text}
    \"\"\"
    """

    start_total = time.time()
    start_phi = time.time()
    response = client.complete(
        messages=[
            SystemMessage(content="You are a helpful assistant that extracts structured data from food product labels."),
            UserMessage(content=prompt),
        ],
        max_tokens=2048,
        temperature=0.0,
        top_p=0.1,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        model=model_name
    )
    print(f"Time for GPT-4.1-mini completion: {time.time() - start_phi:.2f} seconds")

    content = response.choices[0].message.content
    start_parse = time.time()
    try:
        json_str = extract_json_from_codeblock(content)
        structured_data = json.loads(json_str)
    except Exception as e:
        print("Error parsing JSON:", e)
        print("RAW RESPONSE:\n", content)
        structured_data = {"error": str(e), "raw_response": content}
    print(f"Time to parse model response: {time.time() - start_parse:.2f} seconds")
    print(f"Total time for extract_structured_data_from_label: {time.time() - start_total:.2f} seconds")

    # Print each variable
    if "error" not in structured_data:
        print("Product Name:", structured_data.get("prod_name"))
        print("Product Type:", structured_data.get("prod_type"))
        print("Ingredients:", structured_data.get("Ingredients"))

        print("\nNutritional Information:")
        nutritional_info = structured_data.get("nutritional_info", {})
        for key, value in nutritional_info.items():
            print(f"  {key}: {value}")

        print("\nAllergen Info:", structured_data.get("allergen_info"))
        print("Barcode:", structured_data.get("barcode"))
        print("Manufacturing Date:", structured_data.get("manufacturing_date"))

        expiry = structured_data.get("expiry", {})
        print("Expiry Tenure:", expiry.get("tenure"))
        print("Expiry Date:", expiry.get("expiry_date"))
    else:
        print(json.dumps(structured_data, indent=2))

    return structured_data
