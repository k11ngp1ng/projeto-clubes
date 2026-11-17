using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Clubes.App;

internal sealed record Club(int Id, string Name, string City)
{
    public override string ToString() => $"{Name} · {City}";
}
internal sealed record Start(string Csrf, Club[] Clubs, string[] States);
internal sealed record SessionKey(string Csrf);
internal sealed record Notice(string Message);
internal sealed record Due(string Period, int Amount, string? Paid);
internal sealed record Booking(string Purpose, DateTime Starts, DateTime Ends, string Status);
internal sealed record Ticket(string Kind, string Body, string? Reply, DateOnly Created);
internal sealed record Panel(string Name, string Club, string Category, string Status, bool Vote,
    Due[] Dues, Booking[] Bookings, Ticket[] Tickets);

[JsonSourceGenerationOptions(PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase)]
[JsonSerializable(typeof(Start))]
[JsonSerializable(typeof(SessionKey))]
[JsonSerializable(typeof(Panel))]
[JsonSerializable(typeof(Notice))]
[JsonSerializable(typeof(Dictionary<string, string>))]
internal partial class ApiJson : JsonSerializerContext { }

internal sealed class ClubeApi : IDisposable
{
    private readonly HttpClient client;
    private string csrf = "";

    public ClubeApi(string address)
    {
        if (!Uri.TryCreate(address.Trim(), UriKind.Absolute, out var uri) ||
            (uri.Scheme != "http" && uri.Scheme != "https") || uri.UserInfo.Length > 0)
            throw new InvalidOperationException("Informe o endereço do servidor com http:// ou https://.");

        client = new HttpClient(new HttpClientHandler { CookieContainer = new CookieContainer(), AllowAutoRedirect = false })
        {
            BaseAddress = new Uri(uri, "/api/"),
            Timeout = TimeSpan.FromSeconds(12)
        };
    }

    private async Task<T> Send<T>(string path, JsonTypeInfo<T> type, Dictionary<string, string>? fields = null)
    {
        using var request = new HttpRequestMessage(fields is null ? HttpMethod.Get : HttpMethod.Post, path);
        if (fields is not null)
        {
            request.Headers.Add("X-CSRF-Token", csrf);
            request.Content = JsonContent.Create(fields, ApiJson.Default.DictionaryStringString);
        }
        using var response = await client.SendAsync(request);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadFromJsonAsync(ApiJson.Default.Notice);
            throw new InvalidOperationException(error?.Message ?? "O servidor recusou o pedido.");
        }
        return await response.Content.ReadFromJsonAsync(type)
            ?? throw new JsonException("Resposta vazia.");
    }

    public async Task<Start> StartAsync()
    {
        var start = await Send("inicio", ApiJson.Default.Start);
        csrf = start.Csrf;
        return start;
    }

    public async Task LoginAsync(string email, string password)
    {
        var result = await Send("entrar", ApiJson.Default.SessionKey,
            new() { ["email"] = email, ["password"] = password });
        csrf = result.Csrf;
    }

    public Task<Panel> PanelAsync() => Send("painel", ApiJson.Default.Panel);

    public Task<Notice> SubmitAsync(string path, Dictionary<string, string> fields) =>
        Send(path, ApiJson.Default.Notice, fields);

    public void Dispose() => client.Dispose();
}
