import os
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
import json
import re
import warnings
from azure.ai.inference import ChatCompletionsClient #type: ignore
from azure.ai.inference.models import SystemMessage, UserMessage #type: ignore
import time


def chat_about_product(product_json, user_question):
    """
    Use Phi-4 to answer user questions about a packaged food product, given its details as a JSON dict.
    """
    ai_endpoint = settings.AZURE_AI_ENDPOINT
    model_name = "Phi-4"
    ai_api_key = settings.AZURE_AI_API_KEY

    client = ChatCompletionsClient(
        endpoint=ai_endpoint,
        credential=AzureKeyCredential(ai_api_key),
        api_version="2024-05-01-preview"
    )

    # Prepare the system prompt and user message
    system_prompt = (
        "You are a helpful assistant that answers questions about packaged food products. "
        "You are given the product details as a JSON object. "
        "Answer the user's question based only on the provided product data. "
        "If the answer is not present in the data, say 'Sorry, that information is not available.'"
    )
    product_json_str = json.dumps(product_json, indent=2)
    user_prompt = (
        f"Product details:\n```\n{product_json_str}\n```\n\n"
        f"User question: {user_question}"
    )

    start_total = time.time()
    response = client.complete(
        messages=[
            SystemMessage(content=system_prompt),
            UserMessage(content=user_prompt),
        ],
        max_tokens=512,
        temperature=0.2,
        top_p=0.9,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        model=model_name
    )
    print(f"Time for Phi completion: {time.time() - start_total:.2f} seconds")

    content = response.choices[0].message.content
    return content
