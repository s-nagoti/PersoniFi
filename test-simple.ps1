# Simple PowerShell test for PersoniFi API
# This uses Invoke-RestMethod which handles multipart forms better

$filePath = "sample_transactions.csv"
$uri = "http://localhost:3000/api/parse-transactions"

Write-Host "🧪 Testing PersoniFi API..." -ForegroundColor Green
Write-Host "📁 File: $filePath" -ForegroundColor Blue

try {
    # Create form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $fileBytes = [System.IO.File]::ReadAllBytes($filePath)
    $fileEnc = [System.Text.Encoding]::GetEncoding('UTF-8').GetString($fileBytes)
    
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$filePath`"",
        "Content-Type: text/csv$LF",
        $fileEnc,
        "--$boundary--$LF"
    ) -join $LF
    
    $response = Invoke-RestMethod -Uri $uri -Method Post -Body $bodyLines -ContentType "multipart/form-data; boundary=$boundary"
    
    if ($response.success) {
        Write-Host "✅ API Test Successful!" -ForegroundColor Green
        Write-Host "📊 Total transactions: $($response.metadata.total_transactions)" -ForegroundColor Yellow
        Write-Host "📅 Date range: $($response.data[-1].date) to $($response.data[0].date)" -ForegroundColor Yellow
        
        Write-Host "`n💰 First 3 transactions:" -ForegroundColor Cyan
        $response.data[0..2] | ForEach-Object {
            $merchant = if ($_.merchant.Length -gt 30) { $_.merchant.Substring(0, 30) + "..." } else { $_.merchant }
            Write-Host "   $($_.date) | $merchant | `$$($_.amount) | $($_.category)"
        }
        
        Write-Host "`n📋 Column mapping:" -ForegroundColor Cyan
        Write-Host "   Date: $($response.metadata.column_mapping.date)"
        Write-Host "   Amount: $($response.metadata.column_mapping.amount)"
        Write-Host "   Merchant: $($response.metadata.column_mapping.merchant)"
        Write-Host "   Category: $($response.metadata.column_mapping.category)"
    } else {
        Write-Host "❌ API Test Failed!" -ForegroundColor Red
        Write-Host "Error: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
}
