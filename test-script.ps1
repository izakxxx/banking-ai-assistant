# =========================
# Fineract AI Assistant - Step-by-step execution runner
# =========================
# Ejecuta los pasos 1 a 1 contra /chat-rag y guarda un JSON separado por cada respuesta.
# Uso:
#   powershell -ExecutionPolicy Bypass -File .\test-script-steps.ps1

# =========================
# Config
# =========================
$uri = "http://localhost:8000/chat-rag"
$sessionId = "real-exec-1"
$accountId = 1
$tenantId = "default"
$debugEnabled = $true

$outputDir = ".\responses_$sessionId"
$summaryFile = Join-Path $outputDir "00_summary.json"

# Crea carpeta de salida si no existe
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# =========================
# Steps
# =========================
# Nota: todos los pasos usan el mismo session_id porque el backend guarda el execution_plan en sesión.
$steps = @(
    @{
        number  = 1
        name    = "create_plan"
        message = "create monthly maintenance fee for savings account"
    },
    @{
        number  = 2
        name    = "provide_parameters"
        message = "chargeId=2 amount=0.15"
    },
    @{
        number  = 3
        name    = "dry_run"
        message = "dry run"
    },
    @{
        number  = 4
        name    = "execute"
        message = "execute"
    }
)

# =========================
# Helper: Invoke one step
# =========================
function Invoke-ExecutionStep {
    param (
        [Parameter(Mandatory = $true)]
        [hashtable]$Step
    )

    $stepNumber = "{0:D2}" -f [int]$Step.number
    $safeName = $Step.name
    $outputFile = Join-Path $outputDir "$stepNumber`_$safeName.json"

    $body = @{
        message    = $Step.message
        mode       = "execution"
        account_id = $accountId
        tenant_id  = $tenantId
        session_id = $sessionId
        debug      = $debugEnabled
    } | ConvertTo-Json -Depth 10

    Write-Host ""
    Write-Host "========================================"
    Write-Host "▶️  Step $stepNumber - $safeName"
    Write-Host "💬 Message: $($Step.message)"
    Write-Host "📄 Output : $outputFile"
    Write-Host "========================================"

    try {
        $response = Invoke-RestMethod `
            -Uri $uri `
            -Method POST `
            -Body $body `
            -ContentType "application/json" `
            -ErrorAction Stop

        $response | ConvertTo-Json -Depth 100 | Out-File $outputFile -Encoding utf8

        Write-Host "✅ Step $stepNumber guardado correctamente."

        return @{
            step       = [int]$Step.number
            name       = $safeName
            message    = $Step.message
            status     = "success"
            outputFile = $outputFile
            answer     = $response.answer
            confidence = $response.confidence
        }
    }
    catch {
        $errorFile = Join-Path $outputDir "$stepNumber`_$safeName.error.txt"
        $errorMessage = $_.Exception.Message

        $errorMessage | Out-File $errorFile -Encoding utf8

        Write-Host "❌ Step $stepNumber falló. Error guardado en: $errorFile" -ForegroundColor Red
        Write-Host $errorMessage -ForegroundColor Red

        return @{
            step       = [int]$Step.number
            name       = $safeName
            message    = $Step.message
            status     = "failed"
            outputFile = $null
            errorFile  = $errorFile
            error      = $errorMessage
        }
    }
}

# =========================
# Run steps sequentially
# =========================
$summary = @()

foreach ($step in $steps) {
    $result = Invoke-ExecutionStep -Step $step
    $summary += $result

    # Si un paso falla, detenemos para no ejecutar acciones con estado inconsistente.
    if ($result.status -eq "failed") {
        Write-Host "🛑 Ejecución detenida por error en el paso $($result.step)." -ForegroundColor Yellow
        break
    }

    # Pausa corta para que los logs sean legibles y evitar pisar estado si el backend tarda.
    Start-Sleep -Seconds 1
}

# =========================
# Save summary
# =========================
$summary | ConvertTo-Json -Depth 100 | Out-File $summaryFile -Encoding utf8

Write-Host ""
Write-Host "Resumen guardado en: $summaryFile"
Write-Host "Carpeta de respuestas: $outputDir"