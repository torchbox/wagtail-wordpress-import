# Import Hooks

- [Import Hooks](#import-hooks)
  - [What are import hooks useful for?](#what-are-import-hooks-useful-for)
  - [Adding an import hook](#adding-an-import-hook)
    - [Import hook configuration](#import-hook-configuration)

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

The related image in the `<wp:postmeta>` tag above with the `<wp:meta_key>` key of `_thumbnail_id` defines the relationship between the blog post and the image. The image details we need to construct the blog post in Wagtail are stored in a separate XML tag.

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

The type of an XML `<item>` element is given by its `<wp:post_type>` tag. The example item above represents an "attachment" type. This is not included by default when an import is run, because we only import items of the "post" or "page" type, representing a blog post or page to be created in Wagtail.

Import hooks allow you to define a function that will be called when a specific XML tag is encountered. This allows you to define your own custom import logic for your specific import requirements.

## Adding an import hook

The package doesn't include any import hooks by default. You can add your own import hooks by adding a dictionary as the  `WAGTAIL_WORDPRESS_IMPORT_HOOKS` setting and defining an XML post type to identify it, and a function to process the data. The function takes a page instance, and a cache of the tag data to be processed, as arguments.

Following on with the example XML above, we can add an import hook to capture the `<item>` tags that are of type `attachment` and use that attachment data to create a header image for the blog post.

### Import hook configuration

Add a settings variable to your site settings file called `WAGTAIL_WORDPRESS_IMPORT_HOOKS` and add a dict with a key of `attachment` and values as follows:

```python
WORDPRESS_IMPORT_HOOKS_ITEMS_TO_CACHE = {
    "attachment": {
        "DATA_TAG": "_thumbnail_id",
        "FUNCTION": "pages.import_hooks.header_image_importer",
    }
}
```

The `DATA_TAG` key is the `<wp:meta_key>_thumbnail_id</wp:meta_key>` value to be parsed. During the import process the key will be used to extract the value in the `<wp:meta_value>43120</wp:meta_value>` tag.

The resulting dict item in the items_cache would be:



```python
{
    ...
    # each dict item is a nested list of dicts that represents the XML item tags tree 
    # of keys and values. It's not all shown here for brevity as 
    # it can be a large amount of data.
    ...
    'wp:postmeta': [
        ... # other wp:postmeta keys and values
        {
            'wp:meta_key': '_thumbnail_id', 
            'wp:meta_value': 43120
        }
    ]
}
```

The `FUNCTION` key is the dotted path to the function that will be called. The function should accept the Page model and the data to be imported as arguments. The function also needs to be passed an argument of `items_cache` which is the cache of all the items that have been imported with the tag `<wp:post_type>attachment</wp:post_type>`

Sample function and page model for processing the header image:

```python
# pages/import_hooks.py

"""The function called to process the header image"""

def header_image_importer(page, data, items_cache):
    # page.wp_post_meta[data] will exist if the Page model 
    # inherits from WPImportedPageMixin
    thumbnail_id = page.wp_post_meta[data]

    # items_cache is a dict created automatically by the importer 
    # when the import hook setting is included in your own settings
    attachments = items_cache.get("attachment")

    # the code below would be your own code to process the header image,
    # you can perform any type of Python/Wagtail logic here and make use 
    # of thumbnail_id and attachments variables.
    image_url = None

    for attachment in attachments:
        if (
            attachment.get("wp:post_id")
            and attachment.get("wp:post_id") == thumbnail_id
        ):
            image_url = attachment.get("guid")

    if image_url:
        image = get_or_save_image(image_url)
        page.header_image = image
        page.save()
```

Sample page model with header_image field:

```python
"""A sample page model thats has a header image field"""

class PostPage(WPImportedPageMixin, Page):
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
