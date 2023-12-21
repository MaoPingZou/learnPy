# 多位置参数的函数定义方法

# 如果不知道将传递给函数的参数数量是多少，可以在函数入参定义中添加一个 * 作为前缀。

# 当这个时候，其实入参 *args 类型是一个 元组。

# <=================示例一==================>

def multi_param_0(*args):
  print("*args 的类型是：", type(args))

# 输出：*args 的类型是： <class 'tuple'>
multi_param_0("1", "2", "3")

# <=================示例二==================>

def multi_param_1(*args):
  print("第二个参数是：" + args[2])

# 输出：第二个参数是：3
multi_param_1("1", "2", "3")

# <=================示例三==================>

def multi_param_2(*args):
    for arg in args:
        print(arg)

# 输出
# 1
# 2
# 3
multi_param_2("1", "2", "3")
