from ycrawldataprocessor.FileController import *
from ycrawldataprocessor.FileProcessor import *

def donotrun():
    # from ycrawldataprocessor.test import *
    fc = FileController(testnum=0)
    fc.reset_batch()
    flag = True

    processor_threads = []
    while flag: 
        flag, filelist = fc.get_next_batch()
        t = FileProcessor(filelist, fc.BUCKET_NAME, f"{fc.index_for_the_batch:04}")
        processor_threads.append(t)
        t.start()

    for t in processor_threads:
        t.join()

    print("done")
