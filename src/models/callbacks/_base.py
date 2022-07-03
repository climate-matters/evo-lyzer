__all__ = [
    'Callback',
    'CallbackList',
]


class Callback:
    def __init__(self):
        self._model = None

    def on_train_start(self, logs=None):
        pass

    def on_train_end(self, logs=None):
        pass

    def on_train_batch_start(self, batch, logs=None):
        pass

    def on_train_batch_end(self, batch, logs=None):
        pass

    def on_test_batch_start(self, batch, logs=None):
        pass

    def on_test_batch_end(self, batch, logs=None):
        pass

    def on_predict_batch_start(self, batch, logs=None):
        pass

    def on_predict_batch_end(self, batch, logs=None):
        pass

    def on_epoch_start(self, epoch, logs=None):
        pass

    def on_epoch_end(self, epoch, logs=None):
        pass

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value


class CallbackList(Callback):
    """Holds a list of callbacks."""

    def __init__(self, callbacks=None):
        super(CallbackList, self).__init__()
        self._callbacks = callbacks

    def __getattribute__(self, item):
        if item in [
            'on_train_start', 'on_train_end',
            'on_train_batch_start', 'on_train_batch_end',
            'on_test_batch_start', 'on_test_batch_end',
            'on_predict_batch_start', 'on_predict_batch_end',
            'on_epoch_start', 'on_epoch_end',
        ]:
            def apply_callback(*args, **kwargs):
                """Apply callback for all callbacks registered in this list of callbacks.

                :param args: args
                :param kwargs: kwargs
                """
                for c in self._callbacks:
                    if hasattr(c, item):
                        getattr(c, item)(*args, **kwargs)

            return apply_callback
        else:
            return super(CallbackList, self).__getattribute__(item)
