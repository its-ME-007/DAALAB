import heapq
import time

def dijkstras_shortest_path(graph, source):
    """
    Find shortest paths from source to all vertices using Dijkstra's algorithm
    
    Args:
        graph: Adjacency matrix representation of the graph
        source: Source vertex
    
    Returns:
        Dictionary containing shortest path details
    """
    start_time = time.time()
    
    if not graph or len(graph) == 0:
        return {
            "error": "Invalid graph: empty or None"
        }
    
    n = len(graph)
    if source >= n or source < 0:
        return {
            "error": f"Invalid source vertex: {source}. Must be between 0 and {n-1}"
        }
    
    # Initialize distances and previous vertices
    distances = [float('inf')] * n
    previous = [-1] * n
    distances[source] = 0
    
    # Priority queue: (distance, vertex)
    pq = [(0, source)]
    visited = set()
    
    while pq:
        current_distance, current_vertex = heapq.heappop(pq)
        
        # Skip if we've already processed this vertex
        if current_vertex in visited:
            continue
        
        visited.add(current_vertex)
        
        # Check all neighbors
        for neighbor in range(n):
            if graph[current_vertex][neighbor] > 0:  # Edge exists
                distance = current_distance + graph[current_vertex][neighbor]
                
                # If we found a shorter path
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_vertex
                    heapq.heappush(pq, (distance, neighbor))
    
    # Reconstruct paths
    paths = {}
    for target in range(n):
        if distances[target] == float('inf'):
            paths[target] = None
        else:
            path = []
            current = target
            while current != -1:
                path.append(current)
                current = previous[current]
            paths[target] = list(reversed(path))
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "graph": graph,
        "source": source,
        "distances": distances,
        "previous": previous,
        "paths": paths,
        "num_vertices": n,
        "execution_time_ms": execution_time,
        "vertices_processed": len(visited)
    }

def create_graph_from_edges(edges, num_vertices, directed=False):
    """
    Create adjacency matrix from list of edges
    
    Args:
        edges: List of tuples (u, v, weight)
        num_vertices: Number of vertices in the graph
        directed: Whether the graph is directed
    
    Returns:
        Adjacency matrix
    """
    graph = [[0] * num_vertices for _ in range(num_vertices)]
    
    for u, v, weight in edges:
        if 0 <= u < num_vertices and 0 <= v < num_vertices:
            graph[u][v] = weight
            if not directed:
                graph[v][u] = weight  # Undirected graph
    
    return graph

def generate_sample_graph(num_vertices=5, density=0.7, max_weight=100, directed=False):
    """
    Generate a random graph
    
    Args:
        num_vertices: Number of vertices
        density: Probability of edge existence (0-1)
        max_weight: Maximum edge weight
        directed: Whether the graph is directed
    
    Returns:
        Adjacency matrix
    """
    import random
    
    graph = [[0] * num_vertices for _ in range(num_vertices)]
    
    # Add edges based on density
    for i in range(num_vertices):
        for j in range(num_vertices):
            if i != j and random.random() < density:
                weight = random.randint(1, max_weight)
                graph[i][j] = weight
                if not directed:
                    graph[j][i] = weight
    
    return graph

def find_shortest_path_between(graph, source, target):
    """
    Find shortest path between two specific vertices
    
    Args:
        graph: Adjacency matrix
        source: Source vertex
        target: Target vertex
    
    Returns:
        Dictionary with path details
    """
    result = dijkstras_shortest_path(graph, source)
    
    if "error" in result:
        return result
    
    if result["distances"][target] == float('inf'):
        return {
            "error": f"No path exists from {source} to {target}"
        }
    
    return {
        "source": source,
        "target": target,
        "distance": result["distances"][target],
        "path": result["paths"][target],
        "execution_time_ms": result["execution_time_ms"]
    } 