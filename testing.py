from classes import Timer

@Timer(name="download", text="Downloaded the tutorial in {:.2f} seconds")
def dosome():
    meow = []
    for i in range(10000):
        meow.append('meow')
    print(meow)

@Timer(name="multiply", text="and multiply in {:.2f} seconds")
def domore():
    total = 0
    for x in range(30000000):
        total += x
    print(total)

domore()
dosome()
domore()

print(Timer.timers)