# F1 Predictor

A Formula 1 prediction game built as a CMPT 354 database project. Users sign up, pick the top 3 podium finishers and whether a safety car will appear for a race, then see how their prediction scores against randomly generated bot players. Race results and user scores are persisted in a Supabase (PostgreSQL) database.

## Tech Stack

- **Frontend:** React + Vite
- **Backend:** Python / Flask
- **Database:** Supabase (PostgreSQL)

---

## Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Supabase project with the required tables

### 1. Clone the repo

```bash
git clone <repo-url>
cd F1-Predictor
```

### 2. Set up the backend

```bash
cd backend
```

Create a virtual environment and activate it:

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder (copy from the example):

```bash
cp .env.example .env
```

Fill in your Supabase credentials:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Start the Flask server:

```bash
python main.py
```

The backend runs on `http://localhost:5000`.

### 3. Set up the frontend

Open a new terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API requests to the Flask backend.

---

## Usage

1. Sign up for an account
2. Select a race from the sidebar dropdown
3. Go to **Make Prediction** and pick your P1, P2, P3, and safety car guess
4. Go to **View Results** to see how you scored against the bots
5. Check the **Global Leaderboard** to see overall standings

---

## Note

1. For the sake of this project, users are only predicting on the 10 most recent Grand Prix weekends. (Since it is hard to test on live races).
2. To make it seem more realistic, "View Predictions" generate dummy predictions but is NOT recorded on the database.
3. Safety Cars results are not stored on the Jolpica API. Thus, Safety Car results had a 50% chance of being either yes or no when race results were importing.