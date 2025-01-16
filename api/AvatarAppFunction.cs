using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace AvatarApp.Function
{
    public class AvatarAppFunction
    {
        private readonly ILogger<AvatarAppFunction> _logger;

        public AvatarAppFunction(ILogger<AvatarAppFunction> logger)
        {
            _logger = logger;
        }

        [Function("get-ice-server-token")]
        public IActionResult Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");
            return new OkObjectResult("Welcome to Azure Functions!");
        }

        
    }
}
