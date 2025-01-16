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
blob_sas_url = os.getenv("BLOB_SAS_URL")
place_orders = False

sql_db_server = os.getenv("SQL_DB_SERVER")
sql_db_user = os.getenv("SQL_DB_USER")
sql_db_password = os.getenv("SQL_DB_PASSWORD")
sql_db_name = os.getenv("SQL_DB_NAME")
server_connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{sql_db_server},1433;Uid={sql_db_user};Pwd={sql_db_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
database_connection_string = server_connection_string + f"Database={sql_db_name};"

# Azure Open AI
deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
embeddings_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")

temperature = 0.7

tools = [     
    
    {
        "type": "function",
        "function": {
            "name": "bing_web_search",
            "description": "Search the web for questions about recent events, news or web pages related to AGL Electrify Now. Use only if the requested information is not already available in the conversation context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "User question optimized for a web search engine (examples: How to electrify with Electrify Now? Why buy an electric car?, etc.)"
                    },
                },
                "required": ["search_term"],
            }
        }
    }
]


client = openai.AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2023-09-01-preview"
)


def remove_html_tags(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text()

def bing_web_search(search_term):
    """Searches for news and webpages using the Bing Search API and returns matches in a string. Uses sinippets from search engine only. No scraping of web sites."""
    logging.info(f'Searching for: {search_term}')

    # bing search request
    headers = {"Ocp-Apim-Subscription-Key": bing_key}
    params = {"q": search_term, "textDecorations": True, "textFormat": "HTML", "count" : 5,}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()

    # consolidate news and webpage hits into string
    results_str = f"Here are the web search search results for the user query: {search_term}\nThe search engine returned news and links to websites."

    # Parsing news
    if 'news' in search_results:
        results_str += "\n*** News: ***"
        news = search_results['news']['value']

        for index, result in enumerate(news):
            news_str = f"""
        News {index + 1}/{len(news)}:
        Title: {remove_html_tags(result.get('name', 'No title available'))}
        Description: {remove_html_tags(result.get('description', 'No snippet available'))}
        Provider: {result['provider'][0].get('name', 'No provider name available')}
        URL: {result.get('url', 'No URL available')}
        """
            results_str += news_str

    # Parsing webpage hits
    results_str += "\n*** Web pages:***"
    webpages = search_results['webPages']['value']

    for index, result in enumerate(webpages):
        news_str = f"""
    Webpage {index + 1}/{len(webpages)}:
    Title: {result.get('name', 'No title available')}
    Snippet: {remove_html_tags(result.get('snippet', 'No snippet available'))}
    Site name: {result.get('siteName', 'No site name available')}
    URL: {result.get('url', 'No URL available')}
    """
        results_str += news_str

    return results_str



# Get data from Azure Open AI
async def stream_processor(response, messages):

    func_call = {
                  "id": None,
                  "type": "function",
                  "function": {
                        "name": None,
                        "arguments": ""
                  }
                  }

    async for chunk in response:
        if len(chunk.choices) > 0:
            delta = chunk.choices[0].delta

            if delta.content is None:
                if delta.tool_calls:
                    tool_calls = delta.tool_calls
                    tool_call = tool_calls[0]
                    if tool_call.id != None:
                        func_call["id"] = tool_call.id
                    if tool_call.function.name != None:
                        func_call["function"]["name"] = tool_call.function.name
                    if tool_call.function.arguments != None:
                        func_call["function"]["arguments"] += tool_call.function.arguments
                        await asyncio.sleep(0.01)
                        try:
                            arguments = json.loads(func_call["function"]["arguments"])
                            print(f"Function generation requested, calling function", func_call)
                            messages.append({
                                "content": None,
                                "role": "assistant",
                                "tool_calls": [func_call]
                            })

                            available_functions = {
                                "bing_web_search": bing_web_search                                
                            }
                            function_to_call = available_functions[func_call["function"]["name"]] 

                            function_response = function_to_call(**arguments)

                            if function_to_call == get_product_information:
                                product_info = json.loads(function_response)
                                function_response = product_info['description']
                                products = [display_product_info(product_info)]
                                yield json.dumps(products[0])

                            messages.append({
                                "tool_call_id": func_call["id"],
                                "role": "tool",
                                "name": func_call["function"]["name"],
                                "content": function_response
                            })

                            final_response = await client.chat.completions.create(
                                model=deployment,
                                temperature=temperature,
                                max_tokens=1000,
                                messages=messages,
                                stream=True
                            )

                            async for chunk in final_response:
                                if len(chunk.choices) > 0:
                                    delta = chunk.choices[0].delta
                                    if delta.content:
                                        await asyncio.sleep(0.01)
                                        yield delta.content

                        except Exception as e:
                            print(e)

            if delta.content: # Get remaining generated response if applicable
                await asyncio.sleep(0.01)
                yield delta.content


# HTTP streaming Azure Function
@app.route(route="get-oai-response", methods=[func.HttpMethod.GET, func.HttpMethod.POST])
async def stream_openai_text(req: Request) -> StreamingResponse:

    body = await req.body()

    messages_obj = json.loads(body) if body else []
    messages = messages_obj['messages']

    azure_open_ai_response = await client.chat.completions.create(
        model=deployment,
        temperature=temperature,
        max_tokens=1000,
        messages=messages,
        tools=tools,
        stream=True,
        extra_body={  
        "data_sources": [  
            {  
                "type": "azure_search",  
                "parameters": {  
                    "endpoint": search_endpoint,  
                    "index_name": search_index_name,  
                    "authentication": {  
                        "type": "api_key",
                        "key": search_key 
                    }  
                }  
            }  
        ]  
     
    }

    )

    return StreamingResponse(stream_processor(azure_open_ai_response, messages), media_type="text/event-stream")

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
