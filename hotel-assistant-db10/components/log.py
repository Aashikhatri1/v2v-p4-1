def print_and_save(message, file_path='output.txt'):
    print(message)
    with open(file_path, 'a') as file:  # 'a' mode for appending to the file
        file.write(message + '\n')

# Example usage
print_and_save("Hello, World!")
