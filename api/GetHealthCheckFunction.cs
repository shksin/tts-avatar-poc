using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace api
{
    public class GetHealthCheckFunction
    {
        private readonly ILogger<GetHealthCheckFunction> _logger;

        public GetHealthCheckFunction(ILogger<GetHealthCheckFunction> logger)
        {
            _logger = logger;
        }

        [Function("health")]
        public IActionResult Run([HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");
            return new OkObjectResult("API is up and running!!");
        }
    }
}
