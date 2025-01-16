using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using System.Net.Http;

namespace AvatarApp.Function
{
    public class GetSpeechTokenFunction
    {
        private readonly ILogger<GetSpeechTokenFunction> _logger;
        private static readonly HttpClient httpClient = new HttpClient();
        private static readonly string subscriptionKey = Environment.GetEnvironmentVariable("AZURE_SPEECH_API_KEY"); // Replace with your subscription key
        private static readonly string region = Environment.GetEnvironmentVariable("AZURE_SPEECH_REGION"); // Replace with your region

        public GetSpeechTokenFunction(ILogger<GetSpeechTokenFunction> logger)
        {
            _logger = logger;
        }

        [Function("get-speech-token")]
        public async Task<IActionResult> Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");

            // Define token endpoint
            string tokenEndpoint = $"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken";

            // Make HTTP request with subscription key as header
            var requestMessage = new HttpRequestMessage(HttpMethod.Post, tokenEndpoint);
            requestMessage.Headers.Add("Ocp-Apim-Subscription-Key", subscriptionKey);

            HttpResponseMessage response = await httpClient.SendAsync(requestMessage);

            if (response.IsSuccessStatusCode)
            {
                string token = await response.Content.ReadAsStringAsync();
                return new ContentResult
                {
                    Content = $"{{\"token\": \"{token}\"}}",
                    ContentType = "application/json",
                    StatusCode = (int)response.StatusCode
                };
            }
            else
            {
                return new StatusCodeResult((int)response.StatusCode);
            }
        }
    }
}
