global is_test_global

def is_test():
    global is_test_global
    return is_test_global if 'is_test_global' in globals() else False

def set_is_test(is_test_var):
    global is_test_global
    is_test_global = is_test_var