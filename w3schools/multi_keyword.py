# 多关键字参数的函数定义方法

# 如果不知道将传递给函数的关键词数量是多少，可以在函数入参定义中添加两个 ** 作为前缀。

# 此时，**kwargs 是一个包含所有传入关键字参数的 字典

# <=================示例一==================>

def multi_keywordargs_0(**kwargs):
  print("**kwargs 的类型是：", type(kwargs))

# 输出：*args 的类型是： <class 'dict'>
multi_keywordargs_0(a="1", b="2", c="3")

# <=================示例二==================>

def multi_kwargs_1(**kwargs):
  print("小明的英文名是： " + kwargs["e_name"])

# 输出：小明的英文名是： Billy
multi_kwargs_1(e_name="Billy", age=20)

# <=================示例三==================>

def multi_param_2(**kwargs):
    for k, v in kwargs.items():
        print(k, " 的中文名是：", v)

# 输出：
# apple  的中文名是： 苹果
# banana  的中文名是： 香蕉
# orange  的中文名是： 橙子
multi_param_2(apple="苹果", banana="香蕉", orange="橙子")
