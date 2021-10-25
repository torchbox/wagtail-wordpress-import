# Categories

- [Categories](#categories)
  - [Configuration](#configuration)
  - [Example Category model](#example-category-model)
  - [Example Page model](#example-page-model)

The package can handle the import of categories. Categories are imported as a ManyToMany relationship on a Page model.

## Configuration

It is disabled by default but you can enable the plugin by adding the following to your settings file.

```python
WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED = True
```

The plugin will also need to know which model in you app is used for the categories so add the following to your settings file.

```python
WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL = "pages.models.Category
```

The example here uses a Category model inside the pages app but you can use any name for the model.

## Example Category model

```python
@register_snippet
class Category(models.Model):
    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
```

`@register_snippet` is used here but you could use the Wagtail Model Admin if you prefer.

## Example Page model

To link the categories to your Page model you need to use the `ParentalManyToManyField` in your Page model. The [wagtail docs](https://docs.wagtail.io/en/stable/getting_started/tutorial.html#categories) has a good example of it implementation.

```python
class MyPage(Page):
    categories = ParentalManyToManyField(Category, blank=True)
    ... your own extra fields can also be included.

    content_panels = Page.content_panels + [
        FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
    ]
```

*The above example uses the `CheckboxSelectMultiple` forms widget which simplifies selecting multiple categories.*
