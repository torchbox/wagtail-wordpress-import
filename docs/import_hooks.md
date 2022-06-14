# Import Hooks

- [Import Hooks](#import-hooks)
  - [The Importer Debug Feature Default Action](#the-importer-debug-feature-default-action)
  - [What are import hooks useful for?](#what-are-import-hooks-useful-for)
  - [Adding an import hook](#adding-an-import-hook)
  - [Example: Import Hook For A Header Image (Items Cache)](#example-import-hook-for-a-header-image-items-cache)
    - [Settings Configuration](#settings-configuration)
    - [The Function For Processing A Header Image](#the-function-for-processing-a-header-image)
    - [Sample page model with header_image field](#sample-page-model-with-header_image-field)
  - [Example: Import Hook For An Author (Tags Cache)](#example-import-hook-for-an-author-tags-cache)
    - [XML Tag Hook Configuration](#xml-tag-hook-configuration)
    - [Sample function for processing the author](#sample-function-for-processing-the-author)
    - [Sample page model with author field](#sample-page-model-with-author-field)

## The Importer Debug Feature Default Action

**Import hooks rely on the Importer Debug Feature which is enabled by default.**

The import process will save the XML item tags as a JSON string in the `wp_post_meta` field on a page model. In the examples that follow the JSON field data is used in the function examples to get values of XML tags in the XML item. This is how the related data foreign keys can be used to create the relationships between the page model and other wagtail models.

## What are import hooks useful for?

A full XML export of a complete WordPress website will contain all the entities within the database, but as it's a text file the relationships between the entities are not ideally represented for the import process.

**For example**, a blog post might include a header image that's not part of the body content in the Wordpress XML `<item>` tag for the post. The image would be elsewhere in the XML, referenced by an ID in the post item's `<wp:postmeta>` tag.

Sample XML item for a blog post:

```xml
<item>
    <title>A title</title>
    <link>https://www.example.com/a-title</link>
    <description>search description</description>
    <content:encoded>HTML content...</content:encoded>
    <excerpt:encoded>introduction...</excerpt:encoded>
    <wp:post_id>44221</wp:post_id>
    <wp:post_date>2015-05-21 15:00:31</wp:post_date>
    <wp:post_date_gmt>2015-05-21 19:00:31</wp:post_date_gmt>
    <wp:post_modified>2015-05-21 15:00:44</wp:post_modified>
    <wp:post_modified_gmt>2015-05-21 19:00:44</wp:post_modified_gmt>
    <wp:comment_status>open</wp:comment_status>
    <wp:ping_status>closed</wp:ping_status>
    <wp:post_name>a-title</wp:post_name>
    <wp:status>publish</wp:status>
    <wp:post_type>post</wp:post_type>
    ...
    <wp:postmeta>
        <wp:meta_key>_thumbnail_id</wp:meta_key>
        <wp:meta_value>43120</wp:meta_value>
    </wp:postmeta>
    ...
</item>
```

The related image in the `<wp:postmeta>` tag above with the `<wp:meta_key>` key of `_thumbnail_id` defines the relationship between the blog post and the image id `<wp:meta_value>` of 43120 which is a post id. The image data we need to construct the blog post in Wagtail is stored in a separate XML tag see below.

Sample XML tags for an image:

```xml
<item>
  <title>hustlers dont sleep</title>
  <link>https://www.budgetsaresexy.com/ways-to-make-money/hustlers-dont-sleep/</link>
  <pubDate>Fri, 27 Feb 2015 17:40:05 +0000</pubDate>
  <dc:creator>jMoney</dc:creator>
  <guid isPermaLink="false">https://www.budgetsaresexy.com/images/hustlers-dont-sleep1.jpg</guid>
  <description />
  <content:encoded />
  <excerpt:encoded />
  <wp:post_id>43120</wp:post_id>
  ...  
  <wp:post_type>attachment</wp:post_type>
  ...
</item>
```

The type of an XML `<item>` element is given by its `<wp:post_type>` tag. The example item above represents an "attachment" type. This is not included in the import by default, because we only import items of the "post" or "page" type, representing a blog post or page to be created in Wagtail.

Import hooks allow you to define a function that will be called with some parameters where you can define your own custom import logic for your specific import requirements.

## Adding an import hook

The package doesn't include any import hooks by default.

You can add your own import hooks by modifying:

- `settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE` for tags within the `<wp:postmeta>` tag, or
- `settings.WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE` for tags which are directly attributes of the imported post or page

## Example: Import Hook For A Header Image (Items Cache)

This example will add a header image to the imported page based on the presence of an image ID in the XML file.

You will need to include the following in your app.

- Settings Configuration
- A field thats's available in your page model for the image.
- A function that will be called to link the image to the page.

This type of hook will cache an `<item>` tag from the XML, that has a match for the key of the hook configuration.

### Settings Configuration

Add the following configuration to your site settings file

<!-- called `WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE`, add a dict with a key of `attachment` and values as follows: -->

```python
WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE = {
    "attachment": { 
        "DATA_TAG": "thumbnail_id", 
        "FUNCTION": "pages.import_hooks.header_image_processor", 
    }
}
```

The key of `attachment` is the value to look for in `<wp:post_type>` in an `<item>` tag in the XML file.

The `DATA_TAG` value is the key to use to look up the value for the image ID in your own function that processes the header image. This value is passed to your function.

**Important:** If the DATA_TAG value in your XML has a leading `_` character do not include the underscore in the value above. If the value contains a `:` then replace it with a `_` in the value above. This is because in the function that processes the header image, the value is used to construct a lookup by key query parameter on a JSONField available on the page model.

The `FUNCTION` value is a dotted path to the function to call in your own Wagtail site.

### The Function For Processing A Header Image

*During the import process the configuration passed in above will be used to cache any XML `<item>` tag that has a `<wp:post_type>` with a value of `attachment`. The cache is a list of dictionary items that represent XML items. You can use the dictionary as a data source for your own function.*

```python
# pages/import_hooks.py

# get_or_save_image is a convenience function provided in the package
from wagtail_wordpress_import.block_builder_defaults import get_or_save_image


def header_image_processor(imported_pages, data_tag, items_cache):
    """
    imported_pages: 
        Is a specific() page model queryset of all imported pages.
    data_tag:
        Is the value of the `DATA_TAG` key from the configuration above.
    items_cache:
        Is a list of dictionaries, one for each item in the XML file.
    """

    # See note above about leading _ and : characters in the XML value
    lookup = f"wp_post_meta__{data_tag}"

    for attachment in items_cache:
        # The id of the cached item used in the filter
        thumbnail_id = attachment.get("wp:post_id")

        # Filter the imported_pages for only pages that include the 
        # matching thumbnail_id in the wp_post_meta field
        pages = imported_pages.filter(**{lookup: thumbnail_id})

        if pages.exists():

            # guid is the url of the image to fetch, the get_or_save_image() 
            # function will fetch the image if it doesn't exist
            image = get_or_save_image(attachment.get("guid"))

            # update header_image field in all of the pages in 
            # the queryset with the image object
            pages.update(header_image=image)

            # the print statement below is optional 
            # and will show the progress in the console
            print("Attaching header images to pages:", pages)
```

### Sample page model with header_image field

```python
"""A sample page model thats has a header image field"""

class PostPage(WPImportedPageMixin, Page):
    # WPImportedPageMixin is optional, but recommended 
    # when running the import process
    ...
    header_image = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    ...
    content_panels = Page.content_panels + [
        ...
        ImageChooserPanel("header_image"),
        ...
    ]
```

---

## Example: Import Hook For An Author (Tags Cache)

This example will add a author relation to the imported page based on the presence of an `<dc:creator>` value in the XML file.

You will need to include the following in your app.

- Settings Configuration
- A field thats's available in your page model for the related author.
- A function that will be called to link the page to a author record.

This type of hook will cache an XML tag from the XML, that has a match for the key of the hook configuration.

**Sample XML item for a blog post:**

```xml
<item>
    <title>A title</title>
    <link>https://www.example.com/a-title</link>
    <description>search description</description>
    <dc:creator>joe-blogs</dc:creator>
    <content:encoded>HTML content...</content:encoded>
    <excerpt:encoded>introduction...</excerpt:encoded>
    <wp:post_id>44221</wp:post_id>
    <wp:post_date>2015-05-21 15:00:31</wp:post_date>
    <wp:post_date_gmt>2015-05-21 19:00:31</wp:post_date_gmt>
    <wp:post_modified>2015-05-21 15:00:44</wp:post_modified>
    <wp:post_modified_gmt>2015-05-21 19:00:44</wp:post_modified_gmt>
    <wp:comment_status>open</wp:comment_status>
    <wp:ping_status>closed</wp:ping_status>
    <wp:post_name>a-title</wp:post_name>
    <wp:status>publish</wp:status>
    <wp:post_type>post</wp:post_type>
</item>
```

The related author in the `<dc:creator>` tag above defines the relationship between the blog post and the `<wp:author>` tag below.

**Sample XML tags for an author:**

```xml
<wp:author>
  <wp:author_id>3</wp:author_id>
  <wp:author_login>joe-blogs</wp:author_login>
  <wp:author_email>inbox@example.com</wp:author_email>
  <wp:author_display_name>Joe Blogs</wp:author_display_name>
  <wp:author_first_name>Joe</wp:author_first_name>
  <wp:author_last_name>Blogs</wp:author_last_name>
</wp:author>
```

The `<wp:author>` XML tag above is not included in the import by default because only `<item>` tags that represent a blog post or page to be created in Wagtail are imported.

### XML Tag Hook Configuration

Add a settings variable to your site settings file called `WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE` and add a dict with a key of `wp:author` and values as follows:

```python
WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE = {
    # the key is the XML tag name of the item tag that contains the related content
    "wp:author": {
        # the XML tag which has the value to lookup in the tags cache
        "DATA_TAG": "dc_creator",
        # the dotted path to the function to call in your own Wagtail site
        "FUNCTION": "pages.import_hooks.author_processor",
    }
}
```

The key of `wp:author` is the tag name in the XML file.

The `DATA_TAG` value is the key to use to look up the value for the author in your own function that processes the author relation. This value is passed to your function.

**Important:** If the DATA_TAG value in your XML has a leading `_` character do not include the underscore in the value above. If the value contains a `:` then replace it with a `_` in the value above. This is because in the function that processes the header image, the value is used to construct a lookup by key query parameter on a JSONField available on the page model.

The `FUNCTION` value is a dotted path to the function to call in your own Wagtail site.

### Sample function for processing the author

```python
# pages/import_hooks.py

from pages.models import Author  # a snippet model for authors


def author_processor(imported_pages, data_tag, tags_cache):
    """
    imported_pages: 
        Is a specific() page model queryset of all imported pages.
    data_tag:
        Is the value of the `DATA_TAG` key from the configuration above.
    tags_cache:
        Is a list of dictionaries, one for each tag in the XML file.
    """

    # See note above about leading _ and : characters in the XML value
    lookup = f"wp_post_meta__{data_tag}"

    for author in tags_cache:
        # the reference tag to use to for the data value
        author_login = author.get("wp:author_login")

        # Filter the imported_pages for only pages that include the 
        # matching dc_creator in the wp_post_meta field
        pages = imported_pages.filter(**{lookup: author_login})

        if pages:
            # you may need to do some additional validation here
            # depending on your related model
            first_name = (
                author.get("wp:author_first_name")
                if author.get("wp:author_first_name")
                else "not"
            )
            last_name = (
                author.get("wp:author_last_name")
                if author.get("wp:author_last_name")
                else "known"
            )
            email_address = author.get("wp:author_email")

            # author is snippet model but you can use any 
            # model type that you have created in your own Wagtail site
            author, created = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                email_address=email_address,
            )

            if pages.exists():
                # update author field in all of the pages in 
                # the queryset with the author object
                pages.update(author=author)

                # the print statement below is optional 
                # and will show the progress in the console
                print("Attaching authors to pages:", pages)
```

### Sample page model with author field

```python
"""A sample page model thats has a header image field"""
# The imports below assume you are using Wagtail v3.0+

# Wagtail < 3.0
# from wagtail.core.models import Page
from wagtail.models import Page

# Wagtail < 3.0
# from wagtail.admin.edit
from wagtail.admin.panels import FieldPanel

class PostPage(WPImportedPageMixin, Page):
    # WPImportedPageMixin is optional, but recommended 
    # when running the import process
    ...
    author = models.ForeignKey(
        "pages.Author",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    ...
    content_panels = Page.content_panels + [
        ...
        # Wagtail < 3.0
        # SnippetChooserPanel("author"),
        FieldPanel("author"s)
        ...
    ]
```
