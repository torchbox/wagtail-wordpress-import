from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """Utils to delete pages by type."""

    # when using sqlite3 the command line bulk delete won't work
    # so we'll fall back to looping, a bit slower but acceptable

    def add_arguments(self, parser):
        parser.add_argument("pagetype", type=str)

    def handle(self, *args, **options):
        # using this delete may require some adjustment to remove pages
        # deepest in the tree first
        if options["pagetype"] == "postpage" or options["pagetype"] == "all":
            post_page = apps.get_model("pages", "PostPage")
            pages = post_page.objects.all()
            self.delete_pages(pages)

        if options["pagetype"] == "newspage" or options["pagetype"] == "all":
            news_page = apps.get_model("pages", "NewsPage")
            pages = news_page.objects.all()
            self.delete_pages(pages)

        if options["pagetype"] == "pagepage" or options["pagetype"] == "all":
            page_page = apps.get_model("pages", "PagePage")
            pages = page_page.objects.all()
            self.delete_pages(pages)

    def delete_pages(self, model):
        for page in model:
            page.delete()
