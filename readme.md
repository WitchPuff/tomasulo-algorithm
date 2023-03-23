# Computer Architecture - Tomasulo Algorithm

## Summary

Implement the Tomasulo Algorithm in Python. Run the given instruction set with it and print out the reservation stations, load/store buffer status, function unit of every cycle, in addition to the cycle  that the instructions are issued, executed and written back.

Assumed condition: single-issue Tomasulo MIPS pipeline architecture with 3 adder units and 2 multipler units in the reservation stations, 3 buffers separately for Load/Store operations.

The maximum number of register in the function unit is F30.

There are 6 kinds of instructions in the example input.

| Instruction | Exec Time |
| ----------- | --------- |
| LD          | 2         |
| SD          | 2         |
| ADDD        | 2         |
| SUBD        | 2         |
| MULTD       | 10        |
| DIVD        | 20        |

You could change these parameters in the tomasulo class defined in `tomasulo.py`.



## Run

Firstly, edit the path of your input file and output file in `tomasulo.py`.

```python
# change the path of your input file and output file here
input = 'input2.txt'
output = 'output2.txt'
a = tomasulo(ld=2,sd=2,add=2,sub=2,mul=10,div=20)
a.run(input,output)
```

Then run the code.

```shell
python tomasulo.py
```

You could use `Tomasulo.exe` to validate your results in details.

You could see the exampless of input and output in  `output.txt` and `output2.txt` .
