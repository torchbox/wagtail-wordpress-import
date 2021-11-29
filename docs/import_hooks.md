# Import Hooks

- [Import Hooks](#import-hooks)
  - [What are import hooks useful for?](#what-are-import-hooks-useful-for)
  - [Adding an import hook](#adding-an-import-hook)
  - [Example XML Item Hook Configuration](#example-xml-item-hook-configuration)
    - [Sample function for processing the header image](#sample-function-for-processing-the-header-image)
    - [Sample page model with header_image field](#sample-page-model-with-header_image-field)
  - [Example XML Tag Hook Configuration](#example-xml-tag-hook-configuration)
    - [XML Tag Hook Configuration](#xml-tag-hook-configuration)
    - [Sample function for processing the author](#sample-function-for-processing-the-author)
    - [Sample page model with author field](#sample-page-model-with-author-field)

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

- `settings.WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE` for tags within the `<wp:post_meta>` tag, or
- `settings.WORDPRESS_IMPORT_HOOKS_TAGS_TO_CACHE` for tags which are directly attributes of the imported post or page

## Example XML Item Hook Configuration

This hook is run for extra XML items that will be imported.

Add a settings variable to your site settings file called `WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE`, add a dict with a key of `attachment` and values as follows:

```python
WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE = {
    # the key is the wp:post_type XML tag value in the XML item that contains the related content
    "attachment": { 
        # the XML wp:postmeta tag wp:meta_key value
        "DATA_TAG": "thumbnail_id", 
        # the dotted path to the function to call in your own Wagtail site
        "FUNCTION": "pages.import_hooks.header_image_processor", 
    }
}
```

The key of the dict is the value in  `<wp:post_type>...</wp:post_type>` in the XML item that contains the related content.

`DATA_TAG` is the value in `<wp:meta_key>value</wp:meta_key>` of the `<wp:postmeta>` tag in the XML item that contains the related content. *This is passed to your function.*

`FUNCTION` the dotted path to the function to call in your own Wagtail site.

Note: If the DATA_TAG has a leading `_` character do not include the underscore in the settings value. If the value contains a `:` anywhere in it replace it with a `_` in the settings value.

### Sample function for processing the header image

```python
# pages/import_hooks.py

# get_or_save_image is a convenience function provided in the package
from wagtail_wordpress_import.block_builder_defaults import get_or_save_image


def header_image_processor(imported_pages, data, items_cache):

    # see note above about leading _ and : characters 
    # in the settings value
    lookup = f"wp_post_meta__{data}"

    for attachment in items_cache:
        # the id of the cached item used in the filter
        thumbnail_id = attachment.get("wp:post_id")
        # a result set of pages that include the 
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

## Example XML Tag Hook Configuration

This hook is run for extra XML tags that will be imported.

A blog post `<item>` could include author information that has a reference to another XML tag. Here it would be referenced in the post `<item>` tag in `<dc:creator>`.

Sample XML item for a blog post:

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

The related author in the `<dc:creator>` tag above defines the relationship between the blog post and the `<wp:author>` tag. The author data we need to construct the blog post and Author record in Wagtail is stored in a separate XML tag see below.

Sample XML tags for an author:

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
        "DATA_TAG": "dc:creator",
        # the dotted path to the function to call in your own Wagtail site
        "FUNCTION": "pages.import_hooks.author_processor",
    }
}
```

The key of the dict is the name for the tag/s to cache in the XML file which contains the related content.

`DATA_TAG` is the tag `<dc:creator></dc:creator>` value. *This is passed to your function.*

`FUNCTION` is the dotted path to the function that will be called.

### Sample function for processing the author

```python
# pages/import_hooks.py

from pages.models import Author  # a snippet model for authors


def author_processor(imported_pages, data, tags_cache):

    lookup = f"wp_post_meta__{data}"

    for author in tags_cache:
        # the reference tag to use to for the data value
        author_login = author.get("wp:author_login")
        # a result set of pages that include the 
        # matching author_login value
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
        SnippetChooserPanel("author"),
        ...
    ]
```
