# a = [1,2,3,4,5]
# l = [list(map(lambda i:i+3,a[::2]))]
# b=list(map(lambda i:i+3,a[0::2]))
# print(b)

from random import shuffle

a = [1, 2, 3, 4, 5]

# 打乱列表a的元素顺序
shuffle(a)

# 对a进行排序得到列表b
b = sorted(a, reverse=True)

# zip 并行迭代，将两个序列“压缩”到一起，然后返回一个元组列表，最后，转化为字典类型。
