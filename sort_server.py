from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal
import time
from sort.heap_sort import heap_sort
from sort.merge_sort import merge_sort
from sort.quick_sort import quick_sort
from sort.insertion_sort import insertion_sort

app = FastAPI(title="Sorting Algorithms API")

class SortRequest(BaseModel):
    array: List[int]
    algorithm: Literal["heap", "merge", "quick", "insertion"]

class SortResponse(BaseModel):
    original_array: List[int]
    sorted_array: List[int]
    execution_time_ms: float
    is_sorted: bool
    algorithm: str

@app.post("/sort", response_model=SortResponse)
async def sort_array(request: SortRequest):
    try:
        # Create a copy for sorting
        arr_copy = request.array.copy()
        
        # Select algorithm
        if request.algorithm == "heap":
            sort_func = heap_sort
            algo_name = "Heap Sort"
        elif request.algorithm == "merge":
            sort_func = merge_sort
            algo_name = "Merge Sort"
        elif request.algorithm == "quick":
            sort_func = quick_sort
            algo_name = "Quick Sort"
        else:
            sort_func = insertion_sort
            algo_name = "Insertion Sort"
        
        # Measure execution time
        start_time = time.perf_counter()
        sorted_arr = sort_func(arr_copy)
        end_time = time.perf_counter()
        
        # Calculate execution time
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify sort
        is_sorted = all(sorted_arr[i] <= sorted_arr[i+1] for i in range(len(sorted_arr)-1))
        
        return SortResponse(
            original_array=request.array,
            sorted_array=sorted_arr,
            execution_time_ms=round(execution_time, 5),
            is_sorted=is_sorted,
            algorithm=algo_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 