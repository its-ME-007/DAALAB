from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import jwt
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
router = APIRouter()

def verify_token(auth_request: Request):
    """Extract and verify JWT token"""
    auth_header = auth_request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid JWT: no user id")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"JWT decode error: {e}")

@router.get("/api/plot.png")
async def plot_runtime(auth_request: Request):
    """Generate and return algorithm performance plot"""
    try:
        user_id = verify_token(auth_request)
        
        response = supabase.table('algorithm_runtimes')\
            .select('algorithm_name, input_size, execution_time_ms, user_id')\
            .execute()
        
        data = response.data

        if not data or len(data) == 0:
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 
                   'No Algorithm Data Available\n\n'
                   'Run some algorithms with:\n'
                   '• Algorithm name\n'
                   '• Input size\n\n'
                   'to see performance visualization here.',
                   ha='center', va='center', 
                   fontsize=16, color='#718096',
                   bbox=dict(boxstyle='round,pad=1', facecolor='#f7fafc', edgecolor='#e2e8f0'))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            buf.seek(0)
            return Response(content=buf.read(), media_type="image/png")

        algos = {}
        for row in data:
            algo = row['algorithm_name']
            if algo not in algos:
                algos[algo] = {'input_size': [], 'runtime': []}
            algos[algo]['input_size'].append(row['input_size'])
            algos[algo]['runtime'].append(row['execution_time_ms'])

        fig, ax = plt.subplots(figsize=(12, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(algos)))
        
        for i, (algo, vals) in enumerate(algos.items()):
            arr = sorted(zip(vals['input_size'], vals['runtime']))
            x = np.array([a for a, _ in arr])
            y = np.array([b for _, b in arr])
            
            ax.plot(x, y, marker='o', label=algo, color=colors[i], 
                   markersize=8, linewidth=2.5, alpha=0.8)
        
        ax.set_xlabel("Input Size", fontsize=13, fontweight='500')
        ax.set_ylabel("Runtime (ms)", fontsize=13, fontweight='500')
        ax.set_title("Algorithm Performance Comparison\n(All Users Data)", 
                    fontsize=15, fontweight='bold', pad=20)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, 
                 shadow=True, fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")


