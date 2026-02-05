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
        
        # 1. ai match
        ai_res = self.ai.match_guide(student_data, faculty_data)
        
        best_id = ai_res.get("best_faculty_id")
        score = float(ai_res.get("confidence_score", 0))
        reasoning = ai_res.get("reasoning", "AI Analysis Failed")
        
        # 2. decision logic (threshold 60)
        is_random = False
        selected_faculty = None
        
        # check if ai choice exists in available list
        candidate = next((f for f in request.available_faculty if f.id == best_id), None)
        
        if candidate and score >= 60:
            selected_faculty = candidate
        else:
            # fallback: random
            is_random = True
            if request.available_faculty:
                selected_faculty = random.choice(request.available_faculty)
                reasoning = f"fallback: random selection. (ai score {score} was too low or invalid)"
            else:
                reasoning = "no faculty available"
                
        # 3. form response
        if selected_faculty:
            return AllocationResponse(
                recommended_faculty_id=selected_faculty.id,
                faculty_name=selected_faculty.name,
                confidence_score=score if not is_random else 0,
                reasoning=reasoning,
                is_random_fallback=is_random
            )
        else:
            # edge case: no faculty provided
            return AllocationResponse(
                recommended_faculty_id="NONE",
                faculty_name="NONE",
                confidence_score=0,
                reasoning="No faculty provided in request",
                is_random_fallback=True
            )
