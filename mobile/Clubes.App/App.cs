namespace Clubes.App;

public class App : Application
{
    public App() => UserAppTheme = AppTheme.Light;

    internal static NavigationPage Login() => new(new LoginPage())
    {
        BarBackgroundColor = FormPage.Green,
        BarTextColor = Colors.White
    };

    protected override Window CreateWindow(IActivationState? activationState) =>
        new(Login()) { Title = "Projeto Clubes" };
}
