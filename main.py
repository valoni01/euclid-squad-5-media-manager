from app.ui import build_app
from dotenv import load_dotenv
load_dotenv()

app = build_app()

if __name__ == "__main__":
    app.launch()