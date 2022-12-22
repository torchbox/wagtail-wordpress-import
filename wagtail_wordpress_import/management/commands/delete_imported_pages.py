from django.apps import apps
from django.core.management.base import BaseCommand
from wagtail import VERSION as WAGTAIL_VERSION

if WAGTAIL_VERSION >= (3, 0):
    from wagtail.models import Page
else:
    from wagtail.core.models import Page


class Command(BaseCommand):
    help = """Utilitly command to delete pages by type with optional limit to a parent page."""

    """
    When using sqlite3 the command line bulk delete won't work:
        on a site with a lot of pages so we'll fall back to looping

    ./manage.py delete_imported_xml app model [--parent_id]
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "app",
            type=str,
            help="The app which contains your page models for the delete action",
            default="pages",
        )
        parser.add_argument(
            "model",
            type=str,
            help="A page model to use for the deleting pages",
            default="PostPage",
        )
        parser.add_argument(
            "-p",
            "--parent_id",
            type=int,
            help="The page ID of the parent page to use when deleting imported pages",
        )

    def handle(self, *args, **options):

        parent = None
        pages_to_delete = None

        try:
            page_model = apps.get_model(options["app"], options["model"])
        except LookupError:
            self.stdout.write(
                self.style.ERROR(
                    f"Cannot find the app and or model '{options['app']}.{options['model']}'"
                )
            )
            exit()

        if options["parent_id"]:
            # limit to delete pages of a page type to children of a parent page
            try:
                parent = Page.objects.get(id=options["parent_id"])
            except Page.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Cannot find the parent page with id = {options['parent_id']}"
                    )
                )
                exit()

        if not parent:
            pages_to_delete = page_model.objects.defer_streamfields().specific()
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Limiting delete action to children of page: [{parent.id}] '{parent.title}'"
                )
            )
            pages_to_delete = parent.get_children().exact_type(page_model)

        self.stdout.write("⏳ working ...")
        self.stdout.write(self.style.NOTICE(f"{len(pages_to_delete)} pages to delete"))

        for page in pages_to_delete:
            has_children = ""
            if page.get_children():
                has_children = " inc. child pages"
            self.stderr.write(
                self.style.SUCCESS(f"deleting [{page.id}] '{page.title}'{has_children}")
            )
            page.delete()
