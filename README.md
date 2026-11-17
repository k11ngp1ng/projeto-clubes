# Projeto Clubes

Sistema acadêmico para administrar clubes de Foz do Iguaçu e Guaíra. O sócio usa o navegador do celular para solicitar associação, reservar o salão e consultar mensalidades. A equipe entra no mesmo sistema e recebe um painel conforme a função.

## O que falta para a entrega web + .NET MAUI

A web em Flask já atende o presidente, o tesoureiro e o superadministrador. A área do sócio também funciona no navegador. Ainda faltam o projeto .NET MAUI, a API que ele vai consumir e a demonstração integrada. O plano é manter um único banco SQLite no servidor. Assim, quando o presidente aprovar um pedido na web, o sócio verá a decisão ao atualizar a tela do app.

| Ordem | Implementar | Como saber que funciona |
| --- | --- | --- |
| 1. Cadastro e aprovação | Criar o app MAUI com seleção de clube, cadastro de convidado ou simpatizante e login. Expor essas operações em uma API JSON do Flask, reaproveitando as regras de cadastro. | Cadastrar pelo app, ver “Aguardando aprovação”, aprovar na web e atualizar o app para ver nome do clube, categoria e direito a voto. Um cadastro pendente ou recusado fica sem acesso às operações do sócio. |
| 2. Reserva do salão | No app, informar finalidade, data e hora de início e de término. Mostrar a situação do pedido. Usar a mesma verificação de horários da web. | Pedir o salão de sábado à noite até domingo de manhã, aprovar na web e conferir o horário na agenda do site. O app mostra “Aprovada” e informa quando o período já está ocupado. |
| 3. Atendimento e mensalidades | No app, reunir solicitações e reclamações em uma tela com tipo, mensagem e resposta. Em Mensalidades, listar mês, valor e situação do titular. | Enviar uma reclamação pelo app e ler a resposta da presidência. Gerar a mensalidade na web, conferir “Em aberto” no app, registrar o pagamento como tesoureiro e atualizar para ver “Paga”. |
| 4. Entrega | Incluir o app no mesmo repositório e documentar como iniciar o servidor e conectar o app no aparelho ou emulador escolhido. | Em uma cópia limpa do repositório, seguir as instruções com dados fictícios e repetir o fluxo usando o app e o navegador lado a lado. |

Em cada etapa, a API deve identificar o titular pela sessão autenticada e limitar as consultas e alterações aos dados desse titular e do clube dele. A versão inicial mantém os dependentes vinculados ao titular pelo cadastro web. Acesso próprio para dependente pode ser acrescentado se o professor confirmar essa necessidade.

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

1. Abra o **Clube das Cataratas** no diretório e clique em **Solicitar associação**. Use nome, CPF fictício com 11 dígitos e e-mail de teste. Selecione **Convidado**. Entre com essa conta para mostrar o pedido pendente.
2. Em outro navegador ou em uma janela privativa, entre como **presidente**. Em **Sócios → Analisar cadastro**, aprove o pedido. Atualize a janela do sócio para mostrar o painel liberado.
3. Como sócio, cadastre um dependente e peça o salão de sábado às 18h até domingo às 10h, usando datas futuras. Como presidente, aprove o pedido. Abra **Ver página do clube** para mostrar o intervalo na agenda.
4. Como sócio, envie uma reclamação em **Mensagens**. Responda na conta da presidência e confira a resposta na conta do sócio.
5. Entre como **tesoureiro**. Gere as mensalidades do mês e registre o pagamento do novo sócio. Na janela dele, abra **Mensalidades** e confira o valor, o mês e a data da baixa.

## Estrutura e verificação

Python com Flask atende as páginas e valida cada ação no servidor. O SQLite guarda clubes, usuários, dependentes, eventos, reservas, mensagens e mensalidades. A relação com o clube delimita os registros de cada equipe. O valor da mensalidade é gravado em centavos.

O banco e a senha de demonstração ficam em `instance/`, fora do Git. Fechar e abrir o sistema preserva os dados. O GitHub entrega o código e o planejamento. O servidor da demonstração roda no computador que executa o projeto.

Com o ambiente virtual ativo, execute os testes em um banco temporário.

```sh
python -m unittest discover -s tests -v
```
