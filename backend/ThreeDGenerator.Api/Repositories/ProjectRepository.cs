using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using Dapper;
using Npgsql;
using Microsoft.Extensions.Configuration;
using ThreeDGenerator.Api.Models;

namespace ThreeDGenerator.Api.Repositories
{
    public class ProjectRepository
    {
        private readonly string _connectionString;

        public ProjectRepository(IConfiguration config)
        {
            _connectionString = config.GetConnectionString("DefaultConnection")!;
        }

        public async Task<Guid> CreateProjectAsync(Project project)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            var sql = @"
                INSERT INTO Projects (Id, UserId, Name, Description, LLMPlan, Status, CreatedAt) 
                VALUES (@Id, @UserId, @Name, @Description, @LLMPlan, @Status, @CreatedAt)";
            
            await connection.ExecuteAsync(sql, project);
            return project.Id;
        }

        public async Task<IEnumerable<Project>> GetProjectsByUserIdAsync(Guid userId)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            var sql = "SELECT * FROM Projects WHERE UserId = @UserId ORDER BY CreatedAt DESC";
            return await connection.QueryAsync<Project>(sql, new { UserId = userId });
        }

        public async Task<Project?> GetProjectByIdAsync(Guid id, Guid userId)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            var sql = "SELECT * FROM Projects WHERE Id = @Id AND UserId = @UserId";
            var project = await connection.QuerySingleOrDefaultAsync<Project>(sql, new { Id = id, UserId = userId });
            
            if (project != null)
            {
                var versionsSql = "SELECT * FROM ProjectVersions WHERE ProjectId = @Id ORDER BY VersionNumber ASC";
                var versions = await connection.QueryAsync<ProjectVersion>(versionsSql, new { Id = id });
                project.Versions = versions.ToList();
            }

            return project;
        }

        public async Task DeleteProjectAsync(Guid id, Guid userId)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            // Must delete versions first due to FK constraint
            await connection.ExecuteAsync("DELETE FROM ProjectVersions WHERE ProjectId = @Id", new { Id = id });
            await connection.ExecuteAsync("DELETE FROM Projects WHERE Id = @Id AND UserId = @UserId", new { Id = id, UserId = userId });
        }

        public async Task DeleteVersionAsync(Guid versionId, Guid projectId)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.ExecuteAsync("DELETE FROM ProjectVersions WHERE Id = @Id AND ProjectId = @ProjectId", 
                new { Id = versionId, ProjectId = projectId });
        }

        public async Task UpdateVersionStatusAsync(Guid versionId, Guid projectId, string status)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.ExecuteAsync("UPDATE ProjectVersions SET Status = @Status WHERE Id = @Id AND ProjectId = @ProjectId", 
                new { Status = status, Id = versionId, ProjectId = projectId });
        }
        
        public async Task UpdateProjectStatusAsync(Guid projectId, string status)
        {
            using var connection = new NpgsqlConnection(_connectionString);
            await connection.ExecuteAsync("UPDATE Projects SET Status = @Status WHERE Id = @Id", 
                new { Status = status, Id = projectId });
        }
    }
}
