from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images.views.serve import ServeView
from wagtail.contrib.sitemaps.views import sitemap
from django.conf.urls.i18n import i18n_patterns

from search import views as search_views
from .api import api_router

from images import views
from django.views.i18n import JavaScriptCatalog



urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("documents/", include(wagtaildocs_urls)),
    re_path(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', ServeView.as_view(), name='wagtailimages_serve'),
    path("api/v2/", api_router.urls),
    path("sitemap.xml", sitemap),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path("search/", search_views.search, name="search"),
    path("admin/", include(wagtailadmin_urls)),
    re_path(r'^comments/', include('django_comments_xtd.urls')),
    path(r'jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path("plot/", views.plot, name="plot"),
    path("", include(wagtail_urls)),
)

