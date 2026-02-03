import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Induraavi%401929@localhost:5432/pptbuilder",
)
