from django.shortcuts import render
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from django.views import View
from django.core.cache  import cache

from .models import IndexGoodsBanner,IndexTypeGoodsBanner,GoodsType,GoodsSKU
from order.models import OrderGoods

from django_redis import get_redis_connection
from pure_pagination import PageNotAnInteger,EmptyPage,Paginator

# Create your views here.

class IndexView(View):
    def get(self,request):
        """显示首页"""
        #尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            """设置缓存"""
            #如果缓存中没有数据
            types = GoodsType.objects.all()
            #获取轮播图信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            #获取首页分类商品展示信息
            for type in types:
                #获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1)[:4]
                #获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0)

                #动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners
                # 组织模板上下文
            context = {
                'types': types,
                'goods_banners': goods_banners,
            }
            # 设置缓存 key(缓存名) value(缓存内容) timeout(可选 缓存时间)
            cache.set("index_page_data", context, 3600)

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        #更新context
        context.update(cart_count=cart_count)
        return render(request,'index.html',context)

# /goods/商品id
class DetailView(View):
    def get(self,request,good_id):
        try:
            sku = GoodsSKU.objects.get(id=good_id)
        except GoodsSKU.DoesNotExist:
            return HttpResponseRedirect(reverse('goods:index'))
        # 获取商品分类信息
        types = GoodsType.objects.all()
        #获取商品评论信息       exclude():排除函数   排除评论为空的字段
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        #获取同一个SPU的其他规格商品   exclude():排除本身的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=good_id)
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)            #hlen 获取hash表中字段的数量。

            # 添加用户浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            #移除good_id所有浏览记录
            #redis列表移除命令lrem（key,count,value）
            # :注 count>0:从表头向表尾搜索，移除与value相等的元素，数量为count.
            #     count<0:从表尾向表头搜索，移除与value相等的元素，数量为count的绝对值.
            #     count=0：移除表中与所有value相等的元素。
            conn.lrem(history_key, 0, good_id)
            #把good_id插入到列表的左侧
            conn.lpush(history_key,good_id)
            #只保存用户最新浏览的5条信息
            conn.ltrim(history_key,0,4)


        context = {
            'types': types,
            'sku': sku,
            'sku_orders':sku_orders,
            'new_skus': new_skus,
            'cart_count':cart_count,
            'same_spu_skus':same_spu_skus,

        }
        return render(request,'detail.html',context)


#种类id 页码 排序方式
#/list/种类id/页码?sort=排序方式
class goods_listView(View):
    def get(self,request,type_id,pages):
        """显示列表页"""
        # 获取种类信息’
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            #种类不存在
            return HttpResponseRedirect(reverse('goods:index'))

        #获取商品的分类信息
        types = GoodsType.objects.all()
        skus = GoodsSKU.objects.filter(type=type)

        #获取排序的方式
        #sort=default 按默认id排序    price:价格   hot:销量
        sort = request.GET.get('sort','default')
        if sort == 'default':
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        if sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')

        new_skus = GoodsSKU.objects.all().order_by('-sales')[:2]


        # try:
        #     page = request.GET.get(pages,1)
        # except PageNotAnInteger:
        #     page = 1
        # paginator = Paginator(skus,1,request=request)
        # sku_page = paginator.page(page)

        # 对数据进行分页
        paginator = Paginator(skus,1)
        # 获取第page页的内容
        try:
            page = int(pages)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        sku_page = paginator.page(page)

        # todo:进行页码的控制，页面上最多显示5个页码
        # 1. 总页数小于5页，页面上显示所有页码
        # 2. 如果当前页是前3页，显示1-5页
        # 3. 如果当前页是后3页，显示后5页
        # 4. 其他情况，显示当前页的前2页，当前页，当前页后两页。
        num_pages= paginator.num_pages
        if num_pages<5:
            pages = range(1,num_pages+1)
        elif page <= 3:
            pages = range(1,6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4,num_pages+1)
        else:
            pages = range(page-2,page+3)

        content = {
            'types':types,
            'type':type,
            'skus':skus,
            'sku_page':sku_page,
            'pages':pages,
            'new_skus':new_skus,
            'sort':sort,
        }
        return render(request,'list.html',content)