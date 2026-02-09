import random
from app.schemas.allocation import AllocationRequest, AllocationResponse
from app.engine.factory import get_ai_provider

class AllocationEngine:
    """handles faculty-student allocation based on expertise matching."""
    
    def __init__(self):
        self.ai = get_ai_provider()

    def allocate(self, request: AllocationRequest) -> AllocationResponse:
        """allocates best faculty to student based on internship match."""
        student_data = request.student.model_dump()
        faculty_data = [f.model_dump() for f in request.available_faculty]
        
        ai_res = self.ai.match_guide(student_data, faculty_data)
        matches = ai_res.get("ranked_matches", [])
        
        best_candidate = None
        highest_score = -1
        final_reasoning = "no suitable faculty found."
        is_random = False

        if matches:
            for m in matches:
                fac_id = m.get("faculty_id")
                expertise_score = float(m.get("expertise_score", 0))
                
                faculty = next((f for f in request.available_faculty if f.id == fac_id), None)
                if not faculty: continue

                if faculty.max_capacity > 0:
                    workload_score = ((faculty.max_capacity - faculty.current_load) / faculty.max_capacity) * 100
                    workload_score = max(0, workload_score)
                else:
                    workload_score = 0

                # weighted: 80% expertise, 20% workload
                final_score = (expertise_score * 0.8) + (workload_score * 0.2)
                
                if final_score > highest_score:
                    highest_score = final_score
                    best_candidate = faculty
                    final_reasoning = f"{m.get('reasoning')} | expertise: {expertise_score}, load: {faculty.current_load}/{faculty.max_capacity}"

        # fallback if scores too low or ai failed
        if not best_candidate or highest_score < 40:
             available = [f for f in request.available_faculty if f.current_load < f.max_capacity]
             if available:
                 best_candidate = random.choice(available)
                 is_random = True
                 final_reasoning = "fallback: random selection due to low ai confidence or full capacity."
                 highest_score = 0
             else:
                 final_reasoning = "all faculty are at full capacity."

        # collect alternatives (top 3 excluding best)
        alternatives = []
        if matches:
            sorted_matches = sorted(matches, key=lambda x: float(x.get('expertise_score', 0)), reverse=True)
            for m in sorted_matches:
                 if best_candidate and m.get('faculty_id') == best_candidate.id:
                     continue
                 if len(alternatives) >= 3: 
                     break
                 
                 fname = m.get('faculty_name', 'unknown')
                 if not fname or fname == "unknown":
                     fac = next((f for f in request.available_faculty if f.id == m.get('faculty_id')), None)
                     if fac: fname = fac.name
                 
                 alternatives.append({
                     "faculty_id": m.get('faculty_id'),
                     "faculty_name": fname,
                     "score": round(float(m.get('expertise_score', 0)), 1)
                 })

        if best_candidate:
            return AllocationResponse(
                recommended_faculty_id=best_candidate.id,
                faculty_name=best_candidate.name,
                confidence_score=round(highest_score, 1),
                reasoning=final_reasoning,
                is_random_fallback=is_random,
                alternatives=alternatives
            )
        else:
            return AllocationResponse(
                recommended_faculty_id="NONE",
                faculty_name="NONE",
                confidence_score=0,
                reasoning=final_reasoning,
                is_random_fallback=True,
                alternatives=alternatives
            )

    def validate_pair(self, student: dict, faculty: dict) -> dict:
        """validates a specific student-faculty pair (manual override check)."""
        prompt = f"""
validate if this faculty is suitable for this student's internship.

student: {student.get('internship_role')} - {student.get('internship_description')}
faculty expertise: {faculty.get('expertise')}

output json:
{{
    "is_suitable": true/false,
    "score": 0-100,
    "warning": "str if any",
    "reasoning": "brief explanation"
}}
"""
        return self.ai._generate_with_fallback(prompt)
