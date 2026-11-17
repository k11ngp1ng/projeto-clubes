using System.Text.Json;

namespace Clubes.App;

internal class FormPage : ContentPage
{
    internal static readonly Color Green = Color.FromArgb("#155D49");
    protected readonly VerticalStackLayout Form = new() { Spacing = 12, Padding = 20, MaximumWidthRequest = 660 };
    private bool working;

    protected FormPage(string title)
    {
        Title = title;
        BackgroundColor = Colors.White;
        Content = new ScrollView { Content = Form };
    }

    protected void Heading(string text) => Form.Add(new Label
    {
        Text = text, TextColor = Green, FontAttributes = FontAttributes.Bold, FontSize = 22
    });

    protected void Line(string text) => Form.Add(new Label { Text = text, FontSize = 16, TextColor = Colors.Black });

    protected T Field<T>(string label, T input) where T : View
    {
        var group = new VerticalStackLayout { Spacing = 2 };
        group.Add(new Label { Text = label, FontSize = 14, TextColor = Colors.DarkSlateGray });
        if (input is Entry { IsPassword: true })
            SemanticProperties.SetHint(input, label);
        else
            SemanticProperties.SetDescription(input, label);
        group.Add(input);
        Form.Add(group);
        return input;
    }

    protected Picker Choices(string label, IList<string> options, int selected = 0) =>
        Field(label, new Picker { ItemsSource = options.ToList(), SelectedIndex = selected });

    protected void ActionButton(string label, Func<Task> action)
    {
        var button = new Button { Text = label, BackgroundColor = Green, TextColor = Colors.White, CornerRadius = 8 };
        button.Clicked += async (_, _) =>
        {
            if (working) return;
            working = true;
            Form.IsEnabled = false;
            try { await action(); }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException or JsonException or InvalidOperationException)
            {
                var message = e is InvalidOperationException ? e.Message :
                    "Não foi possível concluir o pedido. Confira o endereço e se o servidor do projeto está aberto.";
                await DisplayAlertAsync("Projeto Clubes", message, "OK");
            }
            finally { Form.IsEnabled = true; working = false; }
        };
        Form.Add(button);
    }

    protected void Divider() => Form.Add(new BoxView { HeightRequest = 1, Color = Color.FromArgb("#D5E1DB") });
}
