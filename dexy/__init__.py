def run(*args, **kwargs):
    from dexy.wrapper import Wrapper
    wrapper = Wrapper(*args, **kwargs)
    wrapper.run()
    wrapper.report()
