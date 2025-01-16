using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace AvatarApp.Function
{
    public class GetOpenAIResponse
    {
        private readonly ILogger<GetOpenAIResponse> _logger;

        public GetOpenAIResponse(ILogger<GetOpenAIResponse> logger)
        {
            _logger = logger;
        }

        [Function("get-oai-response")]
        public IActionResult Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");
            return new OkObjectResult("Welcome to Azure Functions!");
        }
    }
}
