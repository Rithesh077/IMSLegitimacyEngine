# Local Testing Commands (PowerShell)

Replace `your_api_key` with your actual `API_ACCESS_KEY` from `.env`

## Health Check (No Auth)
```powershell
curl.exe http://localhost:8001/
```

## Parse Offer Letter (with file)
```powershell
curl.exe -X POST "http://localhost:8001/verification/parse/offer-letter" -H "Legitimacy-engine-key: your_api_key" -F "file=@inputs/dummy_offer.txt" -F "student_programme=Bachelor of Science in Computer Science, Statistics and Mathematics"
```

## Parse Offer Letter (with text)
```powershell
curl.exe -X POST "http://localhost:8001/verification/parse/offer-letter" -H "Legitimacy-engine-key: your_api_key" -F "offer_text=Dear Student, We are pleased to offer you the position of Software Developer Intern at TechCorp India Pvt Ltd. Role: Backend Developer. Stipend: 15000/month. HR Contact: hr@techcorp.in, Rahul Sharma. Location: Bangalore, India." -F "student_programme=BTech Computer Science and Engineering"
```

## Parse Recruiter Registration
```powershell
curl.exe -X POST "http://localhost:8001/verification/parse/recruiter-registration" -H "Legitimacy-engine-key: your_api_key" -F "file=@inputs/dummy_doc.txt"
```

## Verify Company
```powershell
curl.exe -X POST "http://localhost:8001/verification/verify" -H "Legitimacy-engine-key: your_api_key" -H "Content-Type: application/json" -d "{\"name\": \"Infosys Limited\", \"country\": \"India\", \"hr_name\": \"HR Team\", \"hr_email\": \"careers@infosys.com\", \"registry_id\": \"L85110KA1981PLC004418\", \"website_urls\": [\"https://www.infosys.com\"]}"
```

## Get Verification History
```powershell
curl.exe -X GET "http://localhost:8001/verification/history" -H "Legitimacy-engine-key: your_api_key"
```

## Faculty Allocation Recommend
```powershell
curl.exe -X POST "http://localhost:8001/verification/allocation/recommend" -H "Legitimacy-engine-key: your_api_key" -H "Content-Type: application/json" -d "{\"student\": {\"id\": \"S001\", \"name\": \"John Doe\", \"internship_role\": \"Data Analyst\", \"internship_description\": \"Building ML models for customer segmentation\", \"skills\": [\"Python\", \"SQL\", \"Machine Learning\"]}, \"available_faculty\": [{\"id\": \"F001\", \"name\": \"Dr. Ramesh Kumar\", \"expertise\": \"Machine Learning, Deep Learning\", \"current_load\": 3, \"max_capacity\": 8}, {\"id\": \"F002\", \"name\": \"Dr. Priya Singh\", \"expertise\": \"Statistics, Data Mining\", \"current_load\": 5, \"max_capacity\": 6}]}"
```

## Validate Manual Pair
```powershell
curl.exe -X POST "http://localhost:8001/verification/allocation/validate-pair" -H "Legitimacy-engine-key: your_api_key" -H "Content-Type: application/json" -d "{\"student\": {\"internship_role\": \"Web Developer\", \"internship_description\": \"Frontend React development\"}, \"faculty\": {\"expertise\": \"Software Engineering, Web Technologies\"}}"
```
