using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace ttsavatarfuncapp
{
    public class Function1
    {
        private readonly ILogger<Function1> _logger;

        public Function1(ILogger<Function1> logger)
        {
            _logger = logger;
        }

        [Function("GetElectrifyNowInfo")]
        public IActionResult Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "electrifynow")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");
            return new OkObjectResult("Welcome to Azure Functions!");
        }

        [Function("BingWebSearch")]
        public static async Task<IActionResult> BingWebSearch(
            [HttpTrigger(AuthorizationLevel.Function, "post", Route = "bingsearch")] HttpRequest req,
            ILogger log)
        {
            log.LogInformation("Processing BingWebSearch request.");

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            var data = JsonConvert.DeserializeObject<RequestModel>(requestBody);

            var result = await _bingSearchService.PerformSearchAsync(data.SearchTerm);
            return new OkObjectResult(result);
        }
    }
}
