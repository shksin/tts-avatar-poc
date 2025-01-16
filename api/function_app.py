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

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

subscription_key = os.getenv("AZURE_SPEECH_API_KEY")
region = os.getenv("AZURE_SPEECH_REGION")

@app.route(route="get-oai-response", methods=[func.HttpMethod.GET, func.HttpMethod.POST])
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )

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