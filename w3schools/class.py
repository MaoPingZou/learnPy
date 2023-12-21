# python 的类

# 定义一个类使用 class 关键字
# 定义一个类的初始化方法名使用：__init__
# 注意：
#      如果通过 __init__ 方法定义了类的初始化方法，那么类中的其他方法都
#      需要加上 self 参数。
# 
#      因为在 Python 中，类的成员方法默认会将类的实例作为第一个参数传递，
#      通常习惯将这个参数命名为 self，以便在方法内部引用实例的属性和方法。

# 定义一个类
class MyClass:
    # 变量
    x = 8

    # 初始化方法
    def __init__(self, name, age):
        self.name = name
        self.age = age

    # 辅助查看初始化方法的效果
    def display_init(self):
        print(f"名字是：{self.name}, 年龄是：{self.age}")

    # 普通方法
    def my_func(self):
        print("这是一个普通方法")

# 创建一个类的对象
my_class_obj = MyClass("小明", 27)

# 获取类中的变量
print("类中的变量 x 的值是：", my_class_obj.x)

# 类在创建对象时已经初始化
my_class_obj.display_init()

# 调用类中的普通方法
my_class_obj.my_func()

