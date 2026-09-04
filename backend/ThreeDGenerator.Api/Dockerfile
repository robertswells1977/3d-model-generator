FROM mcr.microsoft.com/dotnet/sdk:9.0
WORKDIR /app
COPY . .
RUN dotnet restore
EXPOSE 5045
ENV ASPNETCORE_URLS=http://+:5045
ENTRYPOINT ["dotnet", "run", "--no-launch-profile"]
