import time

class UnionFind:
    """Union-Find data structure for Kruskal's algorithm"""
    
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True

def kruskals_mst(graph):
    """
    Find Minimum Spanning Tree using Kruskal's algorithm
    
    Args:
        graph: Adjacency matrix representation of the graph
    
    Returns:
        Dictionary containing MST details
    """
    start_time = time.time()
    
    if not graph or len(graph) == 0:
        return {
            "error": "Invalid graph: empty or None"
        }
    
    n = len(graph)
    
    # Create list of edges
    edges = []
    for i in range(n):
        for j in range(i+1, n):  # Only upper triangle to avoid duplicates
            if graph[i][j] > 0:
                edges.append((graph[i][j], i, j))
    
    # Sort edges by weight
    edges.sort()
    
    # Initialize Union-Find
    uf = UnionFind(n)
    
    mst_edges = []
    mst_weight = 0
    
    # Process edges in ascending order
    for weight, u, v in edges:
        if uf.union(u, v):
            mst_edges.append({
                'from': u,
                'to': v,
                'weight': weight
            })
            mst_weight += weight
            
            # Stop when we have n-1 edges
            if len(mst_edges) == n - 1:
                break
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "graph": graph,
        "mst_edges": mst_edges,
        "mst_weight": mst_weight,
        "num_vertices": n,
        "num_edges_in_mst": len(mst_edges),
        "total_edges_considered": len(edges),
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