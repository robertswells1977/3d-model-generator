using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Security.Claims;
using System.Threading.Tasks;
using ThreeDGenerator.Api.Models;
using ThreeDGenerator.Api.Repositories;

using Microsoft.AspNetCore.SignalR;
using ThreeDGenerator.Api.Hubs;

namespace ThreeDGenerator.Api.Controllers
{
    [Authorize]
    [Route("api/[controller]")]
    [ApiController]
    public class ProjectsController : ControllerBase
    {
        private readonly ProjectRepository _repository;
        private readonly IHubContext<ProjectHub> _hubContext;

        public ProjectsController(ProjectRepository repository, IHubContext<ProjectHub> hubContext)
        {
            _repository = repository;
            _hubContext = hubContext;
        }

        private Guid GetUserId()
        {
            return Guid.Parse(User.FindFirstValue(ClaimTypes.NameIdentifier)!);
        }

        public class CreateProjectRequest
        {
            public string Name { get; set; } = string.Empty;
            public string Description { get; set; } = string.Empty;
        }

        [HttpPost]
        public async Task<IActionResult> CreateProject([FromBody] CreateProjectRequest request)
        {
            // In Phase 4, the LLM will generate the plan synchronously or asynchronously.
            // For now, we stub it out.
            var project = new Project
            {
                Id = Guid.NewGuid(),
                UserId = GetUserId(),
                Name = request.Name,
                Description = request.Description,
                LLMPlan = "Pending LLM Generation...",
                Status = "planning",
                CreatedAt = DateTime.UtcNow
            };

            await _repository.CreateProjectAsync(project);
            return Ok(project);
        }

        [HttpGet]
        public async Task<IActionResult> GetProjects()
        {
            var projects = await _repository.GetProjectsByUserIdAsync(GetUserId());
            return Ok(projects);
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> GetProject(Guid id)
        {
            var project = await _repository.GetProjectByIdAsync(id, GetUserId());
            if (project == null) return NotFound();
            return Ok(project);
        }

        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteProject(Guid id)
        {
            var project = await _repository.GetProjectByIdAsync(id, GetUserId());
            if (project == null) return NotFound();
            
            await _repository.DeleteProjectAsync(id, GetUserId());
            return NoContent();
        }

        [HttpDelete("{id}/versions/{versionId}")]
        public async Task<IActionResult> DeleteVersion(Guid id, Guid versionId)
        {
            await _repository.DeleteVersionAsync(versionId, id);
            return NoContent();
        }

        public class UpdateStatusRequest
        {
            public string Status { get; set; } = string.Empty;
        }

        [HttpPatch("{id}/versions/{versionId}/status")]
        public async Task<IActionResult> UpdateVersionStatus(Guid id, Guid versionId, [FromBody] UpdateStatusRequest request)
        {
            await _repository.UpdateVersionStatusAsync(versionId, id, request.Status);
            return NoContent();
        }
        
        [HttpPost("{id}/generate")]
        public async Task<IActionResult> GenerateProject(Guid id)
        {
            var project = await _repository.GetProjectByIdAsync(id, GetUserId());
            if (project == null) return NotFound();

            // Set status to generating, Python worker will pick it up
            await _repository.UpdateProjectStatusAsync(id, "generating");
            return Ok(new { message = "Generation started" });
        }

        public class UpdatePlanRequest
        {
            public string LLMPlan { get; set; } = string.Empty;
        }

        [HttpPut("{id}/plan")]
        public async Task<IActionResult> UpdateProjectPlan(Guid id, [FromBody] UpdatePlanRequest request)
        {
            var project = await _repository.GetProjectByIdAsync(id, GetUserId());
            if (project == null) return NotFound();

            await _repository.UpdateProjectPlanAsync(id, request.LLMPlan);
            // Optionally, the frontend might trigger generation immediately after, 
            // or they can just save it. We return OK.
            return Ok();
        }

        public class LogRequest
        {
            public string Message { get; set; } = string.Empty;
        }

        [AllowAnonymous] // Allow worker to hit it without JWT
        [HttpPost("{id}/log")]
        public async Task<IActionResult> AddLog(Guid id, [FromBody] LogRequest request)
        {
            await _hubContext.Clients.Group(id.ToString()).SendAsync("ReceiveLog", request.Message);
            return Ok();
        }
    }
}
