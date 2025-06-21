import heapq
import time

def prims_mst(graph, start_vertex=0):
    """
    Find Minimum Spanning Tree using Prim's algorithm
    
    Args:
        graph: Adjacency matrix representation of the graph
        start_vertex: Starting vertex for the algorithm
    
    Returns:
        Dictionary containing MST details
    """
    start_time = time.time()
    
    if not graph or len(graph) == 0:
        return {
            "error": "Invalid graph: empty or None"
        }
    
    n = len(graph)
    if start_vertex >= n:
        return {
            "error": f"Invalid start vertex: {start_vertex}. Must be less than {n}"
        }
    
    # Initialize data structures
    mst_edges = []
    mst_weight = 0
    visited = [False] * n
    min_heap = []
    
    # Start with the starting vertex
    visited[start_vertex] = True
    
    # Add all edges from start vertex to heap
    for v in range(n):
        if graph[start_vertex][v] > 0:
            heapq.heappush(min_heap, (graph[start_vertex][v], start_vertex, v))
    
    # Process edges until we have n-1 edges (complete MST)
    while min_heap and len(mst_edges) < n - 1:
        weight, u, v = heapq.heappop(min_heap)
        
        # Skip if both vertices are already visited
        if visited[u] and visited[v]:
            continue
        
        # Add edge to MST
        mst_edges.append({
            'from': u,
            'to': v,
            'weight': weight
        })
        mst_weight += weight
        
        # Mark the unvisited vertex as visited
        if not visited[v]:
            visited[v] = True
            # Add all edges from v to unvisited vertices
            for w in range(n):
                if not visited[w] and graph[v][w] > 0:
                    heapq.heappush(min_heap, (graph[v][w], v, w))
        else:
            visited[u] = True
            # Add all edges from u to unvisited vertices
            for w in range(n):
                if not visited[w] and graph[u][w] > 0:
                    heapq.heappush(min_heap, (graph[u][w], u, w))
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "graph": graph,
        "start_vertex": start_vertex,
        "mst_edges": mst_edges,
        "mst_weight": mst_weight,
        "num_vertices": n,
        "num_edges_in_mst": len(mst_edges),
        "execution_time_ms": execution_time,
        "is_connected": len(mst_edges) == n - 1
    }

def create_graph_from_edges(edges, num_vertices):
    """
    Create adjacency matrix from list of edges
    
    Args:
        edges: List of tuples (u, v, weight)
        num_vertices: Number of vertices in the graph
    
    Returns:
        Adjacency matrix
    """
    graph = [[0] * num_vertices for _ in range(num_vertices)]
    
    for u, v, weight in edges:
        if 0 <= u < num_vertices and 0 <= v < num_vertices:
            graph[u][v] = weight
            graph[v][u] = weight  # Undirected graph
    
    return graph

def generate_sample_graph(num_vertices=5, density=0.7, max_weight=100):
    """
    Generate a random connected graph
    
    Args:
        num_vertices: Number of vertices
        density: Probability of edge existence (0-1)
        max_weight: Maximum edge weight
    
    Returns:
        Adjacency matrix
    """
    import random
    
    graph = [[0] * num_vertices for _ in range(num_vertices)]
    
    # Ensure connectivity by creating a spanning tree first
    for i in range(1, num_vertices):
        j = random.randint(0, i-1)
        weight = random.randint(1, max_weight)
        graph[i][j] = weight
        graph[j][i] = weight
    
    # Add additional edges based on density
    for i in range(num_vertices):
        for j in range(i+1, num_vertices):
            if graph[i][j] == 0 and random.random() < density:
                weight = random.randint(1, max_weight)
                graph[i][j] = weight
                graph[j][i] = weight
    
    return graph 