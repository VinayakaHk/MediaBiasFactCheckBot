import time
import math
import numpy as np
from functools import reduce
from sklearn.linear_model import LinearRegression

def layer1_simple_assignment():
    """Layer 1: Simple variable assignment"""
    start = time.time()
    x = 42
    end = time.time()
    return end - start

def layer2_math_computation():
    """Layer 2: Basic math operations (e.g., factorial)"""
    start = time.time()
    result = math.factorial(100000)
    end = time.time()
    return end - start

def layer3_array_processing():
    """Layer 3: Array processing with NumPy"""
    start = time.time()
    arr = np.random.rand(100000)
    result = np.sqrt(arr * np.sin(arr))
    end = time.time()
    return end - start

def layer4_recursive_function():
    """Layer 4: Recursive Fibonacci with memoization"""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    start = time.time()
    result = fib(300)
    end = time.time()
    return end - start

def layer5_ml_model_training():
    """Layer 5: Basic ML model training with scikit-learn"""
    # Generate dummy data
    X = np.random.rand(10000, 10)
    y = np.random.rand(10000)

    model = LinearRegression()

    start = time.time()
    model.fit(X, y)
    end = time.time()

    return end - start

# Run all layers and print the execution times
if __name__ == "__main__":
    print("Execution Time by Layer:")
    print(f"Layer 1 - Simple Assignment: {layer1_simple_assignment():.10f} seconds")
    print(f"Layer 2 - Math Computation:  {layer2_math_computation():.10f} seconds")
    print(f"Layer 3 - NumPy Processing:  {layer3_array_processing():.10f} seconds")
    print(f"Layer 4 - Recursive Func:    {layer4_recursive_function():.10f} seconds")
    print(f"Layer 5 - ML Model Training: {layer5_ml_model_training():.10f} seconds")
