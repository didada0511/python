arr = [4]
try:
    print(arr.index(0))
except ValueError:
    print("ValueError")