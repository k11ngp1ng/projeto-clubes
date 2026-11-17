namespace Clubes.App;

internal sealed class LoginPage : FormPage
{
    private readonly Entry email;
    private readonly Entry password;
    private readonly Entry server;
    private ClubeApi? api;

    public LoginPage() : base("Projeto Clubes")
    {
        Heading("Área do sócio");
        email = Field("E-mail", new Entry { Keyboard = Keyboard.Email });
        password = Field("Senha", new Entry { IsPassword = true });
        ActionButton("Entrar", Enter);
        ActionButton("Solicitar associação", SignUp);
        Divider();
        string local = DeviceInfo.Platform == DevicePlatform.Android ? "10.0.2.2" : "127.0.0.1";
        server = Field("Endereço do servidor", new Entry
        {
            Keyboard = Keyboard.Url, Text = Preferences.Default.Get("server", $"http://{local}:8000")
        });
    }

    private async Task<Start> Connect()
    {
        api?.Dispose();
        var address = server.Text?.Trim() ?? "";
        api = new ClubeApi(address);
        var start = await api.StartAsync();
        Preferences.Default.Set("server", address);
        return start;
    }

    private async Task Enter()
    {
        await Connect();
        await api!.LoginAsync(email.Text ?? "", password.Text ?? "");
        var panel = await api.PanelAsync();
        Window!.Page = new NavigationPage(new MemberPage(api, panel))
        {
            BarBackgroundColor = Green, BarTextColor = Colors.White
        };
    }

    private async Task SignUp()
    {
        var start = await Connect();
        await Navigation.PushAsync(new SignupPage(api!, start));
    }
}
