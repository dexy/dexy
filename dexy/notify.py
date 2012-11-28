class Notify(object):
    def __init__(self, batch):
        self.batch = batch
        self.channels = {}

    def subscribe(self, channel, callback):
        if not channel in self.channels:
            self.batch.wrapper.log.debug("creating new notification channel '%s'" % channel)
            self.channels[channel] = []

        if not callback in self.channels[channel]:
            self.channels[channel].append(callback)

    def notify(self, channel, arg):
        if not self.channels.get(channel):
            self.batch.wrapper.log.warn("trying to pass message '%s' to nonexistent channel %s" % (arg, channel))
        else:
            for callback in self.channels[channel]:
                callback(arg)
