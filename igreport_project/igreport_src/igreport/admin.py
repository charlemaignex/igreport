from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.forms import ModelForm, ModelChoiceField
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location
from igreport.models import IGReport, UserProfile, Category, Unprocessed
from igreport import media
from igreport.html.admin import ListStyleAdmin

class IGReportAdmin(admin.ModelAdmin, ListStyleAdmin):

    list_display = ['sender', 'message', 'accused', 'amount_formatted', 'report_time', 'options']
    list_filter = ['datetime']
    ordering = ['-datetime']
    #date_hierarchy = ['datetime'] # causes strange "ImproperlyConfigured" exception
    search_fields = ['connection__identity']
    actions = None
    Media = media.JQueryUIMedia
    change_list_template = 'igreport/change_list.html'
    change_list_results_template = 'igreport/change_list_results.html'

    def __init__(self, *args, **kwargs):
        super(IGReportAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)

    def accused(self, obj):
        return obj.subject

    accused.short_description = 'Accused'

    def report_time(self, obj):
        return obj.datetime.strftime('%d/%m/%Y %H:%M')

    report_time.short_description = 'Report Date'
    report_time.admin_order_field = 'datetime'

    def message(self, obj):
        text = obj.report
        width = ''
        if len(text) > 50:
            width = '300px'
        else:
            html = text
        style = ''
        if width:
            style += 'width:%s;' % width
        if style:
            style = ' style="%s"' % style
        html = '<div id="rpt_%s"%s>%s</div>' % (obj.id, style, text)
        return html

    message.short_description = 'Report'
    message.allow_tags = True

    def sender(self, obj):
        msisdn = obj.connection.identity
        t = (msisdn, msisdn, msisdn)
        html = '<a href="../unprocessed/?q=%s" \
               style="font-weight:bold" title="Click to view unprocessed messages from %s">%s</a>' % t
        return html
    
    sender.short_description = 'Sender'
    sender.admin_order_field = 'connection'
    sender.allow_tags = True

    def amount_formatted(self, obj):
        if obj.amount:
            return int(obj.amount)
        return 'NA'
    
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'

    def options(self, obj):
        html = ''
        if not obj.synced:
            link = '<a href="" onclick="editrpt(%s);return false;" title="Edit Report"><img src="%s/igreport/img/edit.png" border="0" /></a>&nbsp;&nbsp;' % (obj.id, settings.STATIC_URL)
            html += link

        if obj.completed and not obj.synced:
            link = '<a href="" onclick="syncit(%s);return false;" title="Sync Report"><img src="%s/igreport/img/sync.png"></a>&nbsp;&nbsp;' % (obj.id, settings.STATIC_URL)
            html += link
        
        msisdn = obj.connection.identity
        t = (msisdn, obj.id, msisdn, settings.STATIC_URL)
        html += '<a href="" title="Send SMS to %s" onclick="smsp(%s,\'%s\');return false;"><img src="%s/igreport/img/sms.png" border="0" /></a>' % t

        return html

    options.short_description = 'Options'
    options.allow_tags = True
    
    def get_row_css(self, obj, index):
        if obj.completed:
            return ' rpt-completed'
        if obj.synced:
            return ' rpt-synced'
        return ''

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        raise PermissionDenied
    
    def changelist_view(self, request, extra_context=None):
        title = 'Reports'

        buttons = [ {'label': 'Refresh', 'link': ''}, {'label': 'All Reports', 'link': '?'}, {'label': 'Completed', 'link': '?completed=1'}, {'label': 'Synced', 'link': '?synced=1'} ]
        context = {'title': title, 'include_file':'igreport/report.html', 'bottom_js':'rptsetc()', 'buttons': buttons}
        return super(IGReportAdmin, self).changelist_view(request, extra_context=context)

class UnprocessedAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message', 'send_date']
    #date_hierarchy = ['date']
    search_fields = ('connection__identity', 'text')
    list_filter = ['date']
    actions = None
    change_list_template = 'igreport/change_list.html'

    def __init__(self, *args, **kwargs):
        super(UnprocessedAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)
        
    def sender(self, obj):
        return obj.connection.identity
    
    sender.admin_order_field = 'connection'

    def message(self, obj):
        text = obj.text
        width = ''
        if len(text) > 50:
            width = '300px'
        else:
            html = text
        style = ''
        if width:
            style += 'width:%s;' % width
        if style:
            style = ' style="%s"' % style
        html = '<div id="rpt_%s"%s>%s</div>' % (obj.id, style, text)
        return html
    
    message.allow_tags='True'

    def send_date(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M')

    send_date.short_description = 'Send Date'
    send_date.admin_order_field = 'date'
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):

        buttons = [ {'label': 'Go To Reports', 'link': '../igreport/'}, {'label': 'Refresh', 'link': '?'} ]
        context = {'title': 'Unprocessed Messages', 'buttons': buttons}
        return super(UnprocessedAdmin, self).changelist_view(request, extra_context=context)
    
    def change_view(self, request, object_id, extra_context=None):
        raise PermissionDenied
    
    def queryset(self, request):
        qs = super(UnprocessedAdmin, self).queryset(request)
        return qs.filter(direction='I', application=None)

class UserProfileForm(ModelForm):
    district = ModelChoiceField(Location.objects.filter(type__name='district').order_by('name'))
    class Meta:
        model = UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    
admin.site.register(IGReport, IGReportAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Unprocessed, UnprocessedAdmin)