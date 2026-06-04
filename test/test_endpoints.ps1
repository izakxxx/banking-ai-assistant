param(
  [string]$BaseUrl = "http://127.0.0.1:8008",
  [switch]$IncludeLLM
)

$ErrorActionPreference = "Stop"

function Invoke-Json($method, $url, $body, $timeoutSec) {
  $json = $null
  if ($null -ne $body) { $json = ($body | ConvertTo-Json -Depth 10) }

  if ($method -eq "GET") {
    return Invoke-RestMethod -Method Get -Uri $url -TimeoutSec $timeoutSec
  }

  return Invoke-RestMethod -Method $method -Uri $url -ContentType "application/json" -Body $json -TimeoutSec $timeoutSec
}

$tests = @(
  @{ name = "health"; method = "GET"; path = "/health"; body = $null; timeout = 10 },
  @{ name = "search"; method = "POST"; path = "/search"; body = @{ message = "monthly fee" }; timeout = 20 },
  @{ name = "semantic-search"; method = "POST"; path = "/semantic-search"; body = @{ message = "feeOnMonthDay monthDayFormat feeInterval" }; timeout = 30 },
  @{ name = "hybrid-search"; method = "POST"; path = "/hybrid-search"; body = @{ message = "feeOnMonthDay monthDayFormat feeInterval" }; timeout = 30 },
  @{ name = "answer-draft"; method = "POST"; path = "/answer-draft"; body = @{ message = "How do I configure a Monthly Fee charge on a savings account?" }; timeout = 30 }
)

if ($IncludeLLM) {
  $tests += @(
    @{ name = "chat"; method = "POST"; path = "/chat"; body = @{ message = "hola" }; timeout = 60 },
    @{ name = "chat-rag"; method = "POST"; path = "/chat-rag"; body = @{ message = "How do I configure a Monthly Fee charge on a savings account?" }; timeout = 90 }
  )
}

$results = @()

foreach ($t in $tests) {
  $url = "$BaseUrl$($t.path)"
  try {
    $null = Invoke-Json $t.method $url $t.body $t.timeout
    $results += [pscustomobject]@{ endpoint = $t.path; method = $t.method; status = "OK" }
  } catch {
    $msg = $_.Exception.Message
    $results += [pscustomobject]@{ endpoint = $t.path; method = $t.method; status = "FAIL"; error = $msg }
  }
}

$results | Format-Table -AutoSize

if ($results | Where-Object { $_.status -eq "FAIL" }) {
  exit 1
}
