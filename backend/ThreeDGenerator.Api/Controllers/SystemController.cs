using Microsoft.AspNetCore.Mvc;
using System.Net.Http;
using System.Threading.Tasks;
using System;

namespace ThreeDGenerator.Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class SystemController : ControllerBase
    {
        private readonly HttpClient _httpClient;

        public SystemController(IHttpClientFactory httpClientFactory)
        {
            _httpClient = httpClientFactory.CreateClient();
        }

        [HttpGet("fusion-status")]
        public async Task<IActionResult> GetFusionStatus()
        {
            try
            {
                // Internal docker host address for the Fusion MCP Add-in (must be POST)
                var response = await _httpClient.PostAsync("http://host.docker.internal:5000/test_connection", new StringContent("{}", System.Text.Encoding.UTF8, "application/json"));
                if (response.IsSuccessStatusCode)
                {
                    return Ok(new { status = "online" });
                }
                return Ok(new { status = "offline", reason = "Bad status code" });
            }
            catch (Exception)
            {
                return Ok(new { status = "offline", reason = "Connection failed" });
            }
        }
    }
}
