import time

def fractional_knapsack(weights, values, capacity):
    """
    Solve fractional knapsack problem using greedy approach
    
    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum capacity of knapsack
    
    Returns:
        Dictionary containing solution details
    """
    start_time = time.time()
    
    if not weights or not values or len(weights) != len(values):
        return {
            "error": "Invalid input: weights and values must be non-empty lists of equal length"
        }
    
    # Create list of items with their value-to-weight ratios
    items = []
    for i in range(len(weights)):
        if weights[i] <= 0:
            continue  # Skip items with non-positive weight
        value_per_weight = values[i] / weights[i]
        items.append({
            'index': i,
            'weight': weights[i],
            'value': values[i],
            'value_per_weight': value_per_weight
        })
    
    # Sort items by value-to-weight ratio in descending order
    items.sort(key=lambda x: x['value_per_weight'], reverse=True)
    
    total_value = 0
    remaining_capacity = capacity
    selected_items = []
    
    # Fill knapsack greedily
    for item in items:
        if remaining_capacity <= 0:
            break
            
        if item['weight'] <= remaining_capacity:
            # Take the entire item
            fraction = 1.0
            taken_weight = item['weight']
            taken_value = item['value']
            remaining_capacity -= item['weight']
        else:
            # Take a fraction of the item
            fraction = remaining_capacity / item['weight']
            taken_weight = remaining_capacity
            taken_value = item['value'] * fraction
            remaining_capacity = 0
        
        total_value += taken_value
        
        selected_items.append({
            'item_index': item['index'],
            'original_weight': item['weight'],
            'original_value': item['value'],
            'fraction_taken': fraction,
            'weight_taken': taken_weight,
            'value_taken': taken_value
        })
    
    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "weights": weights,
        "values": values,
        "capacity": capacity,
        "total_value": total_value,
        "remaining_capacity": remaining_capacity,
        "selected_items": selected_items,
        "execution_time_ms": execution_time,
        "items_used": len(selected_items)
    }

def generate_sample_data(num_items=5, max_weight=50, max_value=100, capacity=30):
    """Generate sample data for fractional knapsack"""
    import random
    
    weights = [random.randint(1, max_weight) for _ in range(num_items)]
    values = [random.randint(1, max_value) for _ in range(num_items)]
    
    return weights, values, capacity 