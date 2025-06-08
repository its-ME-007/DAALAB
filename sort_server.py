from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import time
from heap_sort import heap_sort

app = FastAPI(title="Heap Sort API")

class SortRequest(BaseModel):
    array: List[int]

class SortResponse(BaseModel):
    original_array: List[int]
    sorted_array: List[int]
    execution_time_ms: float
    is_sorted: bool

@app.post("/sort", response_model=SortResponse)
async def sort_array(request: SortRequest):
    try:
        # Create a copy for sorting
        arr_copy = request.array.copy()
        
        # Measure execution time
        start_time = time.perf_counter()
        sorted_arr = heap_sort(arr_copy)
        end_time = time.perf_counter()
        
        # Calculate execution time
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify sort
        is_sorted = all(sorted_arr[i] <= sorted_arr[i+1] for i in range(len(sorted_arr)-1))
        
        return SortResponse(
            original_array=request.array,
            sorted_array=sorted_arr,
            execution_time_ms=round(execution_time, 5),
            is_sorted=is_sorted
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 