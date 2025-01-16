using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ttsavatarfuncapp.Services
{
    public class BingSearchService
    {
        private readonly HttpClient _httpClient;
        private readonly string _bingApiKey;
        private readonly string _bingSearchUrl;

        public BingSearchService(HttpClient httpClient, string bingApiKey, string bingSearchUrl)
        {
            _httpClient = httpClient;
            _bingApiKey = bingApiKey;
            _bingSearchUrl = bingSearchUrl;
        }

        public async Task<string> SearchAsync(string searchTerm)
        {
            var request = new HttpRequestMessage(HttpMethod.Get, $"{_bingSearchUrl}?q={Uri.EscapeDataString(searchTerm)}&count=5");
            request.Headers.Add("Ocp-Apim-Subscription-Key", _bingApiKey);

            var response = await _httpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            var jsonResponse = await response.Content.ReadAsStringAsync();
            return FormatSearchResults(jsonResponse);
        }

        private string FormatSearchResults(string jsonResponse)
        {
            var searchResults = JsonDocument.Parse(jsonResponse);
            var resultsStr = $"Here are the web search results for the user query: {searchTerm}\nThe search engine returned news and links to websites.";

            if (searchResults.RootElement.TryGetProperty("webPages", out var webPages) && webPages.GetProperty("value").GetArrayLength() > 0)
            {
                resultsStr += "\n*** Web pages: ***";
                foreach (var page in webPages.GetProperty("value").EnumerateArray())
                {
                    resultsStr += $"\nTitle: {page.GetProperty("name").GetString()}\nSnippet: {page.GetProperty("snippet").GetString()}\nURL: {page.GetProperty("url").GetString()}\n";
                }
            }

            return resultsStr;
        }
    }
}
