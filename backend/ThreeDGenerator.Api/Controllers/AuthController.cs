using Microsoft.AspNetCore.Mvc;
using Google.Apis.Auth;
using Microsoft.Extensions.Configuration;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Security.Claims;
using System.IdentityModel.Tokens.Jwt;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using System;
using System.Data;
using Npgsql;
using Dapper;

namespace ThreeDGenerator.Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class AuthController : ControllerBase
    {
        private readonly IConfiguration _config;
        
        public AuthController(IConfiguration config)
        {
            _config = config;
        }

        public class GoogleLoginRequest
        {
            public string IdToken { get; set; } = string.Empty;
        }

        [HttpPost("google-login")]
        public async Task<IActionResult> GoogleLogin([FromBody] GoogleLoginRequest request)
        {
            try
            {
                var settings = new GoogleJsonWebSignature.ValidationSettings()
                {
                    Audience = new List<string>() { _config["Authentication:Google:ClientId"]! }
                };

                // Validate the token sent by the React frontend
                var payload = await GoogleJsonWebSignature.ValidateAsync(request.IdToken, settings);
                
                // Get or create user in the database
                var userId = await GetOrCreateUserAsync(payload);

                // Generate our own JWT for API authentication
                var token = GenerateJwtToken(payload, userId);
                return Ok(new { token, user = new { id = userId, name = payload.Name, email = payload.Email } });
            }
            catch (InvalidJwtException)
            {
                return Unauthorized("Invalid Google token.");
            }
        }

        private async Task<Guid> GetOrCreateUserAsync(GoogleJsonWebSignature.Payload payload)
        {
            var connectionString = _config.GetConnectionString("DefaultConnection");
            using var connection = new NpgsqlConnection(connectionString);
            
            var user = await connection.QuerySingleOrDefaultAsync<Guid?>(
                "SELECT Id FROM Users WHERE GoogleId = @GoogleId",
                new { GoogleId = payload.Subject });

            if (user != null) return user.Value;

            var newUserId = Guid.NewGuid();
            await connection.ExecuteAsync(
                "INSERT INTO Users (Id, GoogleId, Email, Name) VALUES (@Id, @GoogleId, @Email, @Name)",
                new { Id = newUserId, GoogleId = payload.Subject, Email = payload.Email, Name = payload.Name });
            
            return newUserId;
        }

        private string GenerateJwtToken(GoogleJsonWebSignature.Payload payload, Guid userId)
        {
            var jwtSettings = _config.GetSection("Jwt");
            var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSettings["Key"]!));
            var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

            var claims = new[]
            {
                new Claim(JwtRegisteredClaimNames.Sub, userId.ToString()),
                new Claim(JwtRegisteredClaimNames.Email, payload.Email),
                new Claim("name", payload.Name)
            };

            var token = new JwtSecurityToken(
                issuer: jwtSettings["Issuer"],
                audience: jwtSettings["Audience"],
                claims: claims,
                expires: DateTime.UtcNow.AddDays(7),
                signingCredentials: creds
            );

            return new JwtSecurityTokenHandler().WriteToken(token);
        }
    }
}
