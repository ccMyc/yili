from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

from db.base_model import BaseModel

# Create your models here.

class UserProfile(AbstractUser,BaseModel):

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.username

    # def get_address(self):
    #     return self.address_set.get(user=self.username)

class AddressManager(models.Manager):
    """地址模型管理器类"""
    #应用场景
   #1.改变原有查询的结果集：all()
   #2.封装方法：用户操作模型类对应的数据表（增删改查）
    def get_default_address(self,user):

       """获取用户默认收货地址"""
       #self.model:获取self对象所在的模型类
       #self可直接调用我们models.Manager get方法
       try:
           address = self.get(user=user,is_default=True)  # 使用到了默认的模型管理器：models.Manage(address.objects)
       except self.model.DoesNotExist:

           address = None
       return address


class Address(BaseModel):
    """
    地址模型类
    """
    user = models.ForeignKey(UserProfile,on_delete=models.CASCADE,verbose_name='所属用户')
    receiver = models.CharField(max_length=20,verbose_name='收件人')
    address = models.CharField(max_length=256,verbose_name='收件地址')
    zip_code = models.CharField(max_length=6,null=True,verbose_name='邮政编码')
    phone = models.CharField(max_length=11,verbose_name='联系电话')
    is_default = models.BooleanField(default=False,verbose_name='是否默认地址')

    #自定义一个模型管理器对象
    objects = AddressManager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name

