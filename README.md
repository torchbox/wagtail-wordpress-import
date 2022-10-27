# Wagtail WordPress Import

[![codecov](https://codecov.io/gh/torchbox/wagtail-wordpress-import/branch/main/graph/badge.svg?token=KFSTTxTGxZ)](https://codecov.io/gh/torchbox/wagtail-wordpress-import)

A package for Wagtail CMS to import WordPress blog content from an XML file into Wagtail.

- [Wagtail WordPress Import](#wagtail-wordpress-import)
  - [Requirements](#requirements)
  - [Compatibility](#compatibility)
  - [Initial app and package setup](#initial-app-and-package-setup)
    - [Site URL for importing images and documents](#site-url-for-importing-images-and-documents)
    - [First steps to configure your Wagtail app](#first-steps-to-configure-your-wagtail-app)
      - [A full example of the suggested page model class](#a-full-example-of-the-suggested-page-model-class)
  - [Running the import command](#running-the-import-command)
    - [Optional command arguments](#optional-command-arguments)
  - [Import process flow](#import-process-flow)
  - [Module documentation](#module-documentation)
  - [Developer Tooling](#developer-tooling)
  - [Further Usage Examples](#further-usage-examples)

## Requirements

1. Wagtail CMS Installed with initial setup
2. WordPress XML export of all content in a single file
3. The WordPress website will need to be live and available for importing of assets such as images and documents.

## Compatibility

The package has been developed and tested with:

- Wagtail: ^2.15
- Django: ^3.1
- Postgres and SQLite Databases

`All code examples are for a site using Wagtail v3.0+` See [Wagtail release notes](https://docs.wagtail.org/en/stable/releases/3.0.html) for compatibility for Wagtail versions <3.0

## Initial app and package setup

1. Setup a Wagtail site using your preferred method or follow the [official documentation](https://docs.wagtail.io/en/stable/getting_started/tutorial.html) to get started.
2. Install this package from PyPi with `pip install wagtail-wordpress-import`
 or using any method you prefer.
3. Place your XML files somewhere on your disk. The file can have any name you choose.
4. Create a `log` folder in the root of your site. The import script will need to write report files to this folder, you may need to set the permissions on the folder.
5. Add `"wagtail_wordpress_import"` to your INSTALLED_APPS config in your settings.py file.

### Site URL for importing images and documents

Add a setting of `WAGTAIL_WORDPRESS_IMPORTER_SOURCE_DOMAIN` in your sites settings and set it to the the URL of the website that the images and documents will be imported from.

The importer uses the [requests](https://docs.python-requests.org/en/latest/) library to download images and documents during the import process using the configuration in  `WAGTAIL_WORDPRESS_IMPORTER_REQUESTS_SETTINGS`. 

If the default settings are not suitable for your import, you can add the settings below to your own site settings and override the values.

```python
# import package default settings

WAGTAIL_WORDPRESS_IMPORTER_REQUESTS_SETTINGS = {
    "headers": { "User-Agent": "WagtailWordpressImporter" },
    "timeout": 5,
    "stream": True,
    "allow_redirects": allow_redirects,
}
```

### First steps to configure your Wagtail app

The import can be run on an existing or new site but you will need to perform some setup on your page models.

We recommend your page model inherits from the provided WPImportedPageMixin

```python
from wagtail_wordpress_import.models import WPImportedPageMixin

class PostPage(WPImportedPageMixin, Page):
    ...
```

You will need to run `python manage.py makemigrations` and `python manage.py migrate` to add the fields to your page model.

*It's intended that these fields are temporary for while importing, and can be removed once the content has been imported. [view source](wagtail_wordpress_import/models.py)*

#### A full example of the suggested page model class

The import default is to import the `post` and `page` content types to an app called `app` and a model called `PostPage`. Keep that mind when you create your own page model.

```python
# mysite/app/models.py
# The imports below assume you are using Wagtail v3.0+

# Wagtail < 3.0
# from wagtail.admin.edit_handlers (...)
from wagtail.admin.panels import (
    FieldPanel,
    ObjectList,
    TabbedInterface,
)

# Wagtail < 3.0
# from wagtail.core.fields import StreamField
from wagtail.fields import StreamField

# Wagtail < 3.0
# from wagtail.core.models import Page
from wagtail.models import Page

from wagtail_wordpress_import.blocks import WPImportStreamBlocks
from wagtail_wordpress_import.models import WPImportedPageMixin


class PostPage(WPImportedPageMixin, Page):
    body = StreamField(WPImportStreamBlocks)
    content_panels = Page.content_panels + [
        # Wagtail < 3.0
        # StreamFieldPanel("body")
        FieldPanel("body"),
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
        self.wp_post_meta = data["wp_post_meta"]

        # own model fields
        self.body = data["body"]
```

## Running the import command

The most basic command would be:

```bash
python manage.py import_xml path/to/xml/file.xml parent_page_id
```

`parent_page_id` is the ID of the page in your Wagtail site where WordPress pages will be imported as children. You can find this in the Wagtail admin URL when editing the page e.g. for `http://www.domain.com/admin/pages/3/edit/` the ID is 3.

Running this command will import all WordPress 'post' and 'page' types to the 'PostPage' model in an app called 'pages'

You can run the import as many times as you need. To avoid content duplication, subsequent imports after the first import will update the existing pages. This behavior also applies to any images or documents that have been imported.

### Optional command arguments

- `-m` can be used to specify the Wagtail Page model to use for all imported pages. The default is `PostPage` when it's not specified.
- `-a` can be used to specify the Wagtail App where you have created your Wagtail Page model. The default is `pages` when it's not specified.
- `-t` can be used to limit the WordPress page types to be imported. You can pass in a comma-separated string of page types or just a single page type. The default is `page,post` if not specified.
- `-s` can be used to specify the status of pages you want to import. You can pass in a comma-separated string of statuses or just a single status. The default is `publish,draft` if not specified.

## Import process flow

While the import process is simple to run with the options above there's a lot that happens during the import.

By changing the import configuration, you can customise the import process without modifying `wagtail-wordpress-import` package files. To understand what is possible, and how you can change the behaviour at different stages, you can read an [overview of the import process](docs/import_process.md).

## Module documentation

- [Block Builder](docs/blockbuilder.md)
- [Categories Import](docs/categories.md)
- [Import Hooks](docs/import_hooks.md)
- [Prefilters](docs/prefilters.md)
- [WordPress Block Shortcodes](docs/block_shortcodes.md)
- [WordPress Inline Shortcodes](docs/inline_shortocdes.md)
- [Yoast Import](docs/yoast.md)

## Developer Tooling

We have included some developer commands to help you with importing large datasets and analyzing the data.

[View Developer Tooling](docs/tooling.md)

## Further Usage Examples

- [Handling Specific HTML content structures](docs/examples.md)

## Contributing

If you're a Python or Django developer, fork the repo and get stuck in!

You might like to start by reviewing the [contributing guidelines](https://github.com/torchbox/wagtail-wordpress-import/wiki/Contributing-to-the-package) in the wiki and checking [current issues](https://github.com/torchbox/wagtail-wordpress-import/issues).

## Releases

[Realease process](https://github.com/torchbox/wagtail-wordpress-import/wiki/Create-a-new-release)
