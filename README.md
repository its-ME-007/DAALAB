# Algorithm Runtime Visualizer

A web-based application for running algorithms and visualizing their runtime performance. The application allows users to input algorithm code, run it, and see the runtime performance visualized over time.

## Features

- Run any Python algorithm code
- Measure and display runtime performance
- Visualize runtime history using interactive charts
- Store runtime data in Supabase database
- Modern, responsive UI

## Prerequisites

- Python 3.7+
- Node.js (for serving the frontend)
- Supabase account and project

## Setup

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

4. Set up the database:
   - Create a new Supabase project
   - Run the SQL commands from `schema.sql` in your Supabase SQL editor

5. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

6. Serve the frontend:
   You can use any static file server. For example, using Python's built-in server:
   ```bash
   cd frontend
   python -m http.server 8000
   ```

7. Open your browser and navigate to `http://localhost:8000`

## Usage

1. Enter an algorithm name
2. Input the size of the test data
3. Write your algorithm code in the editor
4. Click "Run Algorithm" to execute
5. View the runtime results and visualization

## Security Notes

- The application uses a sandboxed environment for code execution
- Only basic Python built-ins are available for security
- Consider adding additional security measures for production use

## Project Structure

```
.
├── backend/
│   └── app.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── requirements.txt
├── schema.sql
└── README.md
```

## Contributing

Feel free to submit issues and enhancement requests! 