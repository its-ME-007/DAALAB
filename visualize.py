from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import matplotlib.pyplot as plt
import numpy as np
import io
import jwt
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

router = APIRouter()

@router.get("/api/plot.png")
async def plot_runtime(auth_request: Request):
    # 1. Extract JWT from Authorization header
    auth_header = auth_request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid JWT: no user id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"JWT decode error: {e}")

    # 2. Fetch ALL runtime data from database (not just user-specific)
    response = supabase.table('algorithm_runtimes')\
        .select('algorithm_name, input_size, execution_time_ms, user_id')\
        .execute()
    data = response.data

    if not data:
        raise HTTPException(status_code=404, detail="No runtime data found")

    # 3. Prepare data for plotting - group by algorithm
    algos = {}
    for row in data:
        algo = row['algorithm_name']
        if algo not in algos:
            algos[algo] = {'input_size': [], 'runtime': [], 'user_id': []}
        algos[algo]['input_size'].append(row['input_size'])
        algos[algo]['runtime'].append(row['execution_time_ms'])
        algos[algo]['user_id'].append(row['user_id'])

    # 4. Create comprehensive plot
    plt.figure(figsize=(12, 8))
    
    # Generate distinct colors for algorithms
    colors = plt.cm.Set3(np.linspace(0, 1, len(algos)))
    
    for i, (algo, vals) in enumerate(algos.items()):
        # Sort by input size for each algorithm
        arr = sorted(zip(vals['input_size'], vals['runtime'], vals['user_id']))
        x = np.array([a for a, _, _ in arr])
        y = np.array([b for _, b, _ in arr])
        
        # Plot with different colors and markers
        plt.plot(x, y, marker='o', label=algo, color=colors[i], 
                markersize=6, linewidth=2, alpha=0.8)
    
    plt.xlabel("Input Size", fontsize=12)
    plt.ylabel("Runtime (ms)", fontsize=12)
    plt.title("Algorithm Performance Comparison\n(All Users Data)", fontsize=14, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # 5. Return as PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")

def register_visualization_routes(app):
    app.include_router(router) 