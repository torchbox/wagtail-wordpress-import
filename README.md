# Wagtail WordPress Import

A package for Wagtail CMS to import WordPress blog content from an XML file into Wagtail.

- [Wagtail WordPress Import](#wagtail-wordpress-import)
  - [Requirements](#requirements)
  - [Initial app and package setup](#initial-app-and-package-setup)
    - [First steps to configure your wagtail app](#first-steps-to-configure-your-wagtail-app)
  - [Running the import command](#running-the-import-command)
    - [Optional command arguments](#optional-command-arguments)
  - [Module documentation](#module-documentation)
  - [Developer Tooling](#developer-tooling)
    - [Useful Shell Commands](#useful-shell-commands)
      - [Delete all imported images](#delete-all-imported-images)
      - [Delete all imported documents](#delete-all-imported-documents)

## Requirements

1. Wagtail CMS Installed with initial setup
2. WordPress XML export of all content in a single file
3. The WordPress website will need to be live and available for importing of assets such as images and documents.

## Initial app and package setup

1. Setup a Wagtail site using your preferred method or follow the [official documentation](https://docs.wagtail.io/en/stable/getting_started/tutorial.html) to get started.
2. Download the repo for this package [Wagtail WordPress Import](https://github.com/torchbox/wagtail-wordpress-import/tree/integration/sprint-6) to a location on your hard-drive. (This is the latest development branch)
3. Install this package with pip install -e path/to/wagtail-wordpress-import or using any method you prefer.
4. Place your XML files somewhere on your disk. The file can have any name you choose.

### First steps to configure your Wagtail app

The import can be run on an existing or new site but you will need to perform some setup on your page models.

We recommend your page model inherits from the provided WPImportedPageMixin

```python
from wagtail_wordpress_import.models import WPImportedPageMixin
class PostPage(WPImportedPageMixin, Page):
    ...
```

You will need to run `python manage.py makemigrations` and `python manage.py migrate` to add the fields to your page model.

*It's intended that this initial setup can be removed once the content has been imported. [view source](wagtail-wordpress-import/wagtail_wordpress_import/models.py)*

A full example of the suggested page model class

```python
from wagtail.admin.edit_handlers import (
    FieldPanel,
    ObjectList,
    StreamFieldPanel,
    TabbedInterface,
)
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail_wordpress_import.blocks import WPImportStreamBlocks
from wagtail_wordpress_import.models import WPImportedPageMixin


class PostPage(WPImportedPageMixin, Page):
    body = StreamField(WPImportStreamBlocks)
    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(Page.promote_panels, heading="Promote"),
            ObjectList(Page.settings_panels, heading="Settings", classname="settings"),
            ObjectList(WPImportedPageMixin.wordpress_panels, heading="Debug"),
        ]
    )

    def import_wordpress_data(self, data):
        # Wagtail page model fields
        self.title = data["title"]
        self.slug = data["slug"]
        self.first_published_at = data["first_published_at"]
        self.last_published_at = data["last_published_at"]
        self.latest_revision_created_at = data["latest_revision_created_at"]
        self.search_description = data["search_description"]

        # debug fields
        self.wp_post_id = data["wp_post_id"]
        self.wp_post_type = data["wp_post_type"]
        self.wp_link = data["wp_link"]
        self.wp_raw_content = data["wp_raw_content"]
        self.wp_block_json = data["wp_block_json"]
        self.wp_processed_content = data["wp_processed_content"]
        self.wp_normalized_styles = data["wp_normalized_styles"]

        # own model fields
        self.body = data["body"]
```

## Running the import command

The most basic command would be:

```bash
`python manage.py import_xml path/to/xml/file.xml parent_page_id`
```

`parent_page_id` is the ID of the page in your Wagtail site where WordPress pages will be imported as children. You can find this in the Wagtail admin URL when editing the page e.g. for `http://www.domain.com/admin/pages/3/edit/` the ID is 3.

Running this command will import all WordPress 'post' and 'page' types to the 'PostPage' model in an app called 'pages'

### Optional command arguments

- `-m` can be used to specify the Wagtail Page model to use for all imported pages. The default is `PostPage` when it's not specified.
- `-a` can be used to specify the Wagtail App where you have created your Wagtail Page model. The default is `pages` when it's not specified.
- `-t` can be used to limit the WordPress page types to be imported. You can pass in a comma-separated string of page types or just a single page type. The default is `page,post` if not specified.
- `-s` can be used to specify the status of pages you want to import. You can pass in a comma-separated string of statuses or just a single status. The default is `publish,draft` if not specified.

[View the import command source](wagtail_wordpress_import/management/commands/import_xml.py) to if you need to extend the command.

## Module documentation

- [Block Builder](wagtail-wordpress-import/docs/blockbuilder.md)
- [Categories Import](wagtail-wordpress-import/docs/categories.md)
- [Prefilters](wagtail-wordpress-import/docs/prefilters.md)
- [WordPress Shortcodes](wagtail-wordpress-import/docs/shortcodes.md)
- [Yoast Import](wagtail-wordpress-import/docs/yoast.md)

## Developer Tooling

The XML file you are importing can be a large file. Some of the items in the XML file can be removed before you run the import script. This will reduce the time it takes to complete the import process.

```bash
python manage.py reduce_xml path/to/your/xmlfile.xml
```

 will remove all items of `<wp:comment>`

---

To understand more about the type of HTML content formatting used in your WordPress site we provide a reporting tool that will generate a table output in the console to show inline styles, HTML tags and shortcodes.

```bash
python manage.py analyze_html_content path/to/your/xmlfile.xml
```

---

When testing imports you may need to remove all the imported pages and run it again. This script will run until all pages have been deleted and display progress in the console.

```bash
python manage.py delete_imported_pages [app] [page_model]
# app and page_model are required arguments
```

### Useful Shell Commands

Start a shell with `python manage.py shell`

#### Delete all imported images

```shell
from wagtail.images.models import Image
+
Image.objects.all().delete()
```

#### Delete all imported documents

```shell
from wagtail.documents.models import Document
+
Document.objects.all().delete()
```
