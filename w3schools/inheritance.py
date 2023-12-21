# Python 类的继承

# 继承使得类之间的关系更加灵活，可以实现代码的重用和扩展。
# 子类可以继承父类的特性，并且可以在其基础上添加新的属性和方法，以满足特定的需求。

# 定义方法为 class Child(Parent) 的格式
# <====================================>

# 创建父类
class Parent:
    # 父类的初始化方法
    def __init__(self, parent_attr):
        self.parent_attr = parent_attr
    
    # 父类方法
    def parent_method(self):
        print("调用了父类方法")

class Child(Parent):
    # 子类的初始化方法
    def __init__(self, parent_attr, child_attr):
        super().__init__(parent_attr)
        self.child_attr = child_attr
    
    # 子类方法
    def child_method(self):
        print("调用了子类方法")

# 创建子类的实例
child_obj = Child("父类属性", "子类属性")

# 调用继承的父类方法
child_obj.parent_method()
# 调用子类本身的方法
child_obj.child_method()

# 调用继承的父类方法
print("父类属性：", child_obj.parent_attr)
# 调用子类本身的方法
print("子类属性：",child_obj.child_attr)