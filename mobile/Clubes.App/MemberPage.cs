using System.Globalization;

namespace Clubes.App;

internal sealed class MemberPage : FormPage
{
    private readonly ClubeApi api;
    private Panel panel;
    private enum Section { Home, Bookings, Tickets, Dues }
    private Section section;
    private static readonly CultureInfo PtBr = CultureInfo.GetCultureInfo("pt-BR");

    public MemberPage(ClubeApi api, Panel panel) : base("Área do sócio")
    {
        this.api = api;
        this.panel = panel;
        Render();
    }

    private async Task Open(Section next)
    {
        var updated = await api.PanelAsync();
        panel = updated;
        section = updated.Status == "ativo" ? next : Section.Home;
        Render();
        if (Content is ScrollView scroll && scroll.ScrollY > 0)
            _ = scroll.ScrollToAsync(0, 0, false);
    }

    private void Render()
    {
        Form.Clear();
        if (section == Section.Home)
        {
            Heading(panel.Club);
            Line($"{panel.Name} · {panel.Category}");
            if (panel.Status == "ativo")
            {
                Line(panel.Vote ? "Com direito a voto" : "Sem direito a voto");
                ActionButton("Reservas do salão", () => Open(Section.Bookings));
                ActionButton("Solicitações e reclamações", () => Open(Section.Tickets));
                ActionButton("Minhas mensalidades", () => Open(Section.Dues));
            }
            else
            {
                Line(panel.Status == "pendente" ? "Aguardando aprovação da presidência." : "Cadastro recusado pela presidência.");
            }
        }
        else
        {
            ActionButton("Voltar ao início", () => Open(Section.Home));
            if (section == Section.Bookings) Bookings();
            if (section == Section.Tickets) Tickets();
            if (section == Section.Dues) Dues();
        }
        ActionButton("Atualizar", () => Open(section));
        ActionButton("Sair", () =>
        {
            api.Dispose();
            Window!.Page = App.Login();
            return Task.CompletedTask;
        });
    }

    private void Bookings()
    {
        Heading("Reservar o salão");
        var purpose = Field("Finalidade", new Entry());
        var tomorrow = DateTime.Today.AddDays(1);
        var start = Field("Data de início", new DatePicker { Date = tomorrow, MinimumDate = DateTime.Today, Format = "dd/MM/yyyy" });
        var startTime = Field("Hora de início", new TimePicker { Time = TimeSpan.FromHours(12), Format = "HH:mm" });
        var end = Field("Data de término", new DatePicker { Date = tomorrow, MinimumDate = DateTime.Today, Format = "dd/MM/yyyy" });
        var endTime = Field("Hora de término", new TimePicker { Time = TimeSpan.FromHours(14), Format = "HH:mm" });
        ActionButton("Enviar pedido de reserva", async () =>
        {
            var result = await api.SubmitAsync("reservas", new()
            {
                ["purpose"] = purpose.Text ?? "", ["starts"] = Instant(start, startTime), ["ends"] = Instant(end, endTime)
            });
            purpose.Text = "";
            await DisplayAlertAsync("Reserva", result.Message, "OK");
            await Open(Section.Bookings);
        });
        Heading("Minhas reservas");
        if (panel.Bookings.Length == 0) Line("Nenhuma reserva solicitada.");
        foreach (var item in panel.Bookings)
        {
            Divider();
            Line($"{item.Purpose} · {item.Status}");
            Line($"{item.Starts:dd/MM/yyyy HH:mm} até {item.Ends:dd/MM/yyyy HH:mm}");
        }
    }

    private static string Instant(DatePicker day, TimePicker clock)
    {
        if (day.Date is not DateTime date || clock.Time is not TimeSpan time)
            throw new InvalidOperationException("Preencha as datas e os horários da reserva.");
        return date.Date.Add(time).ToString("yyyy-MM-dd'T'HH:mm", CultureInfo.InvariantCulture);
    }

    private void Tickets()
    {
        Heading("Solicitações e reclamações");
        var kind = Choices("Tipo", ["Solicitação", "Reclamação"]);
        var body = Field("Mensagem", new Editor { HeightRequest = 95, MaxLength = 2000 });
        ActionButton("Enviar à presidência", async () =>
        {
            var result = await api.SubmitAsync("mensagens", new()
            {
                ["kind"] = (string)kind.SelectedItem, ["body"] = body.Text ?? ""
            });
            body.Text = "";
            await DisplayAlertAsync("Atendimento", result.Message, "OK");
            await Open(Section.Tickets);
        });
        Heading("Minhas mensagens");
        if (panel.Tickets.Length == 0) Line("Nenhuma mensagem enviada.");
        foreach (var ticket in panel.Tickets)
        {
            Divider();
            Line($"{ticket.Kind} · {ticket.Created:dd/MM/yyyy}");
            Line(ticket.Body);
            Line(ticket.Reply is null ? "Aguardando resposta." : $"Presidência · {ticket.Reply}");
        }
    }

    private void Dues()
    {
        Heading("Minhas mensalidades");
        if (panel.Dues.Length == 0) Line("Nenhuma mensalidade lançada.");
        foreach (var due in panel.Dues)
        {
            Divider();
            Line($"{due.Period[5..]}/{due.Period[..4]} · {(due.Amount / 100m).ToString("C", PtBr)}");
            Line(due.Paid is null ? "Em aberto" : $"Paga em {DateOnly.Parse(due.Paid, CultureInfo.InvariantCulture):dd/MM/yyyy}");
        }
    }
}
