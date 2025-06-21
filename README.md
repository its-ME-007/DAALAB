# Algorithm Visualizer

A comprehensive Streamlit application that demonstrates various algorithms including sorting, searching, and greedy algorithms with interactive visualizations and performance metrics.

## Features

### Sorting Algorithms
- **Heap Sort**: O(n log n) time complexity, in-place sorting using binary heap
- **Merge Sort**: O(n log n) time complexity, divide-and-conquer approach
- **Quick Sort**: O(n log n) average time complexity, pivot-based partitioning
- **Insertion Sort**: O(n²) time complexity, simple comparison-based sorting

### Searching Algorithms
- **Linear Search**: O(n) time complexity, sequential search through array
- **Binary Search**: O(log n) time complexity, works on sorted arrays
- **Interpolation Search**: O(log log n) average time complexity, improved binary search

### Greedy Algorithms
- **Huffman Coding**: Data compression algorithm using variable-length codes
- **Fractional Knapsack**: Maximize value by taking fractions of items
- **Prim's Algorithm**: Find minimum spanning tree using greedy approach
- **Kruskal's Algorithm**: Find minimum spanning tree using Union-Find
- **Dijkstra's Algorithm**: Find shortest paths from source to all vertices

## Project Structure

```
DAALAB/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── sort/                 # Sorting algorithms
│   ├── heap_sort.py
│   ├── merge_sort.py
│   ├── quick_sort.py
│   └── insertion_sort.py
├── search/               # Searching algorithms
│   ├── linear_search.py
│   ├── binary_search.py
│   └── interpolation_search.py
└── greedy/               # Greedy algorithms
    ├── __init__.py
    ├── huffman.py
    ├── fractional_knapsack.py
    ├── prims.py
    ├── kruskals.py
    └── dijkstras.py
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd DAALAB
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default web browser. You can:

1. **Select Algorithm Category**: Choose between Sorting, Searching, or Greedy algorithms
2. **Choose Algorithm**: Select a specific algorithm from the category
3. **Input Data**: Use manual input or generate random data
4. **Run Algorithm**: Execute the algorithm and view results
5. **Analyze Results**: See performance metrics, execution time, and algorithm-specific outputs

## Algorithm Details

### Sorting Algorithms
- **Heap Sort**: Uses binary heap data structure for efficient sorting
- **Merge Sort**: Recursively divides array and merges sorted subarrays
- **Quick Sort**: Uses pivot element to partition array into smaller subarrays
- **Insertion Sort**: Builds sorted array by inserting elements one by one

### Searching Algorithms
- **Linear Search**: Checks each element sequentially until target is found
- **Binary Search**: Divides search space in half at each step (requires sorted array)
- **Interpolation Search**: Estimates position based on value distribution

### Greedy Algorithms
- **Huffman Coding**: Creates optimal prefix codes for data compression
- **Fractional Knapsack**: Selects items based on value-to-weight ratio
- **Prim's MST**: Grows minimum spanning tree by adding minimum weight edges
- **Kruskal's MST**: Sorts edges and adds them if they don't create cycles
- **Dijkstra's Shortest Path**: Finds shortest paths using priority queue

## Performance Metrics

Each algorithm execution provides:
- **Execution Time**: Measured in milliseconds
- **Algorithm-specific metrics**: 
  - Sorting: Array size, verification of sorted result
  - Searching: Target found/not found, index location
  - Huffman: Compression ratio, character frequencies
  - Knapsack: Total value, remaining capacity
  - MST: Total weight, number of edges
  - Shortest Path: Distances, paths to all vertices

## Contributing

Feel free to add new algorithms or improve existing implementations. Each algorithm should:
- Include proper documentation
- Provide performance metrics
- Handle edge cases gracefully
- Return structured results

## License

This project is open source and available under the MIT License. 