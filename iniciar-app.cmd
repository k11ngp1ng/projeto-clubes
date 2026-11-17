@echo off
setlocal
cd /d "%~dp0"
dotnet run --project "mobile\Clubes.App\Clubes.App.csproj" --framework net10.0-windows10.0.19041.0
if errorlevel 1 (
    echo Verifique se o SDK .NET 10 e as ferramentas .NET MAUI estao instalados.
    pause
    exit /b 1
)
