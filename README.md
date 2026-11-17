# Projeto Clubes

Sistema acadêmico para os clubes de Foz do Iguaçu e Guaíra. A equipe usa a web para administrar o clube. O sócio acessa o app .NET MAUI para Android ou Windows para se cadastrar, acompanhar a aprovação, reservar o salão, conversar com a presidência e consultar mensalidades. A web e o app usam os mesmos registros no servidor Flask com SQLite.

## Rodar a demonstração

No Windows, instale Python 3.10 ou superior, baixe e extraia o projeto e abra **iniciar.cmd**. A primeira execução usa internet para instalar duas dependências. Quando o terminal mostrar o endereço, abra **http://127.0.0.1:8000**. Mantenha o terminal aberto durante a apresentação.

No Linux ou macOS, use os comandos abaixo na pasta do projeto.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

A primeira execução cria quatro clubes fictícios, eventos e uma mensalidade em aberto. O terminal mostra a senha inicial das contas de demonstração. Ela também fica no arquivo local `instance/acesso-demo.txt`. Cadastros feitos pelo formulário usam a senha escolhida pelo sócio.

| Para entrar como | E-mail de demonstração | O que experimentar |
| --- | --- | --- |
| Sócio fundador | `socio@cdc.test` | Consultar a mensalidade e solicitar uma reserva |
| Presidente | `presidente@cdc.test` | Aprovar cadastro e reserva, responder reclamação, publicar evento |
| Tesoureiro | `tesoureiro@cdc.test` | Gerar mensalidades por mês e registrar pagamento |
| Superadministrador | `admin@clubes.test` | Alternar entre clubes, criar um clube e cadastrar a equipe |

CDC identifica o Clube das Cataratas. Nos outros clubes, os e-mails da equipe seguem o mesmo padrão com as siglas `adi`, `csq` e `cdp`.

**Para testar em um celular**, conecte-o ao mesmo Wi-Fi do computador. No PowerShell, na pasta do projeto, execute `$env:CLUBES_HOST = "0.0.0.0"` e depois `.\iniciar.cmd`. No celular, abra `http://IP-DO-COMPUTADOR:8000` usando o IPv4 da rede local. O Windows pode pedir acesso à rede privada. Use dados fictícios na demonstração.

## Abrir o app do sócio

1. Inicie a web com **iniciar.cmd** e mantenha o servidor aberto. Se ele já estava rodando antes de atualizar o código, reinicie-o.
2. Para apresentar tudo no mesmo PC Windows, abra **iniciar-app.cmd**. É preciso ter o SDK .NET 10 e as ferramentas .NET MAUI para Windows. Na primeira compilação, aguarde a restauração dos pacotes. O app abre em uma janela própria. O endereço padrão é `http://127.0.0.1:8000`.
3. Para usar Android, abra `mobile/Clubes.App/Clubes.App.csproj` no Visual Studio com as ferramentas .NET MAUI e o SDK Android instalados. Escolha um emulador Android e execute em **Debug**. O app já vem configurado para `http://10.0.2.2:8000` no Android.
4. Para usar um aparelho Android físico, inicie o servidor com `CLUBES_HOST=0.0.0.0` conforme as instruções de Wi-Fi acima. Execute a versão Debug no aparelho. Na tela de entrada do app, altere **Endereço do servidor** para `http://IP-DO-COMPUTADOR:8000`. O app lembra o último endereço usado com sucesso. O HTTP no Android está habilitado para a demonstração em Debug.
5. Entre com o sócio de demonstração ou toque em **Solicitar associação**. Use **Atualizar** para consultar uma decisão ou pagamento registrado na web.

