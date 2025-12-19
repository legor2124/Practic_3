from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import struct

class Opcode(Enum):
    """Коды операций УВМ"""
    LOAD_CONST = 44
    READ_MEM = 120
    WRITE_MEM = 34
    SHR = 37

@dataclass
class Command:
    """Промежуточное представление команды"""
    opcode: Opcode
    args: List[int]
    raw_bytes: bytes = b""
    
    def __repr__(self):
        return f"{self.opcode.name} {self.args}"
    
    def to_binary(self) -> bytes:
        """Преобразование в бинарный формат"""
        if self.opcode == Opcode.LOAD_CONST:
            reg, const = self.args
            # Формат: A(7) | B(5) | C(24)
            value = (const << 12) | (reg << 7) | self.opcode.value
            return struct.pack('<I', value)[:5]  # 5 байт
            
        elif self.opcode == Opcode.READ_MEM:
            src_reg, dst_reg = self.args
            # Формат: A(7) | B(5) | C(5)
            value = (dst_reg << 12) | (src_reg << 7) | self.opcode.value
            return struct.pack('<H', value)[:3]  # 3 байта
            
        elif self.opcode == Opcode.WRITE_MEM:
            src_reg, addr_reg = self.args
            # Формат: A(7) | B(5) | C(5)
            value = (addr_reg << 12) | (src_reg << 7) | self.opcode.value
            return struct.pack('<H', value)[:3]
            
        elif self.opcode == Opcode.SHR:
            reg, mem_addr = self.args
            # Формат: A(7) | B(5) | C(30)
            value = (mem_addr << 12) | (reg << 7) | self.opcode.value
            return struct.pack('<Q', value)[:6]  # 6 байт
        
        return b""
    
    @classmethod
    def from_binary(cls, binary: bytes) -> 'Command':
        """Создание команды из бинарного представления"""
        if len(binary) == 0:
            raise ValueError("Empty binary data")
        
        opcode_val = binary[0] & 0x7F
        
        if opcode_val == Opcode.LOAD_CONST.value:
            # 5 байт
            if len(binary) < 5:
                binary = binary.ljust(5, b'\x00')
            value = int.from_bytes(binary[:5], 'little')
            const = (value >> 12) & 0xFFFFFF
            reg = (value >> 7) & 0x1F
            return cls(Opcode.LOAD_CONST, [reg, const], binary[:5])
            
        elif opcode_val == Opcode.READ_MEM.value:
            # 3 байта
            if len(binary) < 3:
                binary = binary.ljust(3, b'\x00')
            value = int.from_bytes(binary[:3], 'little')
            dst_reg = (value >> 12) & 0x1F
            src_reg = (value >> 7) & 0x1F
            return cls(Opcode.READ_MEM, [src_reg, dst_reg], binary[:3])
            
        elif opcode_val == Opcode.WRITE_MEM.value:
            # 3 байта
            if len(binary) < 3:
                binary = binary.ljust(3, b'\x00')
            value = int.from_bytes(binary[:3], 'little')
            addr_reg = (value >> 12) & 0x1F
            src_reg = (value >> 7) & 0x1F
            return cls(Opcode.WRITE_MEM, [src_reg, addr_reg], binary[:3])
            
        elif opcode_val == Opcode.SHR.value:
            # 6 байт
            if len(binary) < 6:
                binary = binary.ljust(6, b'\x00')
            value = int.from_bytes(binary[:6], 'little')
            mem_addr = (value >> 12) & 0x3FFFFFFF
            reg = (value >> 7) & 0x1F
            return cls(Opcode.SHR, [reg, mem_addr], binary[:6])
        
        raise ValueError(f"Unknown opcode: {opcode_val}")

class VirtualMachine:
    """Модель виртуальной машины"""
    
    def __init__(self, data_mem_size: int = 65536):
        self.registers = [0] * 32  # 32 регистра
        self.data_memory = [0] * data_mem_size
        self.program: List[Command] = []
        self.pc = 0  # Счётчик команд
        
    def reset(self):
        """Сброс состояния машины"""
        self.registers = [0] * 32
        self.data_memory = [0] * len(self.data_memory)
        self.pc = 0
    
    def load_program(self, binary_data: bytes):
        """Загрузка бинарной программы"""
        self.program.clear()
        i = 0
        
        while i < len(binary_data):
            # Определяем длину команды по первому байту
            first_byte = binary_data[i]
            opcode_val = first_byte & 0x7F
            
            # Определяем длину команды
            if opcode_val == Opcode.LOAD_CONST.value:
                cmd_len = 5
            elif opcode_val in (Opcode.READ_MEM.value, Opcode.WRITE_MEM.value):
                cmd_len = 3
            elif opcode_val == Opcode.SHR.value:
                cmd_len = 6
            else:
                raise ValueError(f"Unknown opcode in binary: {opcode_val}")
            
            # Извлекаем команду
            cmd_bytes = binary_data[i:i+cmd_len]
            if len(cmd_bytes) < cmd_len:
                cmd_bytes = cmd_bytes.ljust(cmd_len, b'\x00')
            
            # Создаём команду
            cmd = Command.from_binary(cmd_bytes)
            self.program.append(cmd)
            i += cmd_len
    
    def execute_step(self) -> bool:
        """Выполнение одной команды"""
        if self.pc >= len(self.program):
            return False
        
        cmd = self.program[self.pc]
        self.execute_command(cmd)
        self.pc += 1
        return True
    
    def execute_command(self, cmd: Command):
        """Выполнение конкретной команды"""
        if cmd.opcode == Opcode.LOAD_CONST:
            reg, const = cmd.args
            self.registers[reg] = const
            
        elif cmd.opcode == Opcode.READ_MEM:
            src_reg, dst_reg = cmd.args
            mem_addr = self.registers[src_reg]
            self.registers[dst_reg] = self.data_memory[mem_addr]
            
        elif cmd.opcode == Opcode.WRITE_MEM:
            src_reg, addr_reg = cmd.args
            mem_addr = self.registers[addr_reg]
            self.data_memory[mem_addr] = self.registers[src_reg]
            
        elif cmd.opcode == Opcode.SHR:
            reg, mem_addr = cmd.args
            shift_amount = self.data_memory[mem_addr]
            # Логический сдвиг вправо
            self.registers[reg] = self.registers[reg] >> shift_amount
    
    def run(self, max_steps: int = 10000):
        """Выполнение программы"""
        steps = 0
        while self.execute_step() and steps < max_steps:
            steps += 1
    
    def dump_memory(self, start_addr: int, end_addr: int) -> List[tuple]:
        """Получение дампа памяти"""
        dump = []
        for addr in range(start_addr, min(end_addr + 1, len(self.data_memory))):
            dump.append((addr, self.data_memory[addr]))
        return dump
