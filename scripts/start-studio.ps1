$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

try {
    Write-Host 'Robin X 巴西 UGC 工作室 · 一键启动' -ForegroundColor Cyan
    Write-Host '首次运行会自动准备所需环境；之后双击即可打开。'

    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8787/api/health' -TimeoutSec 2
        if ($health.ok -eq $true) {
            Write-Host '工作室已经运行，正在打开网页……'
            Start-Process 'http://127.0.0.1:8787'
            exit 0
        }
    } catch { }

    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        Write-Host '正在准备 Python 运行环境……'
        $created = $false
        if (Get-Command python -ErrorAction SilentlyContinue) {
            try {
                & python -c 'import sys; sys.exit(sys.version_info < (3, 11))' *> $null
                if ($LASTEXITCODE -eq 0) {
                    & python -m venv .venv
                    $created = $LASTEXITCODE -eq 0
                }
            } catch { }
        }
        if (-not $created -and (Get-Command py -ErrorAction SilentlyContinue)) {
            try {
                & py -3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' *> $null
                if ($LASTEXITCODE -eq 0) {
                    & py -3 -m venv .venv
                    $created = $LASTEXITCODE -eq 0
                }
            } catch { }
        }
        if (-not $created) {
            if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
                throw '未找到 Python 3.11+，也无法自动安装。请从 python.org 安装 Python 3.11+（勾选 Add Python to PATH）后重新双击。'
            }
            Write-Host '本机没有 Python 3.11+，正在通过 Windows 软件包管理器自动安装（仅首次需要）……'
            & winget install --id Python.Python.3.11 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -ne 0) { throw 'Python 自动安装失败。请检查网络连接，或从 python.org 手动安装后重试。' }
            $installedPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'
            if (-not (Test-Path $installedPython)) {
                throw 'Python 安装完成但未找到程序。请关闭此窗口后重新双击；如果仍失败，请从 python.org 安装 Python 3.11+。'
            }
            & $installedPython -m venv .venv
            if ($LASTEXITCODE -ne 0) { throw '创建 Python 运行环境失败。' }
        }
    }

    $studioPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path $studioPython)) { throw '未能找到工作室运行环境，请重新双击启动。' }
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $requirementsBytes = [System.IO.File]::ReadAllBytes((Join-Path $projectRoot 'requirements-studio.txt'))
        $requirementsHash = [BitConverter]::ToString($sha256.ComputeHash($requirementsBytes)).Replace('-', '')
    } finally { $sha256.Dispose() }
    $stampPath = Join-Path $projectRoot '.venv\studio-dependencies.sha256'
    $savedHash = if (Test-Path $stampPath) { (Get-Content $stampPath -Raw).Trim() } else { '' }
    if ($savedHash -ne $requirementsHash) {
        Write-Host '正在安装工作室依赖（首次启动可能需要几分钟）……'
        & $studioPython -m pip install -r requirements-studio.txt
        if ($LASTEXITCODE -ne 0) { throw '依赖安装失败。请检查网络连接后重新双击。' }
        Set-Content -Path $stampPath -Value $requirementsHash -Encoding ASCII
    }

    $frontendHash = (& $studioPython -m studio.frontend_build).Trim()
    if ($LASTEXITCODE -ne 0) { throw '检查网页资源失败。' }
    $frontendStamp = Join-Path $projectRoot 'studio-web\dist\inputs.sha256'
    $savedFrontendHash = if (Test-Path $frontendStamp) { (Get-Content $frontendStamp -Raw).Trim() } else { '' }
    if (-not (Test-Path 'studio-web\dist\index.html') -or $savedFrontendHash -ne $frontendHash) {
        if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
            throw '网页资源需要重新构建，但未安装 Node.js 22+。请使用完整的 Windows ZIP，或安装 Node.js 后重试。'
        }
        Write-Host '检测到网页源码已更新，正在重新构建……'
        Push-Location 'studio-web'
        try {
            & npx --yes pnpm@9.12.0 install --frozen-lockfile
            if ($LASTEXITCODE -ne 0) { throw '网页依赖安装失败。' }
            & npx --yes pnpm@9.12.0 build
            if ($LASTEXITCODE -ne 0) { throw '网页构建失败。' }
            Set-Content -Path $frontendStamp -Value $frontendHash -Encoding ASCII
        } finally { Pop-Location }
    }

    Write-Host '启动成功后将自动打开浏览器：http://127.0.0.1:8787' -ForegroundColor Green
    Write-Host '使用期间请保持此窗口打开；关闭网页不会中断后台任务。'
    & $studioPython -m studio --open
    if ($LASTEXITCODE -ne 0) { throw '工作室意外停止，请检查上方错误信息。' }
} catch {
    Write-Host "启动失败：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
