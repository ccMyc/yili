from django.contrib import admin
from django.core.cache import cache
from .models import GoodsSKU,GoodsImage,GoodsType,GoodsSPU,IndexGoodsBanner,IndexTypeGoodsBanner
# Register your models here.

class BaseModelAdmin(admin.ModelAdmin):
    """新增或更新表中数据时调用"""
    def save_model(self, request, obj, form, change):
        super().save_model(request,obj,form,change)
        #发出任务，让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        #更新缓存数据方法     清除首页的存储缓存   重新存储缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除表中的数据时调用"""
        super().delete_model(request,obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 更新缓存数据方法     清除首页的存储缓存   重新存储缓存
        cache.delete('index_page_data')

class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass
class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass
class GoodsTypeAdmin(BaseModelAdmin):
    pass
class GoodsSKUAdmin(BaseModelAdmin):
    pass
class GoodsSPUAdmin(BaseModelAdmin):
    pass

admin.site.register(GoodsSKU,GoodsSKUAdmin)
admin.site.register(GoodsSPU,GoodsSPUAdmin)
admin.site.register(IndexGoodsBanner,IndexGoodsBannerAdmin)
admin.site.register(GoodsType,GoodsTypeAdmin)
admin.site.register(IndexTypeGoodsBanner,IndexTypeGoodsBannerAdmin)
