using System.Globalization;

namespace Clubes.App;

internal sealed class SignupPage : FormPage
{
    public SignupPage(ClubeApi api, Start start) : base("Solicitar associação")
    {
        var club = Field("Clube", new Picker { ItemsSource = start.Clubs, SelectedIndex = 0 });
        var category = Choices("Categoria", ["Convidado", "Simpatizante"]);
        var name = Field("Nome completo", new Entry());
        var email = Field("E-mail", new Entry { Keyboard = Keyboard.Email });
        var password = Field("Senha (mínimo de 8 caracteres)", new Entry { IsPassword = true });
        var cpf = Field("CPF", new Entry { Keyboard = Keyboard.Numeric, MaxLength = 14 });
        var birth = Field("Data de nascimento", new DatePicker { Format = "dd/MM/yyyy", MaximumDate = DateTime.Today, Date = null });
        var phone = Field("Telefone", new Entry { Keyboard = Keyboard.Telephone });
        var address = Field("Endereço", new Entry());
        var district = Field("Bairro", new Entry());
        var city = Field("Cidade", new Entry());
        var state = Choices("UF", start.States, Array.IndexOf(start.States, "PR"));
        var sex = Choices("Sexo", ["Feminino", "Masculino", "Outro", "Prefiro não informar"], -1);
        var civil = Choices("Estado civil", ["Solteiro(a)", "Casado(a)", "União estável", "Divorciado(a)", "Viúvo(a)", "Outro"], -1);
        var interests = Field("Interesses (opcional)", new Entry { MaxLength = 300 });

        ActionButton("Enviar cadastro", async () =>
        {
            if (club.SelectedItem is not Club selected)
                throw new InvalidOperationException("Escolha o clube.");
            var result = await api.SubmitAsync("cadastro", new()
            {
                ["club"] = selected.Id.ToString(CultureInfo.InvariantCulture),
                ["category"] = (string)category.SelectedItem,
                ["name"] = name.Text ?? "", ["email"] = email.Text ?? "", ["password"] = password.Text ?? "",
                ["cpf"] = cpf.Text ?? "", ["birth"] = birth.Date?.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture) ?? "",
                ["address"] = address.Text ?? "", ["district"] = district.Text ?? "", ["city"] = city.Text ?? "",
                ["uf"] = (string)state.SelectedItem, ["phone"] = phone.Text ?? "", ["sex"] = sex.SelectedItem as string ?? "",
                ["civil"] = civil.SelectedItem as string ?? "", ["interests"] = interests.Text ?? ""
            });
            await DisplayAlertAsync("Associação", result.Message, "OK");
            await Navigation.PopAsync();
        });
    }
}