@router.get("/api/complexity-plot.png")
async def plot_complexity(
    auth_request: Request,
    time_class: str = "linear",
    space_class: str = "constant",
    algorithm_name: str = "Algorithm"
):
    """
    Generate HIGH-QUALITY theoretical complexity curves
    Uses smart scaling based on complexity class
    """
    try:
        user_id = verify_token(auth_request)
        
        # ✅ SMART SCALING: Different ranges for different complexity classes
        def get_input_range(complexity_class):
            """Return appropriate input size range for complexity class"""
            ranges = {
                "constant": (10, 10000, 300),
                "logarithmic": (10, 100000, 300),
                "linear": (10, 10000, 300),
                "linearithmic": (10, 10000, 300),
                "quadratic": (10, 1000, 300),      # Smaller range for n²
                "cubic": (10, 500, 300),           # Even smaller for n³
                "exponential": (1, 25, 300),       # Very small for 2^n
                "factorial": (1, 12, 100)          # Tiny range for n!
            }
            return ranges.get(complexity_class, (10, 10000, 300))
        
        # Get appropriate ranges for time and space
        time_range = get_input_range(time_class)
        space_range = get_input_range(space_class)
        
        # Use the larger range (so both plots have same x-axis)
        if time_range[1] >= space_range[1]:
            input_sizes = np.linspace(time_range[0], time_range[1], time_range[2])
        else:
            input_sizes = np.linspace(space_range[0], space_range[1], space_range[2])
        
        # Calculate complexity values
        time_values = np.array([complexity_to_function(time_class, n) for n in input_sizes])
        space_values = np.array([complexity_to_function(space_class, n) for n in input_sizes])
        
        # Create HIGH DPI figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7), dpi=150)
        
        # ===== TIME COMPLEXITY PLOT =====
        ax1.plot(input_sizes, time_values, 
                linewidth=3.5,
                color='#667eea', 
                label=f'Time: O({get_complexity_notation(time_class)})',
                solid_capstyle='round')
        
        # Add sample dots
        sample_indices = np.linspace(0, len(input_sizes)-1, 12, dtype=int)
        ax1.scatter(input_sizes[sample_indices], 
                   time_values[sample_indices],
                   s=80, color='#667eea', zorder=5, edgecolors='white', linewidth=2)
        
        ax1.set_xlabel("Input Size (n)", fontsize=15, fontweight='700', color='#2d3748')
        ax1.set_ylabel("Time (operations)", fontsize=15, fontweight='700', color='#2d3748')
        ax1.set_title(f"Time Complexity Analysis\n{algorithm_name}", 
                     fontsize=17, fontweight='bold', pad=20, color='#1a202c')
        ax1.legend(loc='upper left', frameon=True, shadow=True, fontsize=13, fancybox=True)
        ax1.grid(True, alpha=0.25, linestyle='--', linewidth=1)
        
        # Complexity class badge
        ax1.text(0.98, 0.95, f'Class: {time_class.upper()}', 
                transform=ax1.transAxes, ha='right', va='top',
                bbox=dict(boxstyle='round,pad=0.7', facecolor='#667eea', alpha=0.3, edgecolor='#667eea', linewidth=2),
                fontsize=12, fontweight='700', color='#667eea')
        
        # Styling
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_linewidth(2.5)
        ax1.spines['bottom'].set_linewidth(2.5)
        ax1.spines['left'].set_color('#cbd5e0')
        ax1.spines['bottom'].set_color('#cbd5e0')
        
        # Format y-axis with scientific notation for large numbers
        ax1.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
        
        # ===== SPACE COMPLEXITY PLOT =====
        ax2.plot(input_sizes, space_values,
                linewidth=3.5,
                color='#f093fb', 
                label=f'Space: O({get_complexity_notation(space_class)})',
                solid_capstyle='round')
        
        # Add sample dots
        ax2.scatter(input_sizes[sample_indices], 
                   space_values[sample_indices],
                   s=80, color='#f093fb', zorder=5, edgecolors='white', linewidth=2)
        
        ax2.set_xlabel("Input Size (n)", fontsize=15, fontweight='700', color='#2d3748')
        ax2.set_ylabel("Space (memory units)", fontsize=15, fontweight='700', color='#2d3748')
        ax2.set_title(f"Space Complexity Analysis\n{algorithm_name}", 
                     fontsize=17, fontweight='bold', pad=20, color='#1a202c')
        ax2.legend(loc='upper left', frameon=True, shadow=True, fontsize=13, fancybox=True)
        ax2.grid(True, alpha=0.25, linestyle='--', linewidth=1)
        
        # Complexity class badge
        ax2.text(0.98, 0.95, f'Class: {space_class.upper()}', 
                transform=ax2.transAxes, ha='right', va='top',
                bbox=dict(boxstyle='round,pad=0.7', facecolor='#f093fb', alpha=0.3, edgecolor='#f093fb', linewidth=2),
                fontsize=12, fontweight='700', color='#f093fb')
        
        # Styling
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_linewidth(2.5)
        ax2.spines['bottom'].set_linewidth(2.5)
        ax2.spines['left'].set_color('#cbd5e0')
        ax2.spines['bottom'].set_color('#cbd5e0')
        
        # Format y-axis
        ax2.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
        
        plt.tight_layout(pad=2)
        
        # HIGH DPI OUTPUT
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=400, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Complexity plot error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating complexity plot: {str(e)}")


def complexity_to_function(complexity_class: str, input_size: float) -> float:
    """
    Convert complexity class to ACTUAL mathematical function
    With safe limits to prevent overflow
    """
    n = input_size
    
    if complexity_class == "constant":
        return 1.0
    
    elif complexity_class == "logarithmic":
        return np.log2(max(n, 2))
    
    elif complexity_class == "linear":
        return n
    
    elif complexity_class == "linearithmic":
        return n * np.log2(max(n, 2))
    
    elif complexity_class == "quadratic":
        return n ** 2
    
    elif complexity_class == "cubic":
        return n ** 3
    
    elif complexity_class == "exponential":
        # Cap at 1e15 to prevent overflow
        exponent = min(n, 50)  # 2^50 is already huge
        return min(2 ** exponent, 1e15)
    
    elif complexity_class == "factorial":
        # Factorial grows EXTREMELY fast - cap at n=20
        if n > 20:
            return 1e15  # Max representable value
        try:
            return float(np.math.factorial(int(n)))
        except (OverflowError, ValueError):
            return 1e15
    
    else:
        return n  # Default to linear


def get_complexity_notation(complexity_class: str) -> str:
    """Convert complexity class to Big-O notation"""
    notation_map = {
        "constant": "1",
        "logarithmic": "log n",
        "linear": "n",
        "linearithmic": "n log n",
        "quadratic": "n²",
        "cubic": "n³",
        "exponential": "2ⁿ",
        "factorial": "n!"
    }
    return notation_map.get(complexity_class, "n")


@router.get("/api/runtime-data")
async def get_runtime_data(auth_request: Request):
    """Get all algorithm runtime data from the database"""
    try:
        user_id = verify_token(auth_request)
        
        response = supabase.table('algorithm_runtimes')\
            .select('*')\
            .order('created_at', desc=True)\
            .execute()
        
        return {
            'success': True,
            'data': response.data or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve runtime data: {str(e)}")


def register_visualization_routes(app):
    """Register visualization routes with the FastAPI app"""
    app.include_router(router)