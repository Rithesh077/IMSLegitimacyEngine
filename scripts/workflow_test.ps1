# Complete Workflow Test (PowerShell)
# Tests all endpoints with timing

$apiKey = "n9MglUvVhYaF4jhq5I5QGaBQlCDFjwPZdU6xE9_fu6U"
$baseUrl = "http://localhost:8001"

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "   COMPLETE WORKFLOW TEST" -ForegroundColor Cyan
Write-Host "===============================================`n"

# 1. Health Check
Write-Host "1. HEALTH CHECK" -ForegroundColor Yellow
$health = curl.exe -s "$baseUrl/"
Write-Host $health -ForegroundColor Green

# 2. Parse Offer Letter (File Upload)
Write-Host "`n2. PARSE OFFER LETTER (File Upload)" -ForegroundColor Yellow
$start = Get-Date
$offerResult = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "file=@inputs/dummy_offer.txt" `
    -F "student_programme=BSc Computer Science, Statistics and Mathematics"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $offerResult

# 3. Parse Offer Letter (Text Input)
Write-Host "`n3. PARSE OFFER LETTER (Text Input)" -ForegroundColor Yellow
$start = Get-Date
$offerText = curl.exe -s -X POST "$baseUrl/verification/parse/offer-letter" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "offer_text=Offer of employment at DataTech Solutions. Role: Data Engineer. Stipend: 30000/month. HR: hiring@datatech.io, Amit Patel. Location: Mumbai, India." `
    -F "student_programme=BTech Information Technology"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $offerText

# 4. Parse Recruiter Registration
Write-Host "`n4. PARSE RECRUITER REGISTRATION" -ForegroundColor Yellow
$start = Get-Date
$recruiter = curl.exe -s -X POST "$baseUrl/verification/parse/recruiter-registration" `
    -H "Legitimacy-engine-key: $apiKey" `
    -F "file=@inputs/dummy_doc.txt"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $recruiter

# 5. Company Verification
Write-Host "`n5. COMPANY VERIFICATION" -ForegroundColor Yellow
$start = Get-Date
$verify = curl.exe -s -X POST "$baseUrl/verification/verify" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    -d '{"name": "Infosys Limited", "country": "India", "hr_name": "HR Team", "hr_email": "careers@infosys.com", "registry_id": "L85110KA1981PLC004418", "website_urls": ["https://www.infosys.com"]}'
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $verify

# 6. Faculty Allocation Recommend
Write-Host "`n6. FACULTY ALLOCATION RECOMMEND" -ForegroundColor Yellow
$start = Get-Date
$allocBody = '{"student": {"id": "S001", "name": "Test Student", "internship_role": "ML Engineer", "internship_description": "Building ML models", "skills": ["Python", "TensorFlow"]}, "available_faculty": [{"id": "F001", "name": "Dr. Ramesh", "expertise": "Machine Learning", "current_load": 3, "max_capacity": 8}, {"id": "F002", "name": "Dr. Priya", "expertise": "Data Mining", "current_load": 5, "max_capacity": 6}]}'
$alloc = curl.exe -s -X POST "$baseUrl/verification/allocation/recommend" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    -d $allocBody
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $alloc

# 7. Validate Manual Pair
Write-Host "`n7. VALIDATE MANUAL PAIR" -ForegroundColor Yellow
$start = Get-Date
$pairBody = '{"student": {"internship_role": "Web Developer", "internship_description": "React development"}, "faculty": {"expertise": "Web Technologies"}}'
$pair = curl.exe -s -X POST "$baseUrl/verification/allocation/validate-pair" `
    -H "Legitimacy-engine-key: $apiKey" `
    -H "Content-Type: application/json" `
    -d $pairBody
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $pair

# 8. Get History
Write-Host "`n8. GET VERIFICATION HISTORY" -ForegroundColor Yellow
$start = Get-Date
$history = curl.exe -s -X GET "$baseUrl/verification/history" `
    -H "Legitimacy-engine-key: $apiKey"
$time = ((Get-Date) - $start).TotalSeconds
Write-Host "Time: $time seconds" -ForegroundColor Cyan
Write-Host $history

Write-Host "`n===============================================" -ForegroundColor Green
Write-Host "   ALL TESTS COMPLETE" -ForegroundColor Green
Write-Host "===============================================`n"
