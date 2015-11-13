__author__ = 'mpa'

import logging

from sm.so.service_orchestrator import LOG


class FactoryServiceAdapter(object):

    @staticmethod
    def get_agent(module, cl, **kwargs):
        _package = "adapters"
        _module = module
        _class = cl
        LOG.debug("Instantiating %s from %s.%s"%(_class, _package,_module))
        try:
            _loaded_module = __import__(name='%s.%s' % (_package,_module), fromlist=[_module])
        except ImportError, exc:
            exc.message = 'FactoryServiceAdapter -> %s' % exc.message
            LOG.exception(exc)
            raise ImportError(exc.message)
        try:
            _loaded_class = getattr(_loaded_module, _class)
        except AttributeError, exc:
            exc.message = 'FactoryServiceAdapter -> %s' % exc.message
            LOG.exception(exc)
            raise AttributeError(exc.message)
        try:
            if len(kwargs) != 0:
                _instance = _loaded_class(**kwargs)
            else:
                _instance = _loaded_class()
        except TypeError, exc:
            needed_parameters = list(_loaded_class.__init__.func_code.co_varnames[1:_loaded_class.__init__.func_code.co_argcount])
            exc.message = 'FactoryServiceAdapter -> %s.%s. (args=%s)' % (_loaded_class.__name__,exc.message,needed_parameters)
            LOG.exception(exc)
            raise TypeError(exc.message)
        return _instance