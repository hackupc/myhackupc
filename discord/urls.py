from django.conf.urls import url, include
from rest_framework.routers import SimpleRouter

from discord import views
from discord.views import UserViewSet

router = SimpleRouter()
router.register(r'', UserViewSet)


urlpatterns = [
    url(r'^connect/$', views.ConnectDiscord.as_view(), name='discord_login'),
    url(r'^oauth2/$', views.RedirectDiscord.as_view(), name='discord_redirect'),
    url(r'^api/', include(router.urls)),
    url(r'^list/$', views.DiscordTableView.as_view(), name='discord_list'),
    url(r'^error/$', views.RedirectError.as_view(), name='alreadyConnected'),
    url(r'^swag/$', views.SwagView.as_view(), name='swag_form'),
    url(r'^sticker/$', views.DiscordStickerList.as_view(), name='sticker_list'),
    url(r'^list/csv/$', views.get_csv_address, name='csv_address'),
]
