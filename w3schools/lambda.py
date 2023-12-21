# 当涉及到比较简单的函数功能时，可以使用 python 的 lambda 表达式 

# lambda 表达式的语法是: lambda arguments: expression

# <=================示例一==================>

# 将两个数相加
add = lambda x , y : x + y

print("add(2, 3) => ", add(2, 3))

# <=================示例二==================>

# 求一个数的平方
square = lambda x : x**2

print("square(4) => ", square(4))

# <=================示例三==================>

# 获取字符串的长度
str_len = lambda str : len(str)

print("str_len('abcde') => ", str_len("abcde"))