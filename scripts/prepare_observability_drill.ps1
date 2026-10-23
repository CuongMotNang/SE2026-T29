[CmdletBinding()]
param(
    [string]$DiscordWebhookUrl,
    [ValidateSet("127.0.0.1", "0.0.0.0")]
    [string]$BindAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$environmentTemplate = Join-Path $repositoryRoot "deploy/observability.env.example"
$environmentFile = Join-Path $repositoryRoot "deploy/observability.env"
$webhookFile = Join-Path $repositoryRoot "deploy/observability/alertmanager/discord-webhook-url"

if (-not (Test-Path -LiteralPath $environmentTemplate)) {
    throw "Missing observability environment template: $environmentTemplate"
}

if ($DiscordWebhookUrl -and $DiscordWebhookUrl -notmatch '^https://(discord(?:app)?\.com)/api/webhooks/') {
    throw "DiscordWebhookUrl must be a Discord webhook URL"
}

$passwordBytes = New-Object byte[] 24
$randomNumberGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $randomNumberGenerator.GetBytes($passwordBytes)
}
finally {
    $randomNumberGenerator.Dispose()
}
$grafanaPassword = [Convert]::ToBase64String($passwordBytes).TrimEnd("=").Replace("+", "A").Replace("/", "B")

$environmentContent = Get-Content -Raw -LiteralPath $environmentTemplate
$environmentContent = $environmentContent.Replace("OBS_BIND_ADDRESS=127.0.0.1", "OBS_BIND_ADDRESS=$BindAddress")
$environmentContent = $environmentContent.Replace("GRAFANA_ADMIN_PASSWORD=change-me", "GRAFANA_ADMIN_PASSWORD=$grafanaPassword")
[System.IO.File]::WriteAllText($environmentFile, $environmentContent, [System.Text.UTF8Encoding]::new($false))

if ($DiscordWebhookUrl) {
    [System.IO.File]::WriteAllText($webhookFile, $DiscordWebhookUrl.Trim(), [System.Text.UTF8Encoding]::new($false))
}
elseif (-not (Test-Path -LiteralPath $webhookFile)) {
    [System.IO.File]::WriteAllText($webhookFile, "https://discord.com/api/webhooks/replace/me", [System.Text.UTF8Encoding]::new($false))
}

Write-Host "Prepared ignored local files:"
Write-Host "  deploy/observability.env"
Write-Host "  deploy/observability/alertmanager/discord-webhook-url"
if (-not $DiscordWebhookUrl) {
    Write-Warning "The Discord webhook is still a placeholder. Run this script again with -DiscordWebhookUrl before the drill."
}
