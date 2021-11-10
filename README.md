# Wagtail Wordpess Import

A package for Wagtail CMS to import WordPress blog content from an XML file into Wagtail.

- [Wagtail Wordpess Import](#wagtail-wordpess-import)
  - [Requirements](#requirements)
  - [Initial app and package setup](#initial-app-and-package-setup)
    - [First steps to configure your wagtail app](#first-steps-to-configure-your-wagtail-app)
  - [Running the import command](#running-the-import-command)
    - [Optional command arguments](#optional-command-arguments)
  - [Module documentation](#module-documentation)
  - [Developer Tooling](#developer-tooling)
  - [Delete imported pages command](#delete-imported-pages-command)
  - [Useful django shell commands](#useful-django-shell-commands)
    - [Delete all images](#delete-all-images)
    - [Delete all documents](#delete-all-documents)

## Requirements

1. Wagtail CMS Installed with initial setup
2. Wordpress XML export of all content in a single file
3. The Wordpress website will need to be live and available for importing of assets such as images and documents.

## Initial app and package setup

1. Setup a Wagtail site using your preferred method or follow the [official documentation](https://docs.wagtail.io/en/stable/getting_started/tutorial.html) to get started.
2. Download the repo for this package [Wagtail Wordpress Import](https://github.com/torchbox/wagtail-wordpress-import) to a location on your hard-drive. (This is the latest development branch)
3. Install this package with pip install -e "git+https://github.com/torchbox/wagtail-wordpress-import.git#egg=wagtail-wordpress-import"
 or using any method you prefer.
4. Place your XML files somewhere on your disk. The file can have any name you choose.
5. Create a `log` folder in the root of your site. The import script will need to write report files to this folder, you may need to set the permissions on the folder.
6. Add `"wagtail_wordpress_import"` to your INSTALLED_APPS config in your settings.py file.

### First steps to configure your wagtail app

The import can be run on an existing or new site but you will need to perform some setup on your page models.

We recommend your page model inherits from the provided WPImportedPageMixin

```python
from wagtail_wordpress_import.models import WPImportedPageMixin
class PostPage(WPImportedPageMixin, Page):
    ...
```

You will need to run `python manage.py makemigrations` and `python manage.py migrate` to add the fields to your page model.

*It's intended that these fields are temporary for while importing, and can be removed once the content has been imported. [view source](wagtail_wordpress_import/models.py)*

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
        # wagtail page model fields
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
python manage.py import_xml path/to/xml/file.xml parent_page_id
```

[parent_page_id] is the id of the page in your wagtail site where pages will be created as child pages. If you don't know what that is then choose to edit the page in wagtail admin and look at the url in your browser e.g. `http://www.domain.com/admin/pages/3/edit/` the number after /admin/pages/`3` is the id to use.

Running this command will import all Wordpress 'post' and 'page' types to the 'PostPage' model in and app called 'pages'

### Optional command arguments

- `-m` can be used to specify the Wagtail Page model to use for all imported pages. The default is `PostPage` when it's not specified.
- `-a` can be used to specify the Wagtail App where you have created your Wagtail Page model. The default is `pages` when it's not specified.
- `-t` can be used to limit the Wordpress page types to be imported. You can pass in a comma separated string of page types or just a single page type. The default is `page,post` if not specified.
- `-s` can be used to specify the status of pages you want to import. You can pass in a comma separated string of statuses or just a single status. The default is `publish,draft` if not specified.

## Module documentation

- [Block Builder](docs/blockbuilder.md)
- [Categories Import](docs/categories.md)
- [Prefilters](docs/prefilters.md)
- [Wordpress Shortcodes](docs/shortcodes.md)
- [Yoast Import](docs/yoast.md)

## Developer Tooling

The XML file you are importing can be a large file. Some of the items in the XML file can be removed before you run the import script. This will reduce the time it takes to complete the import process.

```bash
python manage.py reduce_xml path/to/your/xmlfile.xml
```

 will remove all items of `<wp:comment>`

---

To understand more about the type of HTML content formatting used in your Wordpress site we provide a reporting tool that will generate a table output in the console to show inline styles, html tags and shortcodes.

```bash
python manage.py analyze_html_content path/to/your/xmlfile.xml
```

---

## Delete imported pages command

When testing imports you may need to delete the imported pages and run the import again.

```bash
python manage.py delete_imported_pages [app] [page_model]
# app and page_model are required arguments
```

This script will run until all pages have been deleted and displays the  progress in the console.

## Useful django shell commands

To start the django shell run

```bash
python manage.py shell
```

The commands below are destructive, there's no going back!

### Delete all images

```python
from wagtail.images.models import Image
```

```python
Image.objects.all().delete()
```

### Delete all documents

```python
from wagtail.documents.models import Document
```

```python
Document.objects.all().delete()
```

