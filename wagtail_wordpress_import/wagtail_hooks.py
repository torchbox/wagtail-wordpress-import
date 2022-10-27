from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

try:
    from wagtail import hooks
except ImportError:
    from wagtail.core import hooks


@hooks.register("register_admin_urls")
def register_admin_urls():
    urls = [
        path(
            "jsi18n/",
            JavaScriptCatalog.as_view(packages=["wagtail_wordpress_import"]),
            name="javascript_catalog",
        ),
        # Add your other URLs here, and they will appear under `/admin/xmlimport/`
        # Note: you do not need to check for authentication in views added here, Wagtail does this for you!
    ]

    return [
        path(
            "xmlimport/",
            include(
                (urls, "wagtail_wordpress_import"),
                namespace="wagtail_wordpress_import",
            ),
        )
    ]
