#include <iostream>
#include <vector>
#include <chrono>

int main() {
    std::cout << "Hello from C++!" << std::endl;
    
    // Simple algorithm test
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = 0;
    
    for (int num : numbers) {
        sum += num;
    }
    
    std::cout << "Sum of numbers: " << sum << std::endl;
    
    return 0;
}