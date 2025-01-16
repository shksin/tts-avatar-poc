using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ttsavatarfuncapp.Services
{
    public class AzureOpenAIService
    {
        private readonly HttpClient _httpClient;
        private readonly string _endpoint;
        private readonly string _apiKey;
        private readonly string _deployment;

        public AzureOpenAIService(HttpClient httpClient, string endpoint, string apiKey, string deployment)
        {
            _httpClient = httpClient;
            _endpoint = endpoint;
            _apiKey = apiKey;
            _deployment = deployment;
        }

        public async Task<string> GenerateEmbeddingsAsync(string input)
        {
            var requestBody = new
            {
                input = input
            };

            var requestContent = new StringContent(JsonSerializer.Serialize(requestBody), Encoding.UTF8, "application/json");
            _httpClient.DefaultRequestHeaders.Add("api-key", _apiKey);

            var response = await _httpClient.PostAsync($"{_endpoint}/openai/deployments/{_deployment}/embeddings?api-version=2023-09-01-preview", requestContent);
            response.EnsureSuccessStatusCode();

            var responseBody = await response.Content.ReadAsStringAsync();
            var jsonResponse = JsonDocument.Parse(responseBody);
            return jsonResponse.RootElement.GetProperty("data")[0].GetProperty("embedding").ToString();
        }

        public async Task<string> ProcessChatCompletionAsync(string messages)
        {
            var requestBody = new
            {
                messages = messages,
                temperature = 0.7,
                max_tokens = 1000,
                stream = true
            };

            var requestContent = new StringContent(JsonSerializer.Serialize(requestBody), Encoding.UTF8, "application/json");
            _httpClient.DefaultRequestHeaders.Add("api-key", _apiKey);

            var response = await _httpClient.PostAsync($"{_endpoint}/openai/deployments/{_deployment}/chat/completions?api-version=2023-09-01-preview", requestContent);
            response.EnsureSuccessStatusCode();

            return await response.Content.ReadAsStringAsync();
        }
    }
}
