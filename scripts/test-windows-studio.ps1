$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$archive = Join-Path (Split-Path -Parent $root) 'videoX-Brazil-UGC-Windows.zip'
$unpack = Join-Path $env:RUNNER_TEMP 'videox-windows-smoke'
$studioRoot = Join-Path $unpack 'videoX'

if (-not (Test-Path $archive)) { throw "缺少 Windows 压缩包：$archive" }
Write-Host '正在解压 Windows 安装包……'
Expand-Archive -Path $archive -DestinationPath $unpack -Force
$launcher = Join-Path $studioRoot '一键启动.cmd'
if (-not (Test-Path $launcher)) { throw '压缩包内缺少中文一键启动入口。' }
Write-Host '解压完成，正在模拟首次双击中文入口……'

$launchLog = Join-Path $env:RUNNER_TEMP 'videox-launch.out.log'
$errorLog = Join-Path $env:RUNNER_TEMP 'videox-launch.err.log'
$runner = $null
try {
    $env:STUDIO_NO_PAUSE = '1'
    $runner = Start-Process -FilePath 'cmd.exe' -ArgumentList '/d', '/c', "`"$launcher`"" -WorkingDirectory $studioRoot -WindowStyle Hidden -RedirectStandardOutput $launchLog -RedirectStandardError $errorLog -PassThru
    $ready = $false
    $deadline = [DateTime]::UtcNow.AddMinutes(3)
    $nextProgress = [DateTime]::UtcNow.AddSeconds(30)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8787/api/health' -TimeoutSec 2
            if ($health.ok -eq $true) { $ready = $true; break }
        } catch { }
        if ($runner.HasExited) { break }
        if ([DateTime]::UtcNow -ge $nextProgress) {
            Write-Host '仍在等待首次启动，正在准备本地运行环境……'
            $nextProgress = [DateTime]::UtcNow.AddSeconds(30)
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw '双击启动入口后，本地网页未在三分钟内启动。' }
    Write-Host '首次双击已启动本地服务，正在检查网页和内置素材……'

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

    Write-Host '正在模拟重复双击……'
    $second = Start-Process -FilePath 'cmd.exe' -ArgumentList '/d', '/c', "`"$launcher`"" -WorkingDirectory $studioRoot -WindowStyle Hidden -PassThru
    for ($attempt = 0; $attempt -lt 15 -and -not $second.HasExited; $attempt++) {
        Start-Sleep -Seconds 1
    }
    if (-not $second.HasExited) {
        Stop-Process -Id $second.Id -Force -ErrorAction SilentlyContinue
        throw '重复双击后启动器未在 15 秒内退出。'
    }
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
