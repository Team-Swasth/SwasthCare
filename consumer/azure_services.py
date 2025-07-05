import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
import json
import re
import warnings
import time


def chat_about_product(product_json, user_question, stream=False):
    """
    Use GPT-4.1-mini to answer user questions about a packaged food product, given its details as a JSON dict.
    """
    ai_endpoint = settings.AZURE_AI_ENDPOINT
    model_name = "gpt-4.1-mini"
    ai_api_key = settings.AZURE_AI_API_KEY

    client = ChatCompletionsClient(
        endpoint=ai_endpoint,
        credential=AzureKeyCredential(ai_api_key),
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

    # Call GPT-4.1-mini via Azure AI Inference
    if stream:
        response = client.complete(
            stream=True,
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt),
            ],
            model=model_name,
            max_tokens=512,
            temperature=0.2,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        try:
            for update in response:
                if update.choices and update.choices[0].delta.content:
                    yield update.choices[0].delta.content
        finally:
            client.close()
    else:
        response = client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt),
            ],
            model=model_name,
            max_tokens=512,
            temperature=0.2,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        content = response.choices[0].message.content
        client.close()
        return content
