from src import VirtualTradeMachine as vtm

def strategy():
    vtm.setup()

    while True:
        vtm.next_time()
