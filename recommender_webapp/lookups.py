from ajax_select import register, LookupChannel
from .models import Comune


@register('cities')
class TagsLookup(LookupChannel):

    model = Comune

    def check_auth(self, request):
        return True

    def get_query(self, q, request):
        return self.model.objects.filter(nome__icontains=q).order_by('nome')

    def get_result(self, obj):
        """ result is the simple text that is the completion of what the person typed """
        return obj.nome

    def format_match(self, obj):
        """ (HTML) formatted item for display in the dropdown """
        return self.format_item_display(obj)

    def format_item_display(self, item):
        """ (HTML) formatted item for displaying item in the selected deck area """
        return u"<span class='tag'>%s</span>" % item.nome