from handlers.python import HeadHandler
import helper

def test_process_text():
    helper.test_process_text(HeadHandler(), 'head.txt')

def test_process():
    helper.test_process(HeadHandler(), 'head.txt', 'process_text')

