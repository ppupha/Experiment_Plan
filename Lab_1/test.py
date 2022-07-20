class Obj:
    def __init__(self):
        print("Call Init")

    def __del__(self):
        print("CAll Dell")

    def say(self):
        print("Hello")


o = Obj()
del o
o.say()


