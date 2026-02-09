# Complete Engine Test - Server Version (Schema Fixed)
# Uses temp files for JSON with correct schema

$apiKey = "n9MglUvVhYaF4jhq5I5QGaBQlCDFjwPZdU6xE9_fu6U"
$baseUrl = "https://imslegitimacyengine.onrender.com"
$passed = 0
$failed = 0

function Test-Endpoint {
    param($name, $result, $expectedKey)
    if ($result -match $expectedKey) {
        Write-Host "[PASS] $name" -ForegroundColor Green
        return 1
    }
    else {
        Write-Host "[FAIL] $name" -ForegroundColor Red
        return 0
    }
}

Clear-Host
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "   SERVER TEST: $baseUrl" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# 1. Health Check
Write-Host "1. HEALTH CHECK" -ForegroundColor Yellow
$r = curl.exe -s "$baseUrl/"
Write-Host $r
if (Test-Endpoint "Health" $r "active") { $passed++ } else { $failed++ }

# 2. Parse Offer Letter
Write-Host "`n2. PARSE OFFER LETTER" -ForegroundColor Yellow
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Offer at DataTech Solutions Pvt Ltd. Role: Data Engineer. Stipend: 30000. HR: hiring@datatech.io, Amit Patel. Mumbai, India." `
    -F "student_programme=BTech IT"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $($time)s"
Write-Host ($r | Select-Object -First 200)
if (Test-Endpoint "Offer" $r "name") { $passed++ } else { $failed++ }

# 3. Relevance Check
Write-Host "`n3. RELEVANCE CHECK" -ForegroundColor Yellow
$r = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Software Developer at TechCorp India Pvt Ltd. HR: hr@techcorp.in, John Doe. Bangalore, India." `
    -F "student_programme=BTech Computer Science"
Write-Host ($r | Select-Object -First 200)
if (Test-Endpoint "Relevance" $r "relevance") { $passed++ } else { $failed++ }

# 4. Company Verification
Write-Host "`n4. COMPANY VERIFICATION" -ForegroundColor Yellow
$jsonFile = "$env:TEMP\verify.json"
@'
{"name":"Infosys Limited","country":"India","hr_name":"HR Team","hr_email":"careers@infosys.com","registry_id":"L85110KA1981PLC004418","website_urls":["https://www.infosys.com"]}
'@ | Out-File -FilePath $jsonFile -Encoding utf8 -NoNewline
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/verify" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    --data-binary "@$jsonFile"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $($time)s"
Write-Host ($r | Select-Object -First 200)
if (Test-Endpoint "Verify" $r "status") { $passed++ } else { $failed++ }

# 5. Faculty Allocation (FIXED: department + expertise as list)
Write-Host "`n5. FACULTY ALLOCATION" -ForegroundColor Yellow
$jsonFile = "$env:TEMP\alloc.json"
@'
{"student":{"id":"S001","name":"Test Student","internship_role":"ML Engineer","internship_description":"Building ML models for predictions","skills":["Python","TensorFlow"]},"available_faculty":[{"id":"F001","name":"Dr. Ramesh","department":"Computer Science","expertise":["Machine Learning","Deep Learning"],"current_load":3,"max_capacity":8}]}
'@ | Out-File -FilePath $jsonFile -Encoding utf8 -NoNewline
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/allocation/recommend" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    --data-binary "@$jsonFile"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $($time)s"
Write-Host ($r | Select-Object -First 200)
if (Test-Endpoint "Allocation" $r "faculty") { $passed++ } else { $failed++ }

# 6. Validate Pair (FIXED: expertise as list)
Write-Host "`n6. VALIDATE PAIR" -ForegroundColor Yellow
$jsonFile = "$env:TEMP\pair.json"
@'
{"student":{"internship_role":"Data Scientist","internship_description":"Building ML models"},"faculty":{"expertise":["Machine Learning","Data Science"]}}
'@ | Out-File -FilePath $jsonFile -Encoding utf8 -NoNewline
$r = curl.exe -s -X POST "$baseUrl/verification/allocation/validate-pair" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    --data-binary "@$jsonFile"
Write-Host $r
if (Test-Endpoint "Pair" $r "valid") { $passed++ } else { $failed++ }

# 7. History
Write-Host "`n7. VERIFICATION HISTORY" -ForegroundColor Yellow
$r = curl.exe -s -X GET "$baseUrl/verification/history" `
    -H "Legitimacy-engine-key: $apiKey"
Write-Host $r
if (Test-Endpoint "History" $r "history") { $passed++ } else { $failed++ }

# 8. Cache Test
Write-Host "`n8. CACHE TEST" -ForegroundColor Yellow
Write-Host "First request..."
$start1 = Get-Date
curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Cache test: Dev at CacheCorp India. HR: hr@cache.io, Test. India." `
    -F "student_programme=BTech CS" | Out-Null
$time1 = ((Get-Date) - $start1).TotalSeconds

Write-Host "Second request (cached)..."
$start2 = Get-Date
curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Cache test: Dev at CacheCorp India. HR: hr@cache.io, Test. India." `
    -F "student_programme=BTech CS" | Out-Null
$time2 = ((Get-Date) - $start2).TotalSeconds

Write-Host "First: $($time1)s | Cached: $($time2)s"
if ($time2 -lt $time1) { $passed++; Write-Host "[PASS] Cache" -ForegroundColor Green } else { $failed++ }

# Cleanup
Remove-Item "$env:TEMP\verify.json" -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\alloc.json" -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\pair.json" -ErrorAction SilentlyContinue

# Summary
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
if ($failed -eq 0) {
    Write-Host "   ALL TESTS PASSED: $passed/$passed" -ForegroundColor Green
}
else {
    Write-Host "   RESULTS: $passed PASSED, $failed FAILED" -ForegroundColor Yellow
}
Write-Host ("=" * 60) -ForegroundColor Cyan
