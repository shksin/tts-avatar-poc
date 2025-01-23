using Azure;
using Azure.AI.OpenAI;
using Azure.Search.Documents;
using Azure.Search.Documents.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json.Linq;
using Azure.Identity;
using OpenAI.Chat;
using OpenAI;
using System.ClientModel;
using Azure.AI.OpenAI.Chat;
using Newtonsoft.Json;
using api;

namespace AvatarApp.Function
{
    public class GetOpenAIResponse
    {
        private readonly ILogger<GetOpenAIResponse> _logger;
        private readonly AzureOpenAIClient _openAIClient;
        string? azureOpenAIEndpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT");
        string? azureOpenAIKey = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY");
        string? deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_CHAT_DEPLOYMENT");
        string? searchEndpoint = Environment.GetEnvironmentVariable("AZURE_SEARCH_ENDPOINT");
        string? searchKey = Environment.GetEnvironmentVariable("AZURE_SEARCH_API_KEY");
        string? searchIndex = Environment.GetEnvironmentVariable("AZURE_SEARCH_INDEX");

        public GetOpenAIResponse(ILogger<GetOpenAIResponse> logger)
        {
            _logger = logger;
            _openAIClient = new(new Uri(azureOpenAIEndpoint), new ApiKeyCredential(azureOpenAIKey));
        }

        [Function("get-oai-response")]
        public async Task<IActionResult> Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");

            try
            {
                //Extract the input data from the request
                string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
                _logger.LogInformation(requestBody);
                var rootObject = JsonConvert.DeserializeObject<Root>(requestBody);

               var chatMessages = new List<ChatMessage>();
               foreach (var message in rootObject.Messages)
               {
                    switch (message.Role)
                    {
                        case Role.System:
                            chatMessages.Add(new SystemChatMessage(message.Content));
                            break;
                        case Role.Assistant:
                            chatMessages.Add(new AssistantChatMessage(message.Content));
                            break;
                        case Role.User:
                            chatMessages.Add(new UserChatMessage(message.Content));
                            break;
                    }
                    }


                

                _logger.LogInformation($"Azure OpenAI Chat deploymentName used {deploymentName}");

                ChatClient chatClient = _openAIClient.GetChatClient(deploymentName);
                _logger.LogInformation("ChatClient initialized");

                // Extension methods to use data sources with options are subject to SDK surface changes. Suppress the
                // warning to acknowledge and this and use the subject-to-change AddDataSource method.
#pragma warning disable AOAI001

                ChatCompletionOptions options = new() { Temperature = (float?)0.7, MaxOutputTokenCount = 1000 };
                options.AddDataSource(new AzureSearchChatDataSource()
                {
                    Endpoint = new Uri(searchEndpoint),
                    IndexName = searchIndex,
                    Authentication = DataSourceAuthentication.FromApiKey(searchKey),
                });

                // call CompletChatStream method to get the response from Azure OpenAI

                CollectionResult<StreamingChatCompletionUpdate> completionUpdates = chatClient.CompleteChatStreaming(chatMessages);

                req.HttpContext.Response.Headers.Append("Content-Type", "text/event-stream");
                foreach (StreamingChatCompletionUpdate completionUpdate in completionUpdates)
                {
                    foreach (ChatMessageContentPart contentPart in completionUpdate.ContentUpdate)
                    {
                        _logger.LogInformation(contentPart.Text);
                        await req.HttpContext.Response.WriteAsync(contentPart.Text);
                        await req.HttpContext.Response.Body.FlushAsync();
                        //await Task.Delay(10); // Simulate delay
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while processing the request.");
                return new ContentResult
                {
                    Content = $"{{\"error\": \"{ex.Message + ex.StackTrace}\"}}",
                    ContentType = "application/json",
                    StatusCode = (int)200
                };
            }

            return new StatusCodeResult((int)200);
        }
    }
}
