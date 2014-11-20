# -*- coding: utf-8
__author__ = 'shibotian'


class MIPS_Machine:
    def __init__(self):
        # 每一段
        self.if_id = IF_ID()
        self.id_ex = ID_EX()
        self.ex_mem = EX_MEM()
        self.mem_wb = MEM_WB()

        # 通用寄存器组(R0-R7)
        self.comm_reg = [
            TYPE_16(0),     # R0
            TYPE_16(0),     # R1
            TYPE_16(0),     # R2
            TYPE_16(0),     # R3
            TYPE_16(0),     # R4
            TYPE_16(0),     # R5
            TYPE_16(0),     # R6
            TYPE_16(0),     # R7
        ]

        # PC
        self.pc = TYPE_16(0)

        # 内存（包括指令）
        self.memory = Memory(1024)

        # 节拍计数器
        self.step_count = 1

    def show_step_info(self):
        print '''
            第%s拍:
                PC: %s(%s)
                reg: R0=%s(%s), R1=%s(%s), R2=%s(%s), R3=%s(%s), R4=%s(%s), R5=%s(%s), R6=%s(%s), R7=%s(%s),''' \
              % (
            self.step_count,
            bin(self.pc.value), self.pc.value,
            bin(self.comm_reg[0].value), self.comm_reg[0].value,
            bin(self.comm_reg[1].value), self.comm_reg[1].value,
            bin(self.comm_reg[2].value), self.comm_reg[2].value,
            bin(self.comm_reg[3].value), self.comm_reg[3].value,
            bin(self.comm_reg[4].value), self.comm_reg[4].value,
            bin(self.comm_reg[5].value), self.comm_reg[5].value,
            bin(self.comm_reg[6].value), self.comm_reg[6].value,
            bin(self.comm_reg[7].value), self.comm_reg[7].value,
        ),

    def show_result_info(self):
        print '''
                ins_code: %s

                IF/ID:  NPC=%s(%s), IR=%s
                ID/EX:  NPC=%s(%s), IR=%s, A=%s(%s), B=%s(%s), Imm=%s(%s)
                EX/MEM: cond=%s, IR=%s, ALUo=%s(%s), B=%s(%s)
                MEM/WB: LMD=%s(%s), IR=%s, ALUo=%s(%s)
            ************************************************************************************************************************'''\
        % (
            bin(self.if_id.IR.value),
            bin(self.if_id.NPC.value), self.if_id.NPC.value,
            bin(self.if_id.IR.value),

            bin(self.id_ex.NPC.value), self.id_ex.NPC.value,
            bin(self.id_ex.IR.value),
            bin(self.id_ex.A.value), self.id_ex.A.value,
            bin(self.id_ex.B.value), self.id_ex.B.value,
            bin(self.id_ex.Imm.value), self.id_ex.Imm.value,

            self.ex_mem.cond,
            bin(self.ex_mem.IR.value),
            bin(self.ex_mem.ALUo.value), self.ex_mem.ALUo.value,
            bin(self.ex_mem.B.value), self.ex_mem.B.value,

            bin(self.mem_wb.LMD.value), self.mem_wb.LMD.value,
            bin(self.mem_wb.IR.value),
            bin(self.mem_wb.ALUo.value), self.mem_wb.ALUo.value
        )

    # 五段流水线
    def step(self):
        self.show_step_info()
        self.__MIPS_IF__()
        self.__MIPS_ID__()
        self.__MIPS_EX__()
        self.__MIPS_MEM__()
        self.__MIPS_WB__()
        self.step_count += 1
        self.show_result_info()

    # 五段流水线 逆执行，可以起到“模拟并行”的效果
    def rev_step(self):
        self.show_step_info()
        self.__MIPS_WB__()
        self.__MIPS_MEM__()
        self.__MIPS_EX__()
        self.__MIPS_ID__()
        self.__MIPS_IF__()
        self.step_count += 1
        self.show_result_info()

    # 取指令周期（IF）
    def __MIPS_IF__(self):
        self.if_id.IR.value = self.memory.get_instruction(self.pc.value).value
        if self.ex_mem.IR.get_op() == 3 and self.ex_mem.cond is True:  # 需要跳转
            self.if_id.IR.value = self.ex_mem.ALUo.value    ########  书上没有？？
            self.if_id.NPC.value = self.ex_mem.ALUo.value
            self.pc.value = self.ex_mem.ALUo.value
        else:
            self.if_id.NPC.value = self.pc.value + 2
            self.pc.value += 2

    # 指令译码/读寄存器周期（ID）
    def __MIPS_ID__(self):
        self.id_ex.A.value = self.comm_reg[self.if_id.IR.get_rs()].value
        self.id_ex.B.value = self.comm_reg[self.if_id.IR.get_rt()].value
        self.id_ex.NPC.value = self.if_id.NPC.value
        self.id_ex.IR.value = self.if_id.IR.value
        self.id_ex.Imm.value = self.if_id.IR.get_imm()

    # 执行/有效地址计算周期（EX）
    def __MIPS_EX__(self):
        self.ex_mem.IR.value = self.id_ex.IR.value
        if self.id_ex.IR.get_op() == 2:     # ALU指令（+）
            self.ex_mem.ALUo.value = self.id_ex.A.value + self.id_ex.B.value
        elif self.id_ex.IR.get_op() == 3:   # 分支指令
            self.ex_mem.ALUo.value = self.id_ex.NPC.value + self.id_ex.Imm.value*2    # 保存分支目标地址
            if self.comm_reg[self.id_ex.IR.get_rt()].value == self.comm_reg[self.id_ex.IR.get_rs()].value:  # 判断是否满足分支条件（reg[rs]=reg[rt]）
                self.ex_mem.cond = True

    # 存储器访问/分支完成周期（MEM）
    def __MIPS_MEM__(self):
        self.mem_wb.IR.value = self.ex_mem.IR.value
        if self.ex_mem.IR.get_op() == 2:    # ALU指令（+）
            self.mem_wb.ALUo.value = self.ex_mem.ALUo.value
        elif self.ex_mem.IR.get_op() == 3:  # 分支指令
            # 无操作
            pass

    # 写回周期（WB）
    def __MIPS_WB__(self):
        if self.mem_wb.IR.get_op() == 2:    # ALU指令（+）
            self.comm_reg[self.mem_wb.IR.get_rd()].value = self.mem_wb.ALUo.value
        elif self.mem_wb.IR.get_op() == 3:  # 分支指令
            # 无操作
            pass


