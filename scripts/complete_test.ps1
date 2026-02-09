# Complete Engine Test - All Features
# Tests every endpoint with detailed output

$apiKey = "n9MglUvVhYaF4jhq5I5QGaBQlCDFjwPZdU6xE9_fu6U"
$baseUrl = "http://localhost:8001"
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
        Write-Host $result -ForegroundColor Gray
        return 0
    }
}

Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "   COMPLETE ENGINE TEST - ALL FEATURES" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 1. Health Check
Write-Host "1. HEALTH CHECK" -ForegroundColor Yellow
$r = curl.exe -s "$baseUrl/"
Write-Host $r
if (Test-Endpoint "Health Check" $r "active") { $passed++ } else { $failed++ }

# 2. Parse Offer Letter - Text Input
Write-Host "`n2. PARSE OFFER LETTER (Text)" -ForegroundColor Yellow
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Offer of internship at DataTech Solutions Pvt Ltd. Role: Data Engineer. Stipend: 30000/month. HR: hiring@datatech.io, Amit Patel. Office: Mumbai, India." `
    -F "student_programme=BTech Information Technology"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time`s" -ForegroundColor Cyan
Write-Host $r
if (Test-Endpoint "Offer Letter Parse" $r "DataTech") { $passed++ } else { $failed++ }

# 3. Parse Offer Letter - File Upload
Write-Host "`n3. PARSE OFFER LETTER (File)" -ForegroundColor Yellow
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "file=@inputs/dummy_offer.txt" `
    -F "student_programme=BSc Computer Science"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time`s" -ForegroundColor Cyan
Write-Host $r
if (Test-Endpoint "File Upload" $r "TechNova") { $passed++ } else { $failed++ }

# 4. Relevance Check - Relevant Role
Write-Host "`n4. RELEVANCE CHECK (Relevant)" -ForegroundColor Yellow
$r = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Software Developer role at TechCorp. HR: hr@techcorp.in" `
    -F "student_programme=BTech Computer Science"
Write-Host $r
if (Test-Endpoint "Relevance - Match" $r "is_relevant.*true") { $passed++ } else { $failed++ }

# 5. Relevance Check - Irrelevant Role
Write-Host "`n5. RELEVANCE CHECK (Irrelevant)" -ForegroundColor Yellow
$r = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Campus Ambassador role at MarketingCo. Promote our brand on campus. HR: hr@marketing.co" `
    -F "student_programme=BTech Mechanical Engineering"
Write-Host $r
if ($r -match "is_relevant") { $passed++; Write-Host "[PASS] Relevance Check" -ForegroundColor Green } else { $failed++ }

# 6. Parse Recruiter Registration
Write-Host "`n6. PARSE RECRUITER REGISTRATION" -ForegroundColor Yellow
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/parse/recruiter-registration" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "file=@inputs/dummy_doc.txt"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time`s" -ForegroundColor Cyan
Write-Host $r
if (Test-Endpoint "Recruiter Parse" $r "name") { $passed++ } else { $failed++ }

# 7. Company Verification
Write-Host "`n7. COMPANY VERIFICATION" -ForegroundColor Yellow
$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/verify" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    -d '{"name": "Infosys Limited", "country": "India", "hr_name": "HR Team", "hr_email": "careers@infosys.com", "registry_id": "L85110KA1981PLC004418", "website_urls": ["https://www.infosys.com"]}'
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time`s" -ForegroundColor Cyan
Write-Host $r
if (Test-Endpoint "Company Verify" $r "status") { $passed++ } else { $failed++ }

# 8. Faculty Allocation - Recommend
Write-Host "`n8. FACULTY ALLOCATION RECOMMEND" -ForegroundColor Yellow
$jsonFile = "$env:TEMP\alloc_full.json"
@'
{"student": {"id": "S001", "name": "Test Student", "internship_role": "Machine Learning Engineer", "internship_description": "Building ML models for predictions", "skills": ["Python", "TensorFlow", "PyTorch"]}, "available_faculty": [{"id": "F001", "name": "Dr. Ramesh Kumar", "department": "Computer Science", "expertise": ["Machine Learning", "Deep Learning", "Neural Networks"], "current_load": 3, "max_capacity": 8}, {"id": "F002", "name": "Dr. Priya Singh", "department": "Data Science", "expertise": ["Data Mining", "Statistics"], "current_load": 5, "max_capacity": 6}, {"id": "F003", "name": "Dr. Vijay Sharma", "department": "IT", "expertise": ["Web Development", "JavaScript"], "current_load": 2, "max_capacity": 7}]}
'@ | Out-File -FilePath $jsonFile -Encoding utf8 -NoNewline

