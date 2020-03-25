# _*_ coding:utf-8 _*_
__author__ = 'cc'
__date__ = '2019/6/11 16:59'

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
#from django_redis import get_redis_connection


#任务处理者（服务器）所用到的初始化
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ttsx2.settings")
# django.setup()

from goods.models import GoodsType,IndexGoodsBanner,IndexTypeGoodsBanner
from django.template import loader

#创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks',broker='redis://192.168.2.127:6379/9') #第一个参数为对象名，一般写路径名，broker:连接中间件redis，后面数字表示第几个数据库，最多到第15个

#定义任务函数
@app.task   #必须要有   对函数进行装饰
def send_register_active_email(to_email,username,token):
    """
    发送激活邮件
    :param to_email:
    :param username:
    :param token:
    :return:
    """
    subject = 'ttsx欢迎信息'
    message = '{0},欢迎您，请点击下面链接激活您的账户:http://127.0.0.1:8000/user/active/{1}'.format(username, token)
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    send_mail(subject, message, sender, receiver)

@app.task
def generate_static_index_html():
    """产生首页静态页面"""
    # 获取商品种类信息
    print(2222)
    types = GoodsType.objects.all()

    # 获取轮播图信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
        # 获取type种类首页分类商品的文字展示信息
        titile_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = titile_banners

    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,

    }

    # 使用模板
    #1.加载模板文件
    temp = loader.get_template('static_index.html')
    #2.渲染模板
    static_index_html = temp.render(context)
    #3.生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR,'static/index.html')
    with open(save_path,'w') as f:
        f.write(static_index_html)
