from django.core.paginator import Paginator, InvalidPage, EmptyPage


class Page(object):
    """
    数据库分页相关逻辑
    """

    def __init__(self, objects, page_count):
        """

        :param objects: query set
        :param page_count: 一页的数量
        """
        self.objects = objects
        self.page_count = page_count
        self.page_index = 1
        self.paginator = Paginator(self.objects, self.page_count)

    def page(self, page_index):
        objs = []
        total_page = 1
        total_count = 0

        try:
            self.page_index = int(page_index)
        except Exception as e:
            self.page_index = 1

        try:
            page_obj = self.paginator.page(self.page_index)

            objs = page_obj.object_list
            total_page = page_obj.paginator.num_pages
            total_count = page_obj.paginator.count
        except Exception as e:
            objs = []

        return {
            'objects': objs,
            'page_index': self.page_index,
            'page_size': self.page_count,
            'total_page': total_page,
            'total_count': total_count
        }
