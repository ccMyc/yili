# 添加商品购物车：
# (1)请求方式，采用ajax
#       如果涉及到数据的修改（新增，更新，删除）,采用post
#       如果只涉及到数据的获取，采用get
# (2)传递的参数：商品id  商品数量
#     Get传参：/cart/add?sku_id=1&count=3
# 	  Post传参：{‘shu_id’:1,’count’:3}
# 	  url传参：url配置时捕获参数

#ajax发起的请求都在后台，在浏览器中看不到效果
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse

from goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

#/cart/add
#购物车添加类使用了ajax post请求，这里不能使用LoginRequiredMixin类判断用户是否登录
#使用if not user.is_authenticated判断用户登录
class CartAddView(View):
    """购物车记录添加"""
    def post(self,request):
        """购物车记录添加"""
        print("1111")
        user = request.user
        if not user.is_authenticated:
            #用户未登录
            return JsonResponse({'res':0,'errmsg':'用户未登录'})
        #接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        #数据校验
        if not all([sku_id,count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            #数目出错
            return JsonResponse({'res':2,'errmsg':'商品数目出错'})
        #校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            #商品不存在
            return  JsonResponse({'res':3,'errmsg':'商品不存在'})

        # 业务处理：添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        #先尝试获取sku_id的值 ->  hget cart_key 属性
        #如果sku_id在hash不存在，hget返回None
        cart_count = conn.hget(cart_key,sku_id)
        if cart_count:
            #累加购物车中商品的数目
            count += int(cart_count)
        #校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品不足'})
        #设置hash中sku_id对应的值
        #hset  如果sku_id已经存在，更新数据，如果sku_id不存在，添加数据
        conn.hset(cart_key,sku_id,count)

        #计算用户购物车商品的条目数
        total_count = conn.hlen(cart_key)
        #返回
        return JsonResponse({'res':5,'total_count':total_count,'message':'添加成功'})

#在CartInfoView显示购物车信息中，没有结束ajax post请求，则可以使用LoginRequiredMixin类判断用户是否登录
class CartInfoView(LoginRequiredMixin,View):
    """购物车页面显示"""
    def get(self,request):
        #获取登录的用户
        user = request.user
        #获取用户购物车中商品的信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        cart_dict = conn.hgetall(cart_key)

        skus = []
        #保存用户购物车中商品的总数目和总价格
        total_count = 0
        total_price = 0
        #遍历获取商品的信息
        for sku_id,count in cart_dict.items():
            #根据商品的id，获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            #计算商品的小计
            amount= sku.price*int(count)
            #动态给sku对象增加一个熟悉amount,保存商品的小计
            sku.amount = amount
            #动态给sku对象增加一个熟悉count,保存商品的数量
            sku.count = int(count)
            #添加
            skus.append(sku)

            #累加计算商品的总数目和总价格
            total_count += int(count)
            total_price += amount

        #组织上下文
        context = {
            'total_count':total_count,
            'total_price':total_price,
            'skus':skus
        }
        return render(request,'cart.html',context)

class CartUpdateView(View):
    """购物车记录添加"""
    def post(self,request):
        """购物车记录添加"""
        user = request.user
        if not user.is_authenticated:
            #用户未登录
            return JsonResponse({'res':0,'errmsg':'用户未登录'})
        #接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        #数据校验
        if not all([sku_id,count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            #数目出错
            return JsonResponse({'res':2,'errmsg':'商品数目出错'})
        #校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            #商品不存在
            return  JsonResponse({'res':3,'errmsg':'商品不存在'})

        # 业务处理：添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        #先尝试获取sku_id的值 ->  hget cart_key 属性
        #如果sku_id在hash不存在，hget返回None

        #校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品不足'})
        #设置hash中sku_id对应的值
        #hset  如果sku_id已经存在，更新数据，如果sku_id不存在，添加数据
        conn.hset(cart_key,sku_id,count)

        #计算用户购物车商品的总件数
        total_count= 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        #返回
        return JsonResponse({'res':5,'total_count':total_count,'message':'添加成功'})


class CartDelView(View):
    """购物车记录删除"""
    def post(self,request):
        """购物车记录添加"""
        user = request.user
        if not user.is_authenticated:
            #用户未登录
            return JsonResponse({'res':0,'errmsg':'用户未登录'})
        #接收数据
        sku_id = request.POST.get('sku_id')
        print("*"*20)
        print(sku_id+"0000000000000")
        #数据校验
        if not sku_id:
            return JsonResponse({'res':1,'errmsg':'数据不完整'})

        #校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            #商品不存在
            return  JsonResponse({'res':2,'errmsg':'商品不存在'})

        # 业务处理：添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        #删除 hdel
        conn.hdel(cart_key,sku_id)

        # 计算用户购物车商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        #返回
        return JsonResponse({'res':3,'total_count':total_count,'message':'添加成功'})