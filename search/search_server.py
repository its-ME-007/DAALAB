from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time

from linear_search import linear_search
from binary_search import binary_search
from interpolation_search import interpolation_search

app = FastAPI(title="Search Algorithms API")

class SearchRequest(BaseModel):
    array: List[int]
    target: int
    algorithm: str

class SearchResponse(BaseModel):
    array: List[int]
    target: int
    found_index: Optional[int]
    execution_time_ms: float
    algorithm: str
    message: str

@app.post("/search", response_model=SearchResponse)
async def search_array(request: SearchRequest):
    total_execution_time = 0.0
    try:
        arr_copy = request.array.copy()
        sort_message = ""
        
        # Select algorithm
        if request.algorithm == "linear":
            search_func = linear_search
            algo_name = "Linear Search"
        elif request.algorithm == "binary" or request.algorithm == "interpolation":
            # For binary/interpolation search, sort the array if not already sorted
            if not all(arr_copy[i] <= arr_copy[i+1] for i in range(len(arr_copy)-1)):
                if arr_copy: # Only sort if array is not empty
                    sort_start_time = time.perf_counter()
                    arr_copy.sort() # Use Python's built-in sort
                    sort_end_time = time.perf_counter()
                    total_execution_time += (sort_end_time - sort_start_time) * 1000
                    sort_message = " (Array sorted by backend using built-in sort)"

            if request.algorithm == "binary":
                search_func = binary_search
                algo_name = "Binary Search"
            else: # interpolation
                search_func = interpolation_search
                algo_name = "Interpolation Search"
        else:
            return SearchResponse(
                array=request.array,
                target=request.target,
                found_index=None,
                execution_time_ms=0.0,
                algorithm=request.algorithm,
                message="Invalid algorithm specified"
            )
        
        # Measure search execution time
        search_start_time = time.perf_counter()
        found_index = search_func(arr_copy, request.target)
        search_end_time = time.perf_counter()
        total_execution_time += (search_end_time - search_start_time) * 1000
        
        # Prepare response message
        if found_index is not None and found_index != -1:
            message = f"Target {request.target} found at index {found_index} using {algo_name}{sort_message}"
        else:
            message = f"Target {request.target} not found in the array using {algo_name}{sort_message}"
        
        return SearchResponse(
            array=request.array,
            target=request.target,
            found_index=found_index if found_index != -1 else None,
            execution_time_ms=round(total_execution_time, 5),
            algorithm=algo_name,
            message=message
        )
    except Exception as e:
        # Catch all other exceptions and return a consistent error format
        return SearchResponse(
            array=request.array if 'request' in locals() else [],
            target=request.target if 'request' in locals() else 0,
            found_index=None,
            execution_time_ms=0.0,
            algorithm=request.algorithm if 'request' in locals() else "",
            message=f"An internal server error occurred: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 