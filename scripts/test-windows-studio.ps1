$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$archive = Join-Path (Split-Path -Parent $root) 'videoX-Brazil-UGC-Windows.zip'
$unpack = Join-Path $env:RUNNER_TEMP 'videox-windows-smoke'
$studioRoot = Join-Path $unpack 'videoX'

if (-not (Test-Path $archive)) { throw "缺少 Windows 压缩包：$archive" }
Expand-Archive -Path $archive -DestinationPath $unpack -Force
$launcher = Join-Path $studioRoot '一键启动.cmd'
if (-not (Test-Path $launcher)) { throw '压缩包内缺少中文一键启动入口。' }

$launchLog = Join-Path $env:RUNNER_TEMP 'videox-launch.out.log'
$errorLog = Join-Path $env:RUNNER_TEMP 'videox-launch.err.log'
$runner = $null
try {
    $runner = Start-Process -FilePath 'cmd.exe' -ArgumentList '/d', '/c', "`"$launcher`"" -WorkingDirectory $studioRoot -WindowStyle Hidden -RedirectStandardOutput $launchLog -RedirectStandardError $errorLog -PassThru
    $ready = $false
    for ($attempt = 0; $attempt -lt 180; $attempt++) {
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8787/api/health' -TimeoutSec 2
            if ($health.ok -eq $true) { $ready = $true; break }
        } catch { }
        if ($runner.HasExited) { break }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw '双击启动入口后，本地网页未在六分钟内启动。' }

    $page = Invoke-WebRequest 'http://127.0.0.1:8787/' -UseBasicParsing -TimeoutSec 10
    if ($page.StatusCode -ne 200 -or $page.Content -notmatch '<html') {
        throw '服务启动，但网页首页未正常返回。'
    }
    $assets = Invoke-WebRequest 'http://127.0.0.1:8787/api/assets' -UseBasicParsing -TimeoutSec 10
    if ($assets.StatusCode -ne 200 -or $assets.Content -notmatch '^\[') {
        throw '素材接口未正常返回。'
    }
    $references = @($assets.Content | ConvertFrom-Json)
    if (@($references | Where-Object { $_.role -eq 'character' }).Count -lt 1 -or
        @($references | Where-Object { $_.role -eq 'scene' }).Count -lt 1) {
        throw '合成内置人物或场景未随压缩包加载。'
    }

    $second = Start-Process -FilePath 'cmd.exe' -ArgumentList '/d', '/c', "`"$launcher`"" -WorkingDirectory $studioRoot -WindowStyle Hidden -Wait -PassThru
    if ($second.ExitCode -ne 0) { throw '重复双击未能打开已经运行的工作室。' }
    Write-Host 'Windows 云端验证通过：解压 → 双击中文入口 → 网页与素材接口 → 重复双击。'
} catch {
    if (Test-Path $launchLog) { Get-Content $launchLog -Tail 80 }
    if (Test-Path $errorLog) { Get-Content $errorLog -Tail 80 }
    throw
} finally {
    $listener = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) { Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue }
    if ($runner -and -not $runner.HasExited) { Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue }
}
