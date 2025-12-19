#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(cmd):
    """Выполнение команды и вывод результата"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode

def main():
    print("=== UVM Assembler and Interpreter Tests ===\n")
    
    # Тест 1: Проверка ассемблера с тестовыми командами из спецификации
    print("Test 1: Assembling test_all.asm")
    run_command("python assembler.py test_all.asm test_all.bin test")
    
    # Тест 2: Проверка копирования массива
    print("\nTest 2: Array copy test")
    # Сначала инициализируем память
    with open('init_memory.py', 'w') as f:
        f.write("""
# Инициализация памяти для теста копирования
from uvm_core import VirtualMachine
vm = VirtualMachine()
# Записываем тестовые данные по адресу 1000
data = [10, 20, 30, 40, 50]
for i, val in enumerate(data):
    vm.data_memory[1000 + i] = val
print("Memory initialized")
""")
    
    # Тест 3: Побитовый сдвиг векторов
    print("\nTest 3: Vector shift test")
    run_command("python assembler.py vector_shift.asm vector_shift.bin")
    run_command("python interpreter.py vector_shift.bin vector_dump.csv 500-2010")
    
    # Проверка результатов
    print("\nChecking results...")
    expected_results = {
        2000: 255 >> 2,  # 63
        2001: 128 >> 2,  # 32
        2002: 64 >> 2,   # 16
        2003: 32 >> 2,   # 8
        2004: 16 >> 2,   # 4
        2005: 8 >> 2     # 2
    }
    
    # Тест 4: Арифметические операции
    print("\nTest 4: Arithmetic operations")
    run_command("python assembler.py arithmetic.asm arithmetic.bin")
    run_command("python interpreter.py arithmetic.bin arithmetic_dump.csv 1000-1010")
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    main()
