# Workflow Speed Test (PowerShell)
# Run these commands to test caching performance

# Test 1: Clear any existing cache (optional - to get fresh baseline)
# Remove-Item outputs/cache/*.json -ErrorAction SilentlyContinue

# Test 2: First request (hits Gemini API - slower)
Write-Host "=== TEST 1: First Request (API Call) ===" -ForegroundColor Yellow
$start1 = Get-Date
$response1 = curl.exe -s -X POST "http://localhost:8001/verification/parse/offer-letter" -H "Legitimacy-engine-key: n9MglUvVhYaF4jhq5I5QGaBQlCDFjwPZdU6xE9_fu6U" -F "offer_text=Speed test: Data Analyst internship at Analytics Corp. HR: hr@analytics.com, Priya Singh. Bangalore, India. Stipend 20000." -F "student_programme=BSc Statistics and Mathematics"
$time1 = (Get-Date) - $start1
Write-Host "Time: $($time1.TotalSeconds) seconds" -ForegroundColor Cyan
Write-Host $response1

# Test 3: Same request (should hit cache - instant)
Write-Host "`n=== TEST 2: Second Request (Cached) ===" -ForegroundColor Yellow
$start2 = Get-Date
$response2 = curl.exe -s -X POST "http://localhost:8001/verification/parse/offer-letter" -H "Legitimacy-engine-key: n9MglUvVhYaF4jhq5I5QGaBQlCDFjwPZdU6xE9_fu6U" -F "offer_text=Speed test: Data Analyst internship at Analytics Corp. HR: hr@analytics.com, Priya Singh. Bangalore, India. Stipend 20000." -F "student_programme=BSc Statistics and Mathematics"
$time2 = (Get-Date) - $start2
Write-Host "Time: $($time2.TotalSeconds) seconds" -ForegroundColor Cyan
Write-Host $response2

# Summary
Write-Host "`n=== RESULTS ===" -ForegroundColor Green
Write-Host "First request (API): $($time1.TotalSeconds)s"
Write-Host "Cached request: $($time2.TotalSeconds)s"
Write-Host "Speed improvement: $([math]::Round($time1.TotalSeconds / $time2.TotalSeconds, 1))x faster"