class IF_ID:
    def __init__(self):
        self.NPC = TYPE_16(0)
        self.IR = TYPE_16(0)


class ID_EX:
    def __init__(self):
        self.NPC = TYPE_16(0)
        self.A = TYPE_16(0)
        self.B = TYPE_16(0)
        self.Imm = TYPE_16(0)
        self.IR = TYPE_16(0)


class EX_MEM:
    def __init__(self):
        # self.cond = TYPE_16(0)
        self.cond = False
        self.ALUo = TYPE_16(0)
        self.B = TYPE_16(0)
        self.IR = TYPE_16(0)


class MEM_WB:
    def __init__(self):
        self.LMD = TYPE_16(0)
        self.ALUo = TYPE_16(0)
        self.IR = TYPE_16(0)


# 内存
class Memory:
    def __init__(self, size):
        self.memory = []
        for i in range(size):
            self.memory.append(TYPE_8(0))

    def set_byte(self, address, value):
        self.memory[address] = TYPE_8(value)

    def get_byte(self, address):
        return self.memory[address]

    # 置入一条指令，address-地址 ins-指令（TYPE_16）
    def set_instruction(self, address, ins):
        high, low = ins.get_type_8()
        self.memory[address] = low
        self.memory[address + 1] = high

    def get_instruction(self, address):
        return TYPE_16.get_type_16_by_type_8(self.memory[address + 1], self.memory[address])


