from django.shortcuts import render,get_object_or_404
from django.views.generic import View
from django.conf import settings
from django.contrib.auth import authenticate,login,logout
from django.urls import reverse
from django.http import HttpResponseRedirect,HttpResponse
from django_redis import get_redis_connection
from django.core.paginator import Paginator

from .forms import RegisterForm,LoginForm,AddressForm
from .models import Address,UserProfile as User
from goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin
from order.models import OrderInfo,OrderGoods

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email,send_mail

import re

class RegisterView(View):
    def get(self,request):
        return render(request,'register.html',{})
    def post(self,request):
        forms = RegisterForm(request.POST)
        if forms.is_valid():
            username = forms.cleaned_data['username']
            password = forms.cleaned_data['password2']
            email = forms.cleaned_data['email']

            user = User.objects.create_user(username=username,password=password,email=email)
            user.is_active=0
            user.save()

            #发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/1
            #激活链接中需要包含用户的身份信息   并且要把身份信息进行加密
            #加密用户的身份信息，生成激活token
            serializer = Serializer(settings.SECRET_KEY,3600)   #实例化对象
            info = {'confirm':user.id}
            token = serializer.dumps(info)          #加密  bytes类型
            token = token.decode()    #解码   字符串
            #发邮件
            # subject = 'ttsx欢迎信息'
            # message = '{0},欢迎您，请点击下面链接激活您的账户:http://127.0.0.1:8000/user/active/{1}'.format(username, token)
            # sender = settings.EMAIL_FROM
            # receiver = [email]
            # send_mail(subject, message, sender, receiver)
            send_register_active_email.delay(email,username,token)

        return render(request, 'register.html', {'msg':forms})

class ActiveView(View):
    def get(self,request,token):
        serializer = Serializer(settings.SECRET_KEY, 3600)      #实例化对象

        try:
            info = serializer.loads(token)
            #获取待激活用户的id
            user_id = info['confirm']
            #根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            #跳转到登录页面
            return HttpResponseRedirect(reverse('login'))

        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse("激活链接已过期")

class LoginView(View):
    def get(self,request):
        #判断是否记住了用户名
        print(request)
        print("*********************")
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            pwd = login_form.cleaned_data['pwd']
            #cache.set('name2','cc',timeout=None)
            user = authenticate(username=username,password=pwd)
            if user is not None:
                login(request,user)
                #获取登录后所要跳转的地址，如果没有则goods：index
                next_url = request.GET.get('next', reverse('goods:index'))
                response = HttpResponseRedirect(next_url)
                #判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    #记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg':'账号未激活'})

                # return HttpResponseRedirect(next_url)
        else:
            return render(request,'login.html',{})


class LogoutView(View):
    def get(self,request):
        #清除用户的session信息
        logout(request)
        #跳转到登录页面
        return HttpResponseRedirect(reverse('login'))


class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        page = 'info'

        #获取用户信息
        user = request.user
        #获取用户默认收货地址
        address = Address.objects.get_default_address(user=user)

       #获取用户的历史浏览记录
        #原生redis连接
        # from redis import StrictRedis
        # sr = StrictRedis(host='192.168.2.127',port='6379',db=2)
        #调用redis作为django缓存的连接
        con = get_redis_connection('default')
        history_key = 'history_%d'%user.id

        #获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key,0,4)

        #从数据库中查询用户浏览的商品具体信息
        goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        #遍历获取用户浏览的商品信息
        goods_li =[]
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        #组织上下文
        context = {
            'page':'user',
            'address':address,
            'goods_li':goods_li
        }
        # request.user.is_authenticated()
        # 除了你给模板文件传递的模板变量之外，
        # django框架会把request.user也传给模板文件（也就是说你可以直接在模板文件使用user.is_authenticated()进行判断）
        return render(request,'user/user_center_info.html',context)


    # def get(self,request):
    #     page = 'info'
    #     #获取用户信息
    #     user = request.user
    #     #获取用户默认收货地址
    #     address = Address.objects.get_default_address(user=user)
    #
    #     # 获取用户的历史浏览记录
    #     # from redis import StrictRedis
    #     # sr = StrictRedis(host='172.16.179.130', port='6379', db=9)
    #     # con = get_redis_connection('default')
    #
    #     history_key = 'history_%d' % user.id
    #
    #     # 获取用户最新浏览的5个商品的id
    #     # sku_ids = con.lrange(history_key, 0, 4)  # [2,3,1]
    #
    #     # 遍历获取用户浏览的商品信息
    #     goods_li = []
    #     # for id in sku_ids:
    #     #     goods = GoodsSKU.objects.get(id=id)
    #     #     goods_li.append(goods)
    #     return render(request,'user/user_center_info.html',{'page':page,'address':address,'goods_li':goods_li})

#用户中心订单页
class UserOrderView(LoginRequiredMixin,View):
    def get(self,request,page):
        page = 'order'
        #获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('order_id')
        for order in orders:
            order_skus = OrderGoods.objects.filter(order=order.order_id)
            #遍历order_skus计算商品的小计
            for order_sku in order_skus:
                #计算小计
                amount = order_sku.count*order_sku.price
                #动态给order_sku增加属性amount，保存订单商品的小计
                order_sku.amount = amount

            #动态给order增加属性，保存订单状态标题
            order.status.name = OrderInfo.ORDER_STATUS[order.order_status]
            #动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        #分页
        paginator = Paginator(orders,1)
        print(paginator.num_pages)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo:进行页码的控制，页面上最多显示5个页码
        # 1. 总页数小于5页，页面上显示所有页码
        # 2. 如果当前页是前3页，显示1-5页
        # 3. 如果当前页是后3页，显示后5页
        # 4. 其他情况，显示当前页的前2页，当前页，当前页后两页。
        num_pages = paginator.num_pages
        print(num_pages)
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        #组织上下文
        context = {'order_page':order_page,
                   'pages':pages,
                   'page':'order'}

        return render(request,'user/user_center_order.html',context)


#地址
class UserSiteView(LoginRequiredMixin,View):
    def get(self,request):
        page = 'site'
        user = request.user
        # 获取用户默认地址
        address = Address.objects.get_default_address(user=user)

        return render(request,'user/user_center_site.html',{'page':page,'address':address})

    def post(self,request):
        """地址的添加"""
        #接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone =request.POST.get('phone')
        print(receiver,addr,zip_code,phone)
        #校验数据
        if not all([receiver,addr,phone]):
            # print("11")
            return render(request,'user/user_center_site.html',{'errmsg':"数据不完整"})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone):
            # print("22")
            return render(request,'user/user_center_site.html',{'errmsg':"手机格式错误！"})

        #地址添加
        user = request.user

        # 获取用户默认地址
        address = Address.objects.get_default_address(user=user)

        if address:
            is_default = False
        else:
            is_default = True
        # print(address.is_default)
        Address.objects.create(user=user,receiver=receiver,address=addr,phone=phone,is_default=is_default)
        # Address.save()
        # return render(request,'user/user_center_site.html',{'form_add':form_add})
        return HttpResponseRedirect(reverse('user:site'))
