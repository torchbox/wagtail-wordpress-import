# Contents

- [Yoast plugin compatibility](#yoast-plugin-compatibility)
  - [Search description default behaviour](#search-description-default-behaviour)
  - [Enable the yoast plugin](#enable-the-yoast-plugin)
  - [Change the imported fields](#change-the-imported-fields)

## Yoast plugin compatibility

The package has built in configuration to include Wordpress yoast search descriptions during the import.

*This feature is disabled by default.*

## Search description default behaviour

The default behaviour for importing the Wordpress search descriptions is to use the data in the Wordpress XML file `<item><description>...` field. The import process will place the Wordpress search description content into the Wagtail search_description field of the page model thats been used for the imported pages.

## Enable the yoast plugin

*Enabling the yoast plugin compatibility will override the default behaviour. The Wordpress XML file `<item><description>...` will be ignored*

The yoast plugin feature can be enabled by adding the following configuration to your own settings

```python
WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_ENABLED = True
```

## Change the imported fields

The package has a default mapping for Wordpress search descriptions. There is no need to add this configuration to your settings.

If you do need to change the field names because your Wordpress site is setup differently, include the configuration below in your settings and adjust the right side of each parameter.

The configuration below is the default included in the package.

```python
WAGTAIL_WORDPRESS_IMPORT_YOAST_PLUGIN_MAPPING = (
    {
        "xml_item_key": "wp:postmeta",
        "description_key": "wp:meta_key",
        "description_value": "wp:meta_value",
        "description_key_value": "_yoast_wpseo_metadesc",
    },
)
```