# 表示一个16位寄存器
class TYPE_16:
    @staticmethod
    def get_type_16_by_value(value):
        obj = TYPE_16(value)
        return obj

    @staticmethod
    def get_type_16_by_type_8(TYPE_8_HIGH, TYPE_8_LOW):
        obj = TYPE_16(0)
        obj.value = TYPE_8_HIGH.value << 8
        obj.value |= TYPE_8_LOW.value
        return obj

    def __init__(self, value=0):
        self.value = value

    # 获取type16的高8位、低8位
    def get_type_8(self):
        return TYPE_8((self.value & 0xff00) >> 8), TYPE_8(self.value & 0xff)

    # 取一定范围的内容, 从_from(包括)起到_to(包括)
    def get_range(self, _from=0, _to=0):

        # 生成掩码（与掩码）
        mask = 0
        for item in [i in range(_from, _to+1) for i in range(0, 16)]:
            mask <<= 1
            mask |= 1 if item is True else 0

        # 用掩码获取指定段间内容
        result = self.value & mask

        # 位移到最右端
        result >>= 15-_to
        return result

    # 获得运算符
    def get_op(self):
        return self.get_range(0, 1)

    def get_rs(self):
        return self.get_range(2, 4)

    def get_rt(self):
        return self.get_range(5, 7)

    def get_rd(self):
        return self.get_range(8, 10)

    def get_imm(self):  # 处理一位符号位
        if self.get_range(8, 8) == 1:
            return -self.get_range(9, 15)
        elif self.get_range(8, 8) == 0:
            return self.get_range(9, 15)


# 表示一个8位寄存器（内存中使用）
class TYPE_8:
    def __init__(self, value=0):
        self.value = value


if __name__ == "__main__":
    # 初始化MIPS机
    machine = MIPS_Machine()

    # 装入程序

    ##################################################################################################################
    #  本程序流水线无冲突
    # ADD R0 R1 R2              10 000 001 010 00000    0x8140  33088
    # ADD R3 R4 R5              10 011 100 101 00000    0x9CA0  40096

    machine.memory.set_instruction(0, TYPE_16(0x8140))
    machine.memory.set_instruction(2, TYPE_16(0x9CA0))

    machine.comm_reg[0].value = 0
    machine.comm_reg[1].value = 1
    machine.comm_reg[2].value = 2
    machine.comm_reg[3].value = 3
    machine.comm_reg[4].value = 4
    machine.comm_reg[5].value = 5
    machine.comm_reg[6].value = 6
    machine.comm_reg[7].value = 7

    ##################################################################################################################

    # ##################################################################################################################
    # # 本程序流水线有冲突
    # # R1=0 R2=1 R3=2 R4=0 R5=123 R6=321
    # # ADD R1 R2 R1              10 001 010 001 00000    0x8A20  35360
    # # ADD R1 R2 R1              10 001 010 001 00000    0x8A20  35360
    # # BEQ R1 R3 0000 0000       11 001 011 0000 0000    0xCB01  25984
    # # ADD R4 R5 R4              10 100 101 100 00000    0xA580  42368
    # # ADD R4 R6 R4              10 100 110 100 00000    0xA680  42624
    #
    # machine.memory.set_instruction(0, TYPE_16(0x8A20))
    # machine.memory.set_instruction(2, TYPE_16(0x8A20))
    # machine.memory.set_instruction(4, TYPE_16(0xCB00))
    # machine.memory.set_instruction(6, TYPE_16(0xA580))
    # machine.memory.set_instruction(8, TYPE_16(0xA680))
    #
    # # 初始化寄存器
    # machine.comm_reg[0].value = 0
    # machine.comm_reg[1].value = 0
    # machine.comm_reg[2].value = 1
    # machine.comm_reg[3].value = 2
    # machine.comm_reg[4].value = 0
    # machine.comm_reg[5].value = 123
    # machine.comm_reg[6].value = 321
    # machine.comm_reg[7].value = 0
    #
    # ###################################################################################################################

    # 单步
    for i in range(20):
        # machine.step()
        machine.rev_step()


