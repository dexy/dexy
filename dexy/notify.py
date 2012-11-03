class Notify(object):
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.channels = {}

    def subscribe(self, channel, callback):
        if not channel in self.channels:
            self.wrapper.log.debug("Creating new notification channel '%s'" % channel)
            self.channels[channel] = []

        if not callback in self.channels[channel]:
            self.channels[channel].append(callback)

    def notify(self, channel, arg):
        if not self.channels.get(channel):
            self.wrapper.log.warn("Trying to pass message '%s' to nonexistent channel %s" % (arg, channel))
        else:
            for callback in self.channels[channel]:
                callback(arg)
