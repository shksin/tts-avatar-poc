import azure.functions as func
import openai
from azurefunctions.extensions.http.fastapi import Request, StreamingResponse, JSONResponse
import asyncio
import os
import logging
import pyodbc
import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Azure Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
api_key = os.environ["AZURE_OPENAI_API_KEY"]
subscription_key = os.getenv("AZURE_SPEECH_API_KEY")
region = os.getenv("AZURE_SPEECH_REGION")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_API_KEY") 
search_api_version = '2023-07-01-Preview'
search_index_name = os.getenv("AZURE_SEARCH_INDEX")
bing_key = os.getenv("BING_KEY")
search_url = os.getenv("BING_SEARCH_URL")

# Azure Open AI
deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
embeddings_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")

temperature = 0.7

# Initialize the Azure OpenAI client
openai_client = openai.AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2023-09-01-preview"
)

 # Initialize the Azure Search client
search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=search_index_name,
        credential=AzureKeyCredential(search_key)
    )

@app.route(route="get-oai-response", methods=[func.HttpMethod.GET, func.HttpMethod.POST])
async def stream_openai_text(req: Request) -> StreamingResponse:
    # Extract the input data from the request
    input_data = await req.json()
    search_query = input_data.get("query", "")

   
    # Perform the search query
    search_results = search_client.search(search_query)
    documents = [doc for doc in search_results]

    # Prepare the messages for the OpenAI API
    messages = [
        {"role": "system", "content": "You are an AI assistant."},
        {"role": "user", "content": search_query},
        {"role": "assistant", "content": str(documents)}
    ]

    # Call Azure OpenAI with chat and enable streaming
    azure_open_ai_response = await client.chat.completions.create(
        model=deployment,
        temperature=temperature,
        max_tokens=1000,
        messages=messages
        stream=True
    )


    # Stream the response back to the client
    async def response_generator():
        for chunk in azure_open_ai_response:
            yield chunk['choices'][0]['delta']['content']

    return StreamingResponse(response_generator(), media_type="text/event-stream")


@app.route(route="get-ice-server-token", methods=[func.HttpMethod.GET, func.HttpMethod.POST])
def get_ice_server_token(req: Request) -> JSONResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Define token endpoint
    token_endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1"

    # Make HTTP request with subscription key as header
    response = requests.get(token_endpoint, headers={"Ocp-Apim-Subscription-Key": subscription_key})

    if response.status_code == 200:
        return JSONResponse(
            content = response.json(),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    else:
        return func.HttpResponse(response.status_code)
    

@app.route(route="get-speech-token", methods=[func.HttpMethod.GET, func.HttpMethod.POST])
def get_speech_token(req: Request) -> JSONResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Define token endpoint
    token_endpoint = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"

    # Make HTTP request with subscription key as header
    response = requests.post(token_endpoint, headers={"Ocp-Apim-Subscription-Key": subscription_key})

    print(response)

    if response.status_code == 200:
        return JSONResponse(
            content = {"token": response.text},
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    else:
        return func.HttpResponse(response.status_code)