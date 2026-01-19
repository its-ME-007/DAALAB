"""Test fixtures - sample code snippets for different complexity classes."""

# ============================================================================
# O(1) - Constant Time
# ============================================================================

CONSTANT_TIME_SAMPLES = {
    "python": [
        """# O(1) - Array access
def get_first_element(arr):
    if arr:
        return arr[0]
    return None

result = get_first_element([1, 2, 3, 4, 5])
print(result)
""",
        """# O(1) - Hash table lookup
def get_value(dictionary, key):
    return dictionary.get(key, "Not found")

data = {"name": "Alice", "age": 30}
print(get_value(data, "name"))
""",
    ],
    "cpp": [
        """// O(1) - Array access
#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<int> arr = {1, 2, 3, 4, 5};
    if (!arr.empty()) {
        cout << arr[0] << endl;
    }
    return 0;
}
""",
    ]
}

# ============================================================================
# O(n) - Linear Time
# ============================================================================

LINEAR_TIME_SAMPLES = {
    "python": [
        """# O(n) - Linear search
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1

arr = list(range(1000))
result = linear_search(arr, 500)
print(f"Found at index: {result}")
""",
        """# O(n) - Sum array
def sum_array(arr):
    total = 0
    for num in arr:
        total += num
    return total

arr = list(range(1000))
result = sum_array(arr)
print(f"Sum: {result}")
""",
    ],
    "cpp": [
        """// O(n) - Linear search
#include <iostream>
#include <vector>
using namespace std;

int linearSearch(const vector<int>& arr, int target) {
    for (int i = 0; i < arr.size(); i++) {
        if (arr[i] == target) {
            return i;
        }
    }
    return -1;
}

int main() {
    vector<int> arr(1000);
    for (int i = 0; i < 1000; i++) arr[i] = i;
    cout << "Found at: " << linearSearch(arr, 500) << endl;
    return 0;
}
""",
    ]
}

# ============================================================================
# O(n log n) - Linearithmic Time
# ============================================================================

LINEARITHMIC_TIME_SAMPLES = {
    "python": [
        """# O(n log n) - Merge sort
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

arr = [5, 2, 8, 1, 9, 3, 7, 4, 6]
sorted_arr = merge_sort(arr)
print(sorted_arr)
""",
        """# O(n log n) - Using built-in sort
arr = list(range(1000, 0, -1))
sorted_arr = sorted(arr)
print(f"First 5: {sorted_arr[:5]}")
""",
    ],
    "cpp": [
        """// O(n log n) - Merge sort
#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main() {
    vector<int> arr(100);
    for (int i = 0; i < 100; i++) arr[i] = 100 - i;
    
    sort(arr.begin(), arr.end());
    
    cout << "First 5: ";
    for (int i = 0; i < 5; i++) {
        cout << arr[i] << " ";
    }
    cout << endl;
    
    return 0;
}
""",
    ]
}

# ============================================================================
# O(n²) - Quadratic Time
# ============================================================================

QUADRATIC_TIME_SAMPLES = {
    "python": [
        """# O(n²) - Bubble sort
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

arr = [64, 34, 25, 12, 22, 11, 90]
sorted_arr = bubble_sort(arr.copy())
print(sorted_arr)
""",
        """# O(n²) - Nested loop
def print_pairs(arr):
    count = 0
    for i in range(len(arr)):
        for j in range(len(arr)):
            count += 1
    return count

arr = list(range(50))
result = print_pairs(arr)
print(f"Total pairs: {result}")
""",
    ],
    "cpp": [
        """// O(n²) - Bubble sort
#include <iostream>
#include <vector>
using namespace std;

void bubbleSort(vector<int>& arr) {
    int n = arr.size();
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n-i-1; j++) {
            if (arr[j] > arr[j+1]) {
                swap(arr[j], arr[j+1]);
            }
        }
    }
}

int main() {
    vector<int> arr = {64, 34, 25, 12, 22, 11, 90};
    bubbleSort(arr);
    
    for (int num : arr) {
        cout << num << " ";
    }
    cout << endl;
    
    return 0;
}
""",
    ]
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_sample(complexity: str, language: str, index: int = 0) -> str:
    """
    Get a sample code snippet.
    
    Args:
        complexity: "constant", "linear", "linearithmic", or "quadratic"
        language: "python" or "cpp"
        index: Sample index (if multiple samples available)
    
    Returns:
        Code string
    """
    samples_map = {
        "constant": CONSTANT_TIME_SAMPLES,
        "linear": LINEAR_TIME_SAMPLES,
        "linearithmic": LINEARITHMIC_TIME_SAMPLES,
        "quadratic": QUADRATIC_TIME_SAMPLES,
    }
    
    if complexity not in samples_map:
        raise ValueError(f"Unknown complexity: {complexity}")
    
    samples = samples_map[complexity].get(language, [])
    
    if not samples:
        raise ValueError(f"No samples for {complexity}/{language}")
    
    return samples[min(index, len(samples) - 1)]


def get_all_samples(language: str = "python") -> dict:
    """Get all sample code snippets for a language."""
    return {
        "constant": CONSTANT_TIME_SAMPLES.get(language, []),
        "linear": LINEAR_TIME_SAMPLES.get(language, []),
        "linearithmic": LINEARITHMIC_TIME_SAMPLES.get(language, []),
        "quadratic": QUADRATIC_TIME_SAMPLES.get(language, []),
    }
