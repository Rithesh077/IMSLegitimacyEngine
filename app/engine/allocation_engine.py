import random
from app.schemas.allocation import AllocationRequest, AllocationResponse
from app.engine.factory import get_ai_provider

class AllocationEngine:
    def __init__(self):
        self.ai = get_ai_provider()

    def allocate(self, request: AllocationRequest) -> AllocationResponse:
        # convert pydantic to json for ai
        student_data = request.student.model_dump()
        faculty_data = [f.model_dump() for f in request.available_faculty]
        
        # 1. ai match (returns ranked list)
        ai_res = self.ai.match_guide(student_data, faculty_data)
        matches = ai_res.get("ranked_matches", [])
        
        best_candidate = None
        highest_score = -1
        final_reasoning = "No suitable faculty found."
        is_random = False

        # 2. scoring logic
        if matches:
            for m in matches:
                fac_id = m.get("faculty_id")
                expertise_score = float(m.get("expertise_score", 0))
                
                # find faculty object
                faculty = next((f for f in request.available_faculty if f.id == fac_id), None)
                if not faculty: continue

                # workload score (0 if full, 100 if empty)
                if faculty.max_capacity > 0:
                    workload_score = ((faculty.max_capacity - faculty.current_load) / faculty.max_capacity) * 100
                    workload_score = max(0, workload_score) # prevent negative
                else:
                    workload_score = 0

                # Weighted Formula: 80% Expertise, 20% Workload
                final_score = (expertise_score * 0.8) + (workload_score * 0.2)
                
                if final_score > highest_score:
                    highest_score = final_score
                    best_candidate = faculty
                    final_reasoning = f"{m.get('reasoning')} | Expertise: {expertise_score}, Load: {faculty.current_load}/{faculty.max_capacity}"

        # 3. fallback if scores are too low or ai failed
        if not best_candidate or highest_score < 40:
             # try to find anyone with capacity
             available = [f for f in request.available_faculty if f.current_load < f.max_capacity]
             if available:
                 best_candidate = random.choice(available)
                 is_random = True
                 final_reasoning = "Fallback: Random selection due to low AI confidence or full capacity."
                 highest_score = 0
             else:
                 final_reasoning = "All faculty are at full capacity."

        # 4. collect alternatives (top 3 excluding best)
        alternatives = []
        if matches:
            sorted_matches = sorted(matches, key=lambda x: float(x.get('expertise_score', 0)), reverse=True)
            for m in sorted_matches:
                 if best_candidate and m.get('faculty_id') == best_candidate.id:
                     continue
                 if len(alternatives) >= 3: 
                     break
                 
                 # find faculty name to be safe
                 fname = m.get('faculty_name', 'Unknown')
                 if not fname or fname == "Unknown":
                     fac = next((f for f in request.available_faculty if f.id == m.get('faculty_id')), None)
                     if fac: fname = fac.name
                 
                 alternatives.append({
                     "faculty_id": m.get('faculty_id'),
                     "faculty_name": fname,
                     "score": round(float(m.get('expertise_score', 0)), 1)
                 })

        # 5. form response
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
        """
        Validates a specific student-faculty pair (Manual Override Check).
        """
        # Quick AI check
        prompt = f"""
        Act as Academic Coordinator. Validate if this Faculty is suitable for this Student Internship.
        
        STUDENT: {student.get('internship_role')} - {student.get('internship_description')}
        FACULTY EXPERTISE: {faculty.get('expertise')}
        
        OUTPUT JSON:
        {{
            "is_suitable": bool,
            "score": int (0-100),
            "warning": "str (if any)",
            "reasoning": "brief explanation"
        }}
        """
        return self.ai._generate_with_fallback(prompt)
