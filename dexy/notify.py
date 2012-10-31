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

    def notify(self, channel, *args):
        if not self.channels.get(channel):
            self.wrapper.log.warn("Trying to pass message '%s' to nonexistent channel %s" % (args, channel))
        else:
            self.wrapper.log.debug("Sending message '%s' on channel '%s'" % (args, channel))
            for callback in self.channels[channel]:
                self.wrapper.log.debug("Passing message to callback '%s'..." % callback)
                callback(*args)
