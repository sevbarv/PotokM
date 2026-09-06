from handlers.start import router as start_router
from handlers.mood import router as mood_router
from handlers.candidate import router as candidate_router
from handlers.employee import router as employee_router
from handlers.recruiter import router as recruiter_router

routers = [
    start_router,
    mood_router,
    candidate_router,
    employee_router,
    recruiter_router,
]