A versão Android usa CoreCLR para que as consultas ao servidor funcionem no emulador testado (Android 15, API 35). No .NET 10, a Microsoft classifica esse runtime no Android como experimental. [Documentação do .NET MAUI 10](https://learn.microsoft.com/en-us/dotnet/maui/whats-new/dotnet-10?view=net-maui-10.0#experimental-coreclr)

Para compilar os dois destinos em um Windows com as ferramentas de Android e Windows instaladas, execute o comando abaixo.

```powershell
dotnet build mobile/Clubes.App/Clubes.App.csproj
```

## Planejamento e critérios de entrega

| Etapa | Entrega | Como verificar |
| --- | --- | --- |
| 1. Clubes e acesso | Diretório com dois clubes em cada cidade. Cada clube tem ID, nome, sigla, endereço, bairro, cidade, UF, telefone e e-mail. | Filtrar por Guaíra, abrir um clube e consultar os contatos. Entrar como superadministrador para editar os dados. |
| 2. Associação | Cadastro de nome, CPF, endereço, bairro, sexo, estado civil, cidade, UF, telefone, e-mail, nascimento e interesses. Aprovação pela presidência e dependentes vinculados ao titular. | Solicitar associação como convidado ou simpatizante. Entrar antes e depois da aprovação para ver a mudança de acesso. |
| 3. Eventos e salão | Evento com data, hora, público-alvo e acesso aberto ou exclusivo. Um salão social por clube, com pedidos de reserva que podem atravessar dias. | Criar um evento exclusivo e consultar a página com e sem login. Aprovar uma reserva e conferir o intervalo na agenda pública. |
| 4. Atendimento e financeiro | Solicitações e reclamações com resposta. Mensalidade por competência, valor definido pelo clube e baixa manual pelo tesoureiro. | Enviar uma reclamação, responder como presidente e ler a resposta como sócio. Registrar pagamento e conferir a situação no celular. |

**Regras adotadas para o trabalho**

- O presidente administra o próprio clube. O tesoureiro acessa o financeiro do seu clube. O superadministrador pode trabalhar em qualquer clube.
- Associado e fundador têm direito a voto. Convidado e simpatizante ficam sem voto. O painel mostra esse direito. A presidência confirma a categoria ao aprovar o cadastro.
- O dependente é cadastrado pelo titular com nome, nascimento e parentesco. O acesso ao aplicativo é pelo titular.
- O clube tem um salão social. O presidente aprova ou recusa cada pedido. A agenda pública mostra os horários confirmados. Reservas do mesmo clube podem ser consecutivas e não podem se sobrepor.
- Os horários são locais. A publicação de um evento e a reserva do salão são operações independentes, pois um evento pode acontecer em outro local.
- O tesoureiro escolhe o mês e gera uma cobrança para cada sócio ativo pelo valor vigente. Repetir a operação inclui sócios aprovados depois e preserva cobranças já emitidas. O sócio vê a situação “Em aberto” ou “Paga” e a data do pagamento.

## Roteiro para apresentar ao professor

1. No **app MAUI**, toque em **Solicitar associação**. Escolha o Clube das Cataratas, a categoria Convidado e preencha o cadastro com dados fictícios. Entre com a nova conta para ver “Aguardando aprovação”.
2. No **navegador**, entre como presidente do mesmo clube. Em **Sócios → Analisar cadastro**, aprove o pedido. No app, toque em **Atualizar** para liberar o painel.
3. No app, peça o salão de sábado às 18h até domingo às 10h, usando datas futuras. Aprove pela web. Confira o intervalo na agenda do site e a situação “Aprovada” na lista do app.
4. Envie uma reclamação no app, responda na web como presidente e toque em **Atualizar** no app para ler a resposta.
5. Entre na web como tesoureiro, gere as mensalidades do mês e confira “Em aberto” no app. Registre o pagamento na web e atualize **Minhas mensalidades** no app para mostrar a data da baixa.
6. Para mostrar os dependentes, use a área web do titular. Para apresentar um evento exclusivo, publique-o na presidência e compare a página pública do clube com a página vista pelo sócio aprovado.

## Estrutura e verificação

Python com Flask atende as páginas e valida cada ação no servidor. O SQLite guarda clubes, usuários, dependentes, eventos, reservas, mensagens e mensalidades. A relação com o clube delimita os registros de cada equipe. O valor da mensalidade é gravado em centavos.

O banco e a senha de demonstração ficam em `instance/`, fora do Git. Fechar e abrir o sistema preserva os dados. O GitHub entrega o código e o planejamento. O servidor da demonstração roda no computador que executa o projeto.

Com o ambiente virtual ativo, execute os testes em um banco temporário.

```sh
python -m unittest discover -s tests -v
```