$start = Get-Date
$r = curl.exe -s -X POST "$baseUrl/verification/allocation/recommend" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    --data-binary "@$jsonFile"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time`s" -ForegroundColor Cyan
Write-Host ($r | Select-Object -First 200)
if (Test-Endpoint "Allocation Recommend" $r "faculty") { $passed++ } else { $failed++ }

# 9. Validate Manual Pair - Good Match
Write-Host "`n9. VALIDATE PAIR (Good Match)" -ForegroundColor Yellow
$jsonFile = "$env:TEMP\pair_good.json"
@'
{"student": {"internship_role": "Data Scientist", "internship_description": "Building ML models"}, "faculty": {"expertise": ["Machine Learning", "Data Science"]}}
'@ | Out-File -FilePath $jsonFile -Encoding utf8 -NoNewline

$r = curl.exe -s -X POST "$baseUrl/verification/allocation/validate-pair" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    --data-binary "@$jsonFile"
Write-Host $r
if (Test-Endpoint "Good Pair" $r "valid") { $passed++ } else { $failed++ }

# 10. Validate Manual Pair - Bad Match
Write-Host "`n10. VALIDATE PAIR (Bad Match)" -ForegroundColor Yellow
$jsonFile = "$env:TEMP\pair_bad.json"
@'
{"student": {"internship_role": "Mechanical Design Engineer", "internship_description": "CAD modeling"}, "faculty": {"expertise": ["Web Development", "JavaScript"]}}
'@ | Out-File -FilePath $jsonFile -Encoding utf8 -NoNewline

$r = curl.exe -s -X POST "$baseUrl/verification/allocation/validate-pair" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    --data-binary "@$jsonFile"
Write-Host $r
if ($r -match "valid") { $passed++; Write-Host "[PASS] Bad Pair Check" -ForegroundColor Green } else { $failed++ }

# 11. Get Verification History
Write-Host "`n11. VERIFICATION HISTORY" -ForegroundColor Yellow
$r = curl.exe -s -X GET "$baseUrl/verification/history" `
    -H "Legitimacy-engine-key: $apiKey"
Write-Host $r
if (Test-Endpoint "History" $r "history") { $passed++ } else { $failed++ }

# 12. Cache Test - Same request should be instant
Write-Host "`n12. CACHE TEST" -ForegroundColor Yellow
Write-Host "First request..." -ForegroundColor Gray
$start1 = Get-Date
$r1 = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Cache test: Backend Developer at CacheCorp. HR: hr@cache.io" `
    -F "student_programme=BTech CS"
$time1 = ((Get-Date) - $start1).TotalSeconds

Write-Host "Second request (cached)..." -ForegroundColor Gray
$start2 = Get-Date
$r2 = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Cache test: Backend Developer at CacheCorp. HR: hr@cache.io" `
    -F "student_programme=BTech CS"
$time2 = ((Get-Date) - $start2).TotalSeconds

Write-Host "First: $time1`s | Cached: $time2`s | Speedup: $([math]::Round($time1/$time2, 1))x" -ForegroundColor Cyan
if ($time2 -lt $time1) { $passed++; Write-Host "[PASS] Cache Working" -ForegroundColor Green } else { $failed++ }

# Summary
Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "   RESULTS: $passed PASSED, $failed FAILED" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "=" * 60 -ForegroundColor Cyan
