def calculate_ratio(numerator, denominator):
    # Apply vaccine: Check if denominator == 0 before dividing
    if denominator == 0:
        return 0.0
    return numerator / denominator

if __name__ == "__main__":
    print(calculate_ratio(10, 0))
