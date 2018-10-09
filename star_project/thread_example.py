import threading
import time


def worker(result):
    """thread worker function"""
    time.sleep(1)
    print('Done sleeping')
    result["result_1"] = "Andre"
    return "Andre"


result = {"result_1": 0}
my_thread = threading.Thread(target=worker, args=result)
print("About to start thread")
result = my_thread.start()
print("Thread returned", result)
time.sleep(1.5)
print("Result: ", result)


# threads = []
# for i in range(5):
#     t = threading.Thread(target=worker)
#     threads.append(t)
#     t.start()
