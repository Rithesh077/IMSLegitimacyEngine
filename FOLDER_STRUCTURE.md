# folder structure

here is what goes where. keep it clean.

## backend/
python logic.

*   **app/engine/**: put your scraping scripts (`scraper.py`), analysis logic (`analyzer.py`), and verification rules here.
*   **app/schemas/**: define what your inputs/outputs look like using pydantic models (`company.py`).
*   **run_engine.py**: script to test your engine without a server.
*   **requirements.txt**: libraries you need (pip install).

## frontend/
reactjs ui. (**note: currently empty. will be started from scratch.**)

*   **app/**: pages. `page.tsx` is the main view. one folder = one route.
*   **components/**: ui parts. button, cards, inputs. things you reuse.
*   **services/**: api calls. function that talk to the backend/external apis.
*   **types/**: typescript interfaces. definitions for your data objects.
