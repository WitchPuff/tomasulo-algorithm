

class tomasulo():
    def __init__(self, ld,sd,add,sub,mul,div,numld=3,numsd=3,numadd=3,nummul=2,max_reg=30) -> None:
        # 每条指令的执行时间
        self.extime = {'LD':ld+1,'SD':sd+1,'SUBD':sub+1,'ADDD':add+1,'MULTD':mul+1,'DIVD':div+1}
        # reservation stations & load/store buffer & FU的单元数量
        self.numadd,self.nummul,self.numld,self.numsd,self.max_reg = numadd,nummul,numld,numsd,max_reg
        # 将运算单元与缓冲区的情况都存入reservation stations
        # add & mult: busy,op,vj,vk,qj,qk,time, time为执行倒计时
        self.resv = [[0,0,0,0,0,0] for i in range(numadd + nummul)] 
        self.resv += [[0,0,0] for i in range(numld)] # ld: address,time
        self.resv += [[0,0,0,0] for i in range(numsd)] # sd: address,fu,time
        self.reg = [0 for i in range(max_reg)] # Function Unit
        # 所有单元的代号，顺序与self.resv对应
        self.units = (  'Add1','Add2','Add3','Mult1',
                        'Mult2','Load1','Load2','Load3',
                        'Store1','Store2','Store3')
        # 用于记录指令的执行情况，元素形如（issue周期、执行完成周期、写回周期，完成/被分配的执行单元）
        self.inst_status = [] 
        self.inst_buffer = [] # 存放被阻塞无法issue的指令
        self.clock = 0 # 记录当前周期
        self.inst = [] # 输入的指令集
        
    def input(self,path):
        with open(path,'r') as f:
            for i in f.readlines():
                self.inst.append(tuple(i.strip().split()))
    
    def issue(self):
        # update the load/store & reservation tables
        if len(self.inst_buffer):
            inst = op,dest,j,k = self.inst_buffer.pop(0) # 优先处理缓冲区的指令
        else:
            inst = op,dest,j,k = self.inst.pop(0)
        dest = int(dest[1:])
        item = 0
        flag = 0
        if op == 'LD' or op == 'SD':
            if op == 'LD':
                n,m = 5,8
            elif op == 'SD':
                n,m = 8,11
            for i in range(n,m):
                if self.resv[i][0] == 0: # 找出第一个闲置的缓冲区
                    item = self.units[i] # 分配load/store buffer
                    if op == 'LD':
                        self.resv[i] = [1, j+k, self.extime[op]] # busy,address,time
                    elif self.reg[dest] == 0: # 该寄存器中为立即数，可以直接取出
                        self.resv[i] = [1, j+k, f'R(F{dest})',self.extime[op]] # busy,address,fu,time
                    else:
                        self.resv[i] = [1, j+k, self.reg[dest],self.extime[op]]
                    flag = 1 # 缓冲区未满，成功issue并分配缓冲区
                    break 
        else:
            j = int(j[1:])
            k = int(k[1:])
            if op == 'MULTD' or op == 'DIVD':
                n,m = 3,5
            elif op == 'ADDD' or op == 'SUBD':
                n,m = 0,3
            for i in range(n,m):
                if self.resv[i][0] == 0: # 找出第一个闲置的执行单元
                    item = self.units[i] # 分配执行单元
                    flag = 1
                    vj = qj = vk = qk = 0
                    # j
                    jt = self.reg[j]
                    if jt == 0: # 寄存器中为立即数，可以直接取出
                        jt = f'R(F{j})'
                    if jt in self.units: # 堵塞
                        qj = jt
                    else: # 可以直接取出值
                        vj = jt
                    # k
                    kt = self.reg[k]
                    if kt == 0: # 寄存器中为立即数，可以直接取出
                        kt = f'R(F{k})'
                    if kt in self.units: # 堵塞
                        qk = kt
                    else: # 可以直接取出值
                        vk = kt
                    self.resv[i] = [1,op,vj,vk,qj,qk,self.extime[op]]
                    break
        if flag == 0: # if reservation table/ buffer is full
            self.inst_buffer.append(inst) # 加入堵塞队列
        else:
            self.inst_status.append([(inst),[self.clock,0,0,item]]) # issue,exe,wr,item
            self.reg[dest] = item # 该寄存器在等待当前分配的执行单元的结果
    

    def next(self):
        # next cycle
        self.clock += 1
        # ISSUE
        if len(self.inst):
            self.issue()
            
        # check if the instructions are executable or ready to write back
        for inst,it in self.inst_status:
            # it = issue,exec,wr,item
            # unfinished，当释放对应执行单元/buffer后，item设为1，代表finished
            if it[-1] != 1: 
                op,dest,j,k = inst
                dest = int(dest[1:])
                temp = self.resv[self.units.index(it[-1])] 
                # 执行倒计时为0时，写回，释放对应的FU与RESV
                if temp[-1] == 0: 
                    if op == 'LD':
                        # temp = busy,address,time
                        self.reg[dest] = f'M({temp[1]})'
                        self.resv[self.units.index(it[-1])] = [0,0,0] # clear related item in resv
                    elif op == 'MULTD':
                        # temp = busy,op,vj,vk,qj,qk,time
                        self.reg[dest] = f'{temp[2]}*{temp[3]}'
                        self.resv[self.units.index(it[-1])] = [0,0,0,0,0,0,0]
                    elif op == 'DIVD':
                        self.reg[dest] = f'{temp[2]}/{temp[3]}'
                        self.resv[self.units.index(it[-1])] = [0,0,0,0,0,0,0]
                    elif op == 'SUBD':
                        self.reg[dest] = f'{temp[2]}-{temp[3]}'
                        self.resv[self.units.index(it[-1])] = [0,0,0,0,0,0,0]
                    elif op == 'ADDD':
                        self.reg[dest] = f'{temp[2]}+{temp[3]}'
                        self.resv[self.units.index(it[-1])] = [0,0,0,0,0,0,0]
                    else:
                        # temp = busy, address, fu, time
                        self.resv[self.units.index(it[-1])] = [0,0,0,0]
                    it[2] = self.clock #wr cycle
                    it[3] = 1 # tag done!
                # 若未执行完，判断是否能执行（即vj，vk不为空），若能，倒计时-1
                else:
                    if op == 'LD':
                        self.resv[self.units.index(it[-1])][-1] -= 1
                    elif op == 'SD': #temp = busy,address,fu,time
                        if temp[2] not in self.units:
                            self.resv[self.units.index(it[-1])][-1] -= 1
                        elif self.resv[self.units.index(temp[2])][0] == 0:
                            self.resv[self.units.index(it[-1])][2] = 'M()'
                            self.resv[self.units.index(it[-1])][-1] -= 1
                    else:
                        # 若不能，判断是否准备就绪，通过CDB运输计算好的数据到vj/vk
                        # temp = busy,op,vj,vk,qj,qk,time
                        if not temp[2] and self.resv[self.units.index(temp[4])][0] == 0:
                                self.resv[self.units.index(it[-1])][2] = 'M()'
                                self.resv[self.units.index(it[-1])][4] = 0
                        if not temp[3] and self.resv[self.units.index(temp[5])][0] == 0:
                                self.resv[self.units.index(it[-1])][3] = 'M()'
                                self.resv[self.units.index(it[-1])][5] = 0
                                
                        temp = self.resv[self.units.index(it[-1])] 
                        if temp[2] and temp[3]:
                            self.resv[self.units.index(it[-1])][-1] -= 1
                    if self.resv[self.units.index(it[-1])][-1] == 0:
                        it[1] = self.clock # tag the exe cycle
    
    def isFinished(self):
        for inst,it in self.inst_status:                    
            if it[-1] != 1:
                return False
        return True
    def output(self,path):
        with open(path,'a') as f:
            f.write(f"\n\n//Cycle_{self.clock}\n")
            f.write(f'//Reservation Stations(Add:{self.numadd}, Multd:{self.nummul}) & Load({self.numld}) & Store({self.numsd})\n')
            for i,item in enumerate(self.units):
                f.write(f"{item}: ")
                if self.resv[i][0] == 0:
                    f.write('No')
                else:
                    f.write('Yes')
                for t in self.resv[i][1:-1]: 
                    f.write(', ')
                    if t != 0:
                        f.write(f'{t}')
                    
                f.write(';\n')
            f.write(f'//Registers(max:{self.max_reg})\n')
            for i,r in enumerate(self.reg):
                if i % 2 == 0:
                    f.write(f"F{i}: {r}; ")
            f.write('\n//Instruction status\n')
            for inst,t in self.inst_status:
                for i in inst:
                    f.write(f"{i} ")
                f.write(': ')
                for i in t[:-1]:
                    f.write(f"{i} ")
                f.write(';\n')
        f.close()
        
        
    def run(self,input,output):
        a.input(input)
        while not self.isFinished() or self.clock == 0:           
            self.next()
            self.output(output)

# change the path of your input file and output file here
input = 'input2.txt'
output = 'output2.txt'
a = tomasulo(ld=2,sd=2,add=2,sub=2,mul=10,div=20)
a.run(input,output)