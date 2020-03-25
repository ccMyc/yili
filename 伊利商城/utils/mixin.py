# _*_ coding:utf-8 _*_
__author__ = 'cc'
__date__ = '2019/6/12 16:04'

from django.contrib.auth.decorators import login_required
class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        #调用父类的as_view
        view = super(LoginRequiredMixin,cls).as_view(**initkwargs)
        return login_required(view)