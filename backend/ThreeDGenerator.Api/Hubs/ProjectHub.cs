using Microsoft.AspNetCore.SignalR;
using System.Threading.Tasks;

namespace ThreeDGenerator.Api.Hubs
{
    public class ProjectHub : Hub
    {
        public async Task JoinProjectGroup(string projectId)
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, projectId);
        }

        public async Task LeaveProjectGroup(string projectId)
        {
            await Groups.RemoveFromGroupAsync(Context.ConnectionId, projectId);
        }
    }
}
